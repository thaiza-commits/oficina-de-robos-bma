"""Robô Selic - Oficina de Robôs BMA FIDC.

Consulta a Selic (série 1178 do SGS/Banco Central) no período escolhido
(padrão: últimos 12 meses) e entrega um painel visual (HTML), Excel, gráfico
PNG, relatório PDF e log, com a identidade visual da BMA FIDC.
Se a internet falhar, usa a última consulta salva (cache) ou os dados de
exemplo - sempre avisando na tela, no painel, no Excel e no PDF.

Período (do mais forte para o mais fraco):
  --inicio / --fim / --meses  >  --perguntar  >  parametros.ini  >  12 meses
"""
from __future__ import annotations

if __name__ == "__main__":
    # Aparece antes de carregar as bibliotecas (a 1a execução pode levar alguns segundos).
    print("Iniciando o Robô Selic... aguarde alguns segundos.", flush=True)

import argparse
import configparser
import json
import logging
import os
import platform
import re
import subprocess
import sys
import textwrap
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # gera o PNG sem abrir janela (funciona também no .exe)

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import requests
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

try:  # usa os certificados do Windows (necessário em redes corporativas com proxy)
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass

VERSAO = "1.1.0"
SERIE_SELIC = 1178
INICIO_SERIE = date(1986, 6, 4)
MESES_PADRAO = 12
# A API do SGS aceita no máximo 10 anos por consulta; pedimos em blocos menores.
BLOCO_DIAS = 3650
API_URL = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{SERIE_SELIC}/dados"
FONTE_BCB = f"Banco Central do Brasil - SGS, série {SERIE_SELIC}"

# Identidade visual bmafidc.com.br
PRIMARIA = "#1B172D"
AZUL = "#2B63DF"
AZUL_ESCURO = "#253E8C"
LARANJA = "#F37522"
TEXTO = "#202020"
FUNDO = "#EDEDED"


def _pasta_documentos() -> Path:
    """Pasta Documentos do usuário (respeita redirecionamento para OneDrive)."""
    if platform.system() == "Windows":
        import ctypes

        buffer = ctypes.create_unicode_buffer(260)
        if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buffer) == 0:
            return Path(buffer.value)
    return Path.home() / "Documents"


if getattr(sys, "frozen", False):
    # Executável (instalador): arquivos de apoio vêm embutidos no .exe e os
    # resultados vão para Documentos, onde a pessoa encontra facilmente.
    RECURSOS_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    CODIGO_DIR = RECURSOS_DIR
    BASE_DIR = _pasta_documentos() / "Oficina de Robos BMA"
else:
    CODIGO_DIR = Path(__file__).resolve().parent
    RECURSOS_DIR = CODIGO_DIR.parent
    BASE_DIR = RECURSOS_DIR

DADOS_DIR = BASE_DIR / "dados"
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"

PAINEL_PATH = OUTPUT_DIR / "painel_selic.html"
EXCEL_PATH = OUTPUT_DIR / "selic.xlsx"
GRAFICO_PATH = OUTPUT_DIR / "selic.png"
PDF_PATH = OUTPUT_DIR / "resumo_selic.pdf"
PARAMETROS_PATH = BASE_DIR / "parametros.ini"
ARQUIVO_CACHE = DADOS_DIR / "ultima_consulta_selic.csv"
ARQUIVO_EXEMPLO = RECURSOS_DIR / "dados" / "exemplo_selic.csv"
LOGO_PATH = CODIGO_DIR / "logo_bma_fidc.svg"
TEMPLATE_PATH = CODIGO_DIR / "painel_template.html"

PARAMETROS_MODELO = """; Parâmetros do Robô Selic - edite no Bloco de Notas e rode o robô de novo.
[periodo]
; Quantos meses para trás a partir de hoje (usado se as datas abaixo estiverem vazias).
meses = 12
; Ou um período fixo, no formato DD/MM/AAAA (deixe em branco para usar "meses").
data_inicial =
data_final =

[saida]
; O que abrir ao final: painel, pdf, ambos ou nenhum.
abrir = painel
"""


def br(valor: float, casas: int = 2) -> str:
    """Formata número no padrão brasileiro: 1234.5 -> '1.234,50'."""
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def sinal(valor: float, casas: int = 2) -> str:
    return ("+" if valor > 0 else "") + br(valor, casas)


def preparar_pastas() -> None:
    for pasta in (DADOS_DIR, OUTPUT_DIR, LOG_DIR):
        pasta.mkdir(parents=True, exist_ok=True)
    if not PARAMETROS_PATH.exists():
        PARAMETROS_PATH.write_text(PARAMETROS_MODELO, encoding="utf-8")


def configurar_log() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        # Na janela do Windows o texto sai acentuado; redirecionado, sai em UTF-8.
        if sys.stdout.isatty():
            sys.stdout.reconfigure(errors="replace")
        else:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(LOG_DIR / "oficina.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


# ----------------------------------------------------------------- período
def ler_data(texto: str) -> date:
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y").date()
    except ValueError:
        raise ValueError(f'Data inválida "{texto.strip()}": use DD/MM/AAAA, por exemplo 01/01/2026.') from None


def menos_meses(dia: date, meses: int) -> date:
    ano, mes = divmod(dia.year * 12 + dia.month - 1 - meses, 12)
    mes += 1
    ultimo_dia = (date(ano + mes // 12, mes % 12 + 1, 1) - timedelta(days=1)).day
    return date(ano, mes, min(dia.day, ultimo_dia))


def perguntar_periodo(meses: int) -> tuple[date | None, date | None]:
    print("\nEscolha o período (formato DD/MM/AAAA). ENTER mantém o padrão.")
    while True:
        try:
            ini = input(f"  Data inicial [ENTER = {meses} meses atrás]: ").strip()
            fim = input("  Data final   [ENTER = hoje]: ").strip()
            return (ler_data(ini) if ini else None), (ler_data(fim) if fim else None)
        except ValueError:
            print("  Data inválida. Use DD/MM/AAAA, por exemplo 01/01/2026.")
        except EOFError:
            return None, None


def ler_parametros() -> configparser.ConfigParser:
    """Lê parametros.ini aceitando UTF-8 (com ou sem BOM) e ANSI; se estiver ilegível, usa o padrão."""
    cfg = configparser.ConfigParser()
    if not PARAMETROS_PATH.exists():
        return cfg
    bruto = PARAMETROS_PATH.read_bytes()
    for codificacao in ("utf-8-sig", "cp1252"):
        try:
            cfg.read_string(bruto.decode(codificacao))
            return cfg
        except UnicodeDecodeError:
            continue
        except configparser.Error as erro:
            logging.warning("parametros.ini ilegível (%s); usando o padrão de %s meses.",
                            str(erro).splitlines()[0], MESES_PADRAO)
            return configparser.ConfigParser()
    logging.warning("parametros.ini com codificação desconhecida; usando o padrão de %s meses.", MESES_PADRAO)
    return configparser.ConfigParser()


def definir_periodo(args: argparse.Namespace) -> tuple[date, date, str]:
    """Retorna (início, fim, de onde veio o período)."""
    ini_cfg = ler_parametros()
    cfg = ini_cfg["periodo"] if ini_cfg.has_section("periodo") else {}
    meses = MESES_PADRAO
    origem = f"padrão ({MESES_PADRAO} meses)"
    inicio = fim = None
    try:
        if cfg.get("meses", "").strip():
            meses, origem = int(cfg["meses"]), f"parametros.ini ({cfg['meses'].strip()} meses)"
        if cfg.get("data_inicial", "").strip():
            inicio, origem = ler_data(cfg["data_inicial"]), "parametros.ini (datas)"
        if cfg.get("data_final", "").strip():
            fim = ler_data(cfg["data_final"])
    except ValueError as erro:
        logging.warning("parametros.ini com valor inválido (%s); usando o padrão de %s meses.", erro, MESES_PADRAO)
        meses, inicio, fim, origem = MESES_PADRAO, None, None, f"padrão ({MESES_PADRAO} meses)"
    if args.perguntar:
        p_ini, p_fim = perguntar_periodo(args.meses or meses)
        if p_ini or p_fim:
            inicio, fim, origem = p_ini or inicio, p_fim or fim, "informado na tela"
    if args.meses:
        meses, inicio, origem = args.meses, None, f"linha de comando ({args.meses} meses)"
    if args.inicio:
        inicio, origem = ler_data(args.inicio), "linha de comando (datas)"
    if args.fim:
        fim = ler_data(args.fim)

    hoje = date.today()
    fim = min(fim or hoje, hoje)
    inicio = max(inicio or menos_meses(fim, meses), INICIO_SERIE)
    if inicio >= fim:
        raise ValueError(f"Período inválido: {inicio:%d/%m/%Y} a {fim:%d/%m/%Y} (a data inicial deve vir antes da final).")
    return inicio, fim, origem


# ----------------------------------------------------------------- dados
def tratar(tabela: pd.DataFrame) -> pd.DataFrame:
    tabela = tabela.copy()
    tabela["data"] = pd.to_datetime(tabela["data"], format="%d/%m/%Y")
    tabela["valor"] = pd.to_numeric(tabela["valor"].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    return tabela.dropna().drop_duplicates("data").sort_values("data").reset_index(drop=True)


def pedir_bloco(inicio: date, fim: date, tentativas: int = 3):
    """GET na API com novas tentativas para quedas de conexão e erros 5xx (oscilações do BCB)."""
    parametros = {"formato": "json", "dataInicial": f"{inicio:%d/%m/%Y}", "dataFinal": f"{fim:%d/%m/%Y}"}
    for tentativa in range(1, tentativas + 1):
        try:
            resposta = requests.get(API_URL, params=parametros, timeout=30)
            resposta.raise_for_status()
            return resposta.json()
        except requests.RequestException as erro:
            status = getattr(getattr(erro, "response", None), "status_code", None)
            if tentativa == tentativas or (status is not None and status < 500):
                raise  # erro 4xx é pedido errado: repetir não resolve
            logging.warning("Tentativa %s de %s falhou (%s). Nova tentativa em %s s...",
                            tentativa, tentativas, type(erro).__name__, 2 * tentativa)
            time.sleep(2 * tentativa)


def consultar_bacen(inicio: date, fim: date) -> pd.DataFrame:
    logging.info("Consultando a API do Banco Central (série %s) de %s a %s...",
                 SERIE_SELIC, f"{inicio:%d/%m/%Y}", f"{fim:%d/%m/%Y}")
    partes = []
    bloco_ini = inicio
    while bloco_ini <= fim:
        bloco_fim = min(bloco_ini + timedelta(days=BLOCO_DIAS), fim)
        dados = pedir_bloco(bloco_ini, bloco_fim)
        if not isinstance(dados, list):
            raise ValueError("A API respondeu em formato inesperado.")
        partes.extend(dados)
        bloco_ini = bloco_fim + timedelta(days=1)
    if not partes:
        raise ValueError("A API não retornou dados para o período.")
    tabela = tratar(pd.DataFrame(partes))
    if tabela.empty:
        raise ValueError("Os dados retornados não puderam ser processados.")
    logging.info("Dados obtidos com sucesso: %s registros.", len(tabela))
    return tabela


def ler_csv(caminho: Path) -> pd.DataFrame:
    return tratar(pd.read_csv(caminho, sep=";", dtype=str, encoding="utf-8-sig"))


def salvar_cache(tabela: pd.DataFrame) -> None:
    """Acumula tudo o que já foi consultado, para a contingência cobrir qualquer período já visto."""
    if ARQUIVO_CACHE.exists():
        try:
            tabela = pd.concat([ler_csv(ARQUIVO_CACHE), tabela])
            tabela = tabela.drop_duplicates("data", keep="last").sort_values("data").reset_index(drop=True)
        except (ValueError, KeyError, pd.errors.ParserError) as erro:
            logging.warning("Cache anterior ilegível (%s); será substituído.", erro)
    tabela.to_csv(ARQUIVO_CACHE, sep=";", decimal=",", index=False, date_format="%d/%m/%Y", encoding="utf-8-sig")


def carregar_contingencia(inicio: date, fim: date) -> tuple[pd.DataFrame, str]:
    if ARQUIVO_CACHE.exists():
        salvo_em = datetime.fromtimestamp(ARQUIVO_CACHE.stat().st_mtime)
        logging.warning("ATENÇÃO: usando a ÚLTIMA CONSULTA SALVA (de %s), não a consulta ao vivo.",
                        f"{salvo_em:%d/%m/%Y %H:%M}")
        tabela, fonte = ler_csv(ARQUIVO_CACHE), f"{FONTE_BCB} - última consulta salva em {salvo_em:%d/%m/%Y %H:%M}"
    else:
        logging.warning("ATENÇÃO: usando DADOS DE EXEMPLO (modo offline), não a consulta ao vivo.")
        tabela, fonte = ler_csv(ARQUIVO_EXEMPLO), "DADOS DE EXEMPLO (modo offline) - não usar para decisão"
    recorte = tabela[(tabela["data"].dt.date >= inicio) & (tabela["data"].dt.date <= fim)].reset_index(drop=True)
    if len(recorte) < 2:
        logging.warning("ATENÇÃO: o período pedido não está nos dados offline; mostrando %s a %s.",
                        f"{tabela['data'].iloc[0]:%d/%m/%Y}", f"{tabela['data'].iloc[-1]:%d/%m/%Y}")
        return tabela, fonte
    if recorte["data"].iloc[0].date() > inicio + timedelta(days=7) or recorte["data"].iloc[-1].date() < fim - timedelta(days=7):
        logging.warning("ATENÇÃO: os dados offline cobrem só parte do período pedido (%s a %s).",
                        f"{recorte['data'].iloc[0]:%d/%m/%Y}", f"{recorte['data'].iloc[-1]:%d/%m/%Y}")
    return recorte, fonte


def obter_dados(inicio: date, fim: date, modo_offline: bool) -> tuple[pd.DataFrame, str, bool]:
    """Retorna (tabela, fonte, ao_vivo)."""
    if modo_offline:
        logging.info("Modo offline escolhido: a internet não será usada.")
        tabela, fonte = carregar_contingencia(inicio, fim)
        return tabela, fonte, False
    try:
        tabela = consultar_bacen(inicio, fim)
    except (requests.RequestException, ValueError, KeyError) as erro:
        logging.error("Falha na consulta online: %s", erro)
        tabela, fonte = carregar_contingencia(inicio, fim)
        return tabela, fonte, False
    salvar_cache(tabela)
    return tabela, f"{FONTE_BCB} - consulta em {datetime.now():%d/%m/%Y %H:%M}", True


def calcular_resumo(tabela: pd.DataFrame) -> dict:
    primeiro = float(tabela.iloc[0]["valor"])
    ultimo = float(tabela.iloc[-1]["valor"])
    variacao_pp = ultimo - primeiro
    anterior = tabela["valor"].shift()
    mudou = tabela[(tabela["valor"] != anterior) & anterior.notna()]
    mudancas = [
        {"data": d.strftime("%d/%m/%Y"), "de": float(a), "para": float(v)}
        for d, a, v in zip(mudou["data"], anterior[mudou.index], mudou["valor"])
    ]
    return {
        "data_inicial": tabela.iloc[0]["data"].strftime("%d/%m/%Y"),
        "data_final": tabela.iloc[-1]["data"].strftime("%d/%m/%Y"),
        "registros": len(tabela),
        "primeiro": primeiro,
        "ultimo": ultimo,
        "maior": float(tabela["valor"].max()),
        "menor": float(tabela["valor"].min()),
        "media": float(tabela["valor"].mean()),
        "variacao_pp": variacao_pp,
        "variacao_pct": (variacao_pp / primeiro * 100) if primeiro else 0.0,
        "mudancas": mudancas,
    }


# ----------------------------------------------------------------- saídas
def gerar_painel(tabela: pd.DataFrame, resumo: dict, fonte: str, ao_vivo: bool) -> None:
    logging.info("Gerando painel visual (HTML)...")
    dados = {
        "serie": [[d.strftime("%Y-%m-%d"), round(float(v), 4)] for d, v in zip(tabela["data"], tabela["valor"])],
        "fonte": fonte,
        "ao_vivo": ao_vivo,
        "gerado_em": f"{datetime.now():%d/%m/%Y %H:%M}",
        "versao": VERSAO,
    }
    logo = LOGO_PATH.read_text(encoding="utf-8")
    logo = re.sub(r'width="100%" height="100%"', 'role="img" aria-label="BMA FIDC"', logo, count=1)
    html = TEMPLATE_PATH.read_text(encoding="utf-8")
    html = html.replace("__LOGO__", logo).replace("__DADOS__", json.dumps(dados, ensure_ascii=False))
    PAINEL_PATH.write_text(html, encoding="utf-8")


def gerar_excel(tabela: pd.DataFrame, resumo: dict, fonte: str) -> None:
    logging.info("Gerando planilha Excel...")
    dados_excel = tabela.rename(columns={"data": "Data", "valor": "Selic (% a.a.)"})
    with pd.ExcelWriter(EXCEL_PATH, engine="xlsxwriter", datetime_format="dd/mm/yyyy") as writer:
        dados_excel.to_excel(writer, sheet_name="Dados", index=False)

        workbook = writer.book
        ws_dados = writer.sheets["Dados"]
        ws_resumo = workbook.add_worksheet("Resumo")
        ws_mud = workbook.add_worksheet("Mudanças")
        header = workbook.add_format({"bold": True, "font_color": "white", "bg_color": PRIMARIA, "align": "center"})
        rotulo = workbook.add_format({"bold": True})
        taxa = workbook.add_format({"num_format": "0.00"})
        pp = workbook.add_format({"num_format": "+0.00;-0.00;0.00"})
        pct = workbook.add_format({"num_format": "+0.00%;-0.00%;0.00%"})
        data_fmt = workbook.add_format({"num_format": "dd/mm/yyyy"})
        alerta = workbook.add_format({"bold": True, "font_color": LARANJA})

        ws_dados.set_row(0, 24, header)
        ws_dados.set_column("A:A", 15)
        ws_dados.set_column("B:B", 18, taxa)
        ws_dados.freeze_panes(1, 0)
        ws_dados.autofilter(0, 0, len(dados_excel), 1)

        ws_resumo.write_row(0, 0, ["Indicador", "Valor"], header)
        ws_resumo.set_row(0, 24)
        linhas = [
            ("Primeiro valor (% a.a.)", resumo["primeiro"], taxa),
            ("Último valor (% a.a.)", resumo["ultimo"], taxa),
            ("Maior valor (% a.a.)", resumo["maior"], taxa),
            ("Menor valor (% a.a.)", resumo["menor"], taxa),
            ("Média (% a.a.)", resumo["media"], taxa),
            ("Variação (p.p.)", resumo["variacao_pp"], pp),
            ("Variação (%)", resumo["variacao_pct"] / 100, pct),
            ("Mudanças da taxa", len(resumo["mudancas"]), None),
        ]
        for i, (nome, valor, formato) in enumerate(linhas, start=1):
            ws_resumo.write(i, 0, nome, rotulo)
            ws_resumo.write_number(i, 1, valor, formato)
        ws_resumo.write(10, 0, "Período", rotulo)
        ws_resumo.write(10, 1, f'{resumo["data_inicial"]} a {resumo["data_final"]} ({resumo["registros"]} registros)')
        ws_resumo.write(11, 0, "Fonte", rotulo)
        ws_resumo.write(11, 1, fonte, alerta if "EXEMPLO" in fonte or "salva" in fonte else None)
        ws_resumo.write(12, 0, "Gerado em", rotulo)
        ws_resumo.write(12, 1, f"{datetime.now():%d/%m/%Y %H:%M}")
        ws_resumo.set_column("A:A", 26)
        ws_resumo.set_column("B:B", 18)

        ws_mud.write_row(0, 0, ["Data", "De (% a.a.)", "Para (% a.a.)", "Variação (p.p.)"], header)
        ws_mud.set_row(0, 24)
        for i, m in enumerate(resumo["mudancas"], start=1):
            ws_mud.write_datetime(i, 0, datetime.strptime(m["data"], "%d/%m/%Y"), data_fmt)
            ws_mud.write_number(i, 1, m["de"], taxa)
            ws_mud.write_number(i, 2, m["para"], taxa)
            ws_mud.write_number(i, 3, m["para"] - m["de"], pp)
        if not resumo["mudancas"]:
            ws_mud.write(1, 0, "A taxa não mudou no período.")
        ws_mud.set_column("A:D", 16)

        chart = workbook.add_chart({"type": "line"})
        chart.add_series({
            "name": "Selic (% a.a.)",
            "categories": ["Dados", 1, 0, len(dados_excel), 0],
            "values": ["Dados", 1, 1, len(dados_excel), 1],
            "line": {"color": AZUL, "width": 2.25},
        })
        chart.set_title({"name": "Evolução da Selic"})
        chart.set_x_axis({"name": "Data", "date_axis": True, "num_format": "mm/yy"})
        chart.set_y_axis({"name": "Selic (% a.a.)", "num_format": "0.00"})
        chart.set_legend({"none": True})
        chart.set_size({"width": 720, "height": 380})
        ws_resumo.insert_chart("D2", chart)


def gerar_grafico(tabela: pd.DataFrame, resumo: dict) -> None:
    logging.info("Gerando gráfico PNG...")
    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.step(tabela["data"], tabela["valor"], where="post", color=AZUL, linewidth=2.4)
    ax.fill_between(tabela["data"], tabela["valor"], tabela["valor"].min() - 10, step="post", color=AZUL, alpha=0.10)
    limite_rotulo = tabela["data"].iloc[0] + (tabela["data"].iloc[-1] - tabela["data"].iloc[0]) * 0.93
    for m in resumo["mudancas"]:
        dia = datetime.strptime(m["data"], "%d/%m/%Y")
        ax.plot(dia, m["para"], "o", color=LARANJA, markersize=8, markeredgecolor="white", markeredgewidth=1.5, zorder=3)
        if len(resumo["mudancas"]) <= 12:
            perto = dia > limite_rotulo  # perto da borda direita: rótulo à esquerda do ponto
            ax.annotate(br(m["para"]), (dia, m["para"]), textcoords="offset points", xytext=(-7 if perto else 7, 6),
                        ha="right" if perto else "left", fontsize=9, color=PRIMARIA, fontweight="bold")
    ax.set_title(f'Selic (% a.a.) - {resumo["data_inicial"]} a {resumo["data_final"]}', color=PRIMARIA, fontsize=13)
    ax.set_ylabel("Selic (% a.a.)", color=TEXTO)
    dias = (tabela["data"].iloc[-1] - tabela["data"].iloc[0]).days
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m" if dias <= 60 else "%m/%y" if dias <= 1100 else "%Y"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: br(v)))
    minimo, maximo = tabela["valor"].min(), tabela["valor"].max()
    folga = max((maximo - minimo) * 0.15, 0.1)
    ax.set_ylim(minimo - folga, maximo + folga)
    ax.set_xlim(tabela["data"].iloc[0], tabela["data"].iloc[-1])
    ax.grid(True, axis="y", color="#E6E8EE")
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    fig.autofmt_xdate(rotation=0, ha="center")
    fig.tight_layout()
    fig.savefig(GRAFICO_PATH, dpi=180)
    plt.close(fig)


def desenhar_logo(c: canvas.Canvas, x: float, y: float, largura: float) -> None:
    """Desenha logo_bma_fidc.svg (caminhos M/L/H/V/C/Z e retângulos) no PDF."""
    svg = LOGO_PATH.read_text(encoding="utf-8")
    vb = [float(n) for n in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
    escala = largura / vb[2]
    px = lambda a: x + (a - vb[0]) * escala
    py = lambda b: y + (vb[1] + vb[3] - b) * escala
    for tag in re.finditer(r"<(path|rect)\b([^>]*)>", svg):
        atributos = tag.group(2)
        cor = re.search(r"fill:#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})", atributos)
        hexa = cor.group(1) if cor else "fff"
        if len(hexa) == 3:  # "#fff" -> "#ffffff" (o ReportLab leria "#fff" como azul)
            hexa = "".join(ch * 2 for ch in hexa)
        c.setFillColor(colors.HexColor("#" + hexa))
        if tag.group(1) == "rect":
            v = {k: float(n) for k, n in re.findall(r'\b(x|y|width|height)="([-\d.]+)"', atributos)}
            c.rect(px(v["x"]), py(v["y"] + v["height"]), v["width"] * escala, v["height"] * escala, fill=1, stroke=0)
            continue
        tokens = re.findall(r"[MmLlHhVvCcZz]|-?\d*\.?\d+(?:e-?\d+)?", re.search(r'\bd="([^"]+)"', atributos).group(1))
        caminho, i, cx, cy, cmd = c.beginPath(), 0, 0.0, 0.0, "M"
        while i < len(tokens):
            if re.match(r"[A-Za-z]", tokens[i]):
                cmd = tokens[i]
                i += 1
                if cmd in "Zz":
                    caminho.close()
                    continue
            n = lambda k: float(tokens[i + k])
            rel = cmd.islower()
            if cmd in "Mm":
                cx, cy = (cx + n(0), cy + n(1)) if rel else (n(0), n(1))
                caminho.moveTo(px(cx), py(cy))
                cmd, i = ("l" if rel else "L"), i + 2
            elif cmd in "Ll":
                cx, cy = (cx + n(0), cy + n(1)) if rel else (n(0), n(1))
                caminho.lineTo(px(cx), py(cy))
                i += 2
            elif cmd in "Hh":
                cx = cx + n(0) if rel else n(0)
                caminho.lineTo(px(cx), py(cy))
                i += 1
            elif cmd in "Vv":
                cy = cy + n(0) if rel else n(0)
                caminho.lineTo(px(cx), py(cy))
                i += 1
            elif cmd in "Cc":
                pts = [n(k) for k in range(6)]
                if rel:
                    pts = [pts[k] + (cx if k % 2 == 0 else cy) for k in range(6)]
                caminho.curveTo(px(pts[0]), py(pts[1]), px(pts[2]), py(pts[3]), px(pts[4]), py(pts[5]))
                cx, cy = pts[4], pts[5]
                i += 6
            else:
                i += 1
        c.drawPath(caminho, fill=1, stroke=0, fillMode=0)  # 0 = par-ímpar (furos das letras)


def gerar_pdf(resumo: dict, fonte: str, ao_vivo: bool) -> None:
    logging.info("Gerando relatório PDF...")
    c = canvas.Canvas(str(PDF_PATH), pagesize=A4)
    c.setTitle("Relatório Executivo - Selic")
    c.setAuthor("Oficina de Robôs - BMA FIDC")
    w, h = A4
    primaria = colors.HexColor(PRIMARIA)
    laranja = colors.HexColor(LARANJA)
    claro = colors.HexColor("#F1F2F5")

    c.setFillColor(primaria)
    c.rect(0, h - 110, w, 110, fill=1, stroke=0)
    desenhar_logo(c, 42, h - 88, 118)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawRightString(w - 42, h - 56, "OFICINA DE ROBÔS")
    c.setFillColor(laranja)
    c.setFont("Helvetica", 11)
    c.drawRightString(w - 42, h - 76, "Relatório Executivo - Selic")

    if not ao_vivo:
        c.setFillColor(laranja)
        c.rect(42, h - 138, w - 84, 22, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(52, h - 131, "ATENÇÃO: dados de contingência, não da consulta ao vivo. Veja a fonte no rodapé.")

    c.setFillColor(primaria)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(42, h - 170, f'Selic - {resumo["data_inicial"]} a {resumo["data_final"]}')

    indicadores = [
        (f'Selic atual ({resumo["data_final"]})', f'{br(resumo["ultimo"])}%', True),
        ("Variação no período", f'{sinal(resumo["variacao_pp"])} p.p.', False),
        ("Mudanças da taxa", str(len(resumo["mudancas"])), False),
        ("Maior valor", f'{br(resumo["maior"])}%', False),
        ("Menor valor", f'{br(resumo["menor"])}%', False),
        ("Média", f'{br(resumo["media"])}%', False),
    ]
    x0, y0 = 42, h - 240
    for i, (rotulo, valor, destaque) in enumerate(indicadores):
        col, row = i % 3, i // 3
        x, y = x0 + col * 175, y0 - row * 75
        c.setFillColor(primaria if destaque else claro)
        c.rect(x, y, 155, 55, fill=1, stroke=0)
        c.setFillColor(colors.white if destaque else primaria)
        c.setFont("Helvetica", 9)
        c.drawString(x + 12, y + 35, rotulo)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(x + 12, y + 14, valor)

    if resumo["variacao_pp"] > 0:
        movimento = f'alta de {br(resumo["variacao_pp"])} ponto percentual'
    elif resumo["variacao_pp"] < 0:
        movimento = f'queda de {br(abs(resumo["variacao_pp"]))} ponto percentual'
    else:
        movimento = "estabilidade"
    n_mud = len(resumo["mudancas"])
    texto = (
        f'A Selic anualizada base 252 passou de {br(resumo["primeiro"])}% para '
        f'{br(resumo["ultimo"])}% entre {resumo["data_inicial"]} e {resumo["data_final"]}, '
        f'com {movimento} ({sinal(resumo["variacao_pct"])}%). '
    )
    if n_mud:
        ultimas = "; ".join(f'{m["data"]}: {br(m["de"])}% > {br(m["para"])}%' for m in resumo["mudancas"][-4:])
        texto += f'A taxa mudou {n_mud} vez(es) no período. Últimas mudanças: {ultimas}.'
    else:
        texto += "A taxa não mudou no período."
    c.setFillColor(colors.HexColor(TEXTO))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(42, h - 350, "Resumo executivo")
    bloco = c.beginText(42, h - 370)
    bloco.setFont("Helvetica", 10)
    bloco.setLeading(15)
    for linha in textwrap.wrap(texto, 95):
        bloco.textLine(linha)
    c.drawText(bloco)
    c.drawImage(ImageReader(str(GRAFICO_PATH)), 48, 72, width=500, height=300, preserveAspectRatio=True, anchor="n")
    c.setFillColor(laranja if not ao_vivo else colors.grey)
    c.setFont("Helvetica-Bold" if not ao_vivo else "Helvetica", 8)
    c.drawString(42, 54, f"Fonte: {fonte}.")
    c.setFillColor(colors.grey)
    c.setFont("Helvetica", 8)
    c.drawString(42, 42, f"Gerado em {datetime.now():%d/%m/%Y %H:%M} pelo Robô Selic v{VERSAO}.")
    c.save()


def abrir_arquivo(caminho: Path) -> None:
    try:
        sistema = platform.system()
        if sistema == "Windows":
            os.startfile(caminho)  # type: ignore[attr-defined]
        elif sistema == "Darwin":
            subprocess.run(["open", str(caminho)], check=False)
        else:
            subprocess.run(["xdg-open", str(caminho)], check=False)
    except OSError as erro:
        logging.warning("Não foi possível abrir %s automaticamente: %s", caminho.name, erro)


def o_que_abrir(args: argparse.Namespace) -> str:
    if args.no_open:
        return "nenhum"
    if args.abrir:
        return args.abrir
    escolha = ler_parametros().get("saida", "abrir", fallback="painel").strip().lower()
    return escolha if escolha in ("painel", "pdf", "ambos", "nenhum") else "painel"


def executar(args: argparse.Namespace) -> int:
    logging.info("=" * 52)
    logging.info("OFICINA DE ROBÔS - BMA FIDC  |  Robô Selic v%s", VERSAO)
    logging.info("=" * 52)
    inicio, fim, origem = definir_periodo(args)
    logging.info("Período pedido: %s a %s (%s)", f"{inicio:%d/%m/%Y}", f"{fim:%d/%m/%Y}", origem)
    tabela, fonte, ao_vivo = obter_dados(inicio, fim, args.offline)
    resumo = calcular_resumo(tabela)
    logging.info("Período: %s a %s | Registros: %s", resumo["data_inicial"], resumo["data_final"], resumo["registros"])
    logging.info("Último valor: %s%% | Variação: %s p.p. | Mudanças da taxa: %s",
                 br(resumo["ultimo"]), sinal(resumo["variacao_pp"]), len(resumo["mudancas"]))
    gerar_painel(tabela, resumo, fonte, ao_vivo)
    gerar_excel(tabela, resumo, fonte)
    gerar_grafico(tabela, resumo)
    gerar_pdf(resumo, fonte, ao_vivo)
    logging.info("Painel: %s", PAINEL_PATH)
    logging.info("Excel: %s", EXCEL_PATH)
    logging.info("Gráfico: %s", GRAFICO_PATH)
    logging.info("PDF: %s", PDF_PATH)
    logging.info("Fonte dos dados: %s", fonte)
    if ao_vivo:
        logging.info("Processo concluído com sucesso (dados ao vivo do Banco Central).")
    else:
        logging.warning("Processo concluído com DADOS DE CONTINGÊNCIA (não é a consulta ao vivo).")
    abrir = o_que_abrir(args)
    if abrir in ("painel", "ambos"):
        abrir_arquivo(PAINEL_PATH)
    if abrir in ("pdf", "ambos"):
        abrir_arquivo(PDF_PATH)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Robô Selic - Oficina de Robôs BMA")
    parser.add_argument("--offline", action="store_true", help="Não usa a internet (última consulta salva ou exemplo).")
    parser.add_argument("--meses", type=int, help="Quantos meses para trás a partir de hoje (padrão: 12).")
    parser.add_argument("--inicio", help="Data inicial DD/MM/AAAA.")
    parser.add_argument("--fim", help="Data final DD/MM/AAAA (padrão: hoje).")
    parser.add_argument("--perguntar", action="store_true", help="Pergunta o período na tela.")
    parser.add_argument("--abrir", choices=["painel", "pdf", "ambos", "nenhum"], help="O que abrir ao final (padrão: painel).")
    parser.add_argument("--no-open", action="store_true", help="Não abre nada ao final (o mesmo que --abrir nenhum).")
    parser.add_argument("--no-pause", action="store_true", help="Não espera ENTER ao final (executável).")
    args = parser.parse_args()
    preparar_pastas()
    configurar_log()
    try:
        codigo = executar(args)
    except ValueError as erro:  # período ou parâmetro inválido: mensagem simples, sem rastreamento
        logging.error("Não foi possível rodar: %s", erro)
        codigo = 1
    except Exception:  # noqa: BLE001 - qualquer falha precisa aparecer na tela e no log
        logging.exception("O robô falhou. Detalhes acima e em %s", LOG_DIR / "oficina.log")
        codigo = 1
    if getattr(sys, "frozen", False) and not args.no_pause and sys.stdin and sys.stdin.isatty():
        print(f"\nResultados em: {OUTPUT_DIR}")
        input("Pressione ENTER para fechar...")
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
