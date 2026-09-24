"""Robô Selic - Oficina de Robôs BMA FIDC.

Consulta a Selic (série 1178 do SGS/Banco Central), gera Excel, gráfico PNG,
relatório PDF e log. Se a internet falhar, usa a última consulta salva
(cache) ou, na falta dela, os dados de exemplo - sempre avisando na tela,
no Excel e no PDF que os dados não são da consulta ao vivo.
"""
from __future__ import annotations

if __name__ == "__main__":
    # Aparece antes de carregar as bibliotecas (a 1a execução pode levar alguns segundos).
    print("Iniciando o Robô Selic... aguarde alguns segundos.", flush=True)

import argparse
import logging
import os
import platform
import subprocess
import sys
import textwrap
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

VERSAO = "1.0.0"
SERIE_SELIC = 1178
OBSERVACOES = 30
# A API do SGS limita "ultimos/N" a 20 valores; por isso consultamos por período
# (75 dias corridos cobrem com folga 30 dias úteis, feriados incluídos).
JANELA_DIAS = 75
API_URL = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{SERIE_SELIC}/dados"
FONTE_BCB = f"Banco Central do Brasil - SGS, série {SERIE_SELIC}"

NAVY = "#0B1D3A"
ORANGE = "#F28C2B"


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
    BASE_DIR = _pasta_documentos() / "Oficina de Robos BMA"
else:
    RECURSOS_DIR = Path(__file__).resolve().parent.parent
    BASE_DIR = RECURSOS_DIR

DADOS_DIR = BASE_DIR / "dados"
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"

EXCEL_PATH = OUTPUT_DIR / "selic.xlsx"
GRAFICO_PATH = OUTPUT_DIR / "selic.png"
PDF_PATH = OUTPUT_DIR / "resumo_selic.pdf"
ARQUIVO_CACHE = DADOS_DIR / "ultima_consulta_selic.csv"
ARQUIVO_EXEMPLO = RECURSOS_DIR / "dados" / "exemplo_selic.csv"


def br(valor: float, casas: int = 2) -> str:
    """Formata número no padrão brasileiro: 1234.5 -> '1.234,50'."""
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def preparar_pastas() -> None:
    for pasta in (DADOS_DIR, OUTPUT_DIR, LOG_DIR):
        pasta.mkdir(parents=True, exist_ok=True)


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


def consultar_bacen() -> pd.DataFrame:
    hoje = date.today()
    parametros = {
        "formato": "json",
        "dataInicial": (hoje - timedelta(days=JANELA_DIAS)).strftime("%d/%m/%Y"),
        "dataFinal": hoje.strftime("%d/%m/%Y"),
    }
    logging.info("Consultando a API do Banco Central (série %s)...", SERIE_SELIC)
    resposta = requests.get(API_URL, params=parametros, timeout=30)
    resposta.raise_for_status()
    dados = resposta.json()
    if not isinstance(dados, list) or not dados:
        raise ValueError("A API não retornou dados.")

    tabela = pd.DataFrame(dados)
    tabela["data"] = pd.to_datetime(tabela["data"], format="%d/%m/%Y")
    tabela["valor"] = pd.to_numeric(
        tabela["valor"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )
    tabela = (
        tabela.dropna()
        .drop_duplicates("data")
        .sort_values("data")
        .tail(OBSERVACOES)
        .reset_index(drop=True)
    )
    if tabela.empty:
        raise ValueError("Os dados retornados não puderam ser processados.")
    logging.info("Dados obtidos com sucesso: %s registros.", len(tabela))
    return tabela


def ler_csv(caminho: Path) -> pd.DataFrame:
    tabela = pd.read_csv(caminho, sep=";", decimal=",", encoding="utf-8-sig")
    tabela["data"] = pd.to_datetime(tabela["data"], format="%d/%m/%Y")
    return tabela.sort_values("data").reset_index(drop=True)


def salvar_cache(tabela: pd.DataFrame) -> None:
    tabela.to_csv(
        ARQUIVO_CACHE, sep=";", decimal=",", index=False,
        date_format="%d/%m/%Y", encoding="utf-8-sig",
    )


def carregar_contingencia() -> tuple[pd.DataFrame, str]:
    if ARQUIVO_CACHE.exists():
        salvo_em = datetime.fromtimestamp(ARQUIVO_CACHE.stat().st_mtime)
        logging.warning(
            "ATENÇÃO: usando a ÚLTIMA CONSULTA SALVA (de %s), não a consulta ao vivo.",
            salvo_em.strftime("%d/%m/%Y %H:%M"),
        )
        fonte = f"{FONTE_BCB} - última consulta salva em {salvo_em:%d/%m/%Y %H:%M}"
        return ler_csv(ARQUIVO_CACHE), fonte
    logging.warning("ATENÇÃO: usando DADOS DE EXEMPLO (modo offline), não a consulta ao vivo.")
    return ler_csv(ARQUIVO_EXEMPLO), "DADOS DE EXEMPLO (modo offline) - não usar para decisão"


def obter_dados(modo_offline: bool) -> tuple[pd.DataFrame, str, bool]:
    """Retorna (tabela, fonte, ao_vivo)."""
    if modo_offline:
        logging.info("Modo offline escolhido: a internet não será usada.")
        tabela, fonte = carregar_contingencia()
        return tabela, fonte, False
    try:
        tabela = consultar_bacen()
    except (requests.RequestException, ValueError, KeyError) as erro:
        logging.error("Falha na consulta online: %s", erro)
        tabela, fonte = carregar_contingencia()
        return tabela, fonte, False
    salvar_cache(tabela)
    return tabela, f"{FONTE_BCB} - consulta em {datetime.now():%d/%m/%Y %H:%M}", True


def calcular_resumo(tabela: pd.DataFrame) -> dict:
    primeiro = float(tabela.iloc[0]["valor"])
    ultimo = float(tabela.iloc[-1]["valor"])
    variacao_pp = ultimo - primeiro
    variacao_pct = (variacao_pp / primeiro * 100) if primeiro else 0.0
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
        "variacao_pct": variacao_pct,
    }


def gerar_excel(tabela: pd.DataFrame, resumo: dict, fonte: str) -> None:
    logging.info("Gerando planilha Excel...")
    dados_excel = tabela.rename(columns={"data": "Data", "valor": "Selic (% a.a.)"})
    with pd.ExcelWriter(EXCEL_PATH, engine="xlsxwriter", datetime_format="dd/mm/yyyy") as writer:
        dados_excel.to_excel(writer, sheet_name="Dados", index=False)

        workbook = writer.book
        ws_dados = writer.sheets["Dados"]
        ws_resumo = workbook.add_worksheet("Resumo")
        header = workbook.add_format({"bold": True, "font_color": "white", "bg_color": NAVY, "align": "center"})
        rotulo = workbook.add_format({"bold": True})
        taxa = workbook.add_format({"num_format": "0.00"})
        pp = workbook.add_format({"num_format": "+0.00;-0.00;0.00"})
        pct = workbook.add_format({"num_format": "+0.00%;-0.00%;0.00%"})
        alerta = workbook.add_format({"bold": True, "font_color": ORANGE})

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
        ]
        for i, (nome, valor, formato) in enumerate(linhas, start=1):
            ws_resumo.write(i, 0, nome, rotulo)
            ws_resumo.write_number(i, 1, valor, formato)
        ws_resumo.write(9, 0, "Período", rotulo)
        ws_resumo.write(9, 1, f'{resumo["data_inicial"]} a {resumo["data_final"]} ({resumo["registros"]} registros)')
        ws_resumo.write(10, 0, "Fonte", rotulo)
        ws_resumo.write(10, 1, fonte, alerta if "EXEMPLO" in fonte or "salva" in fonte else None)
        ws_resumo.write(11, 0, "Gerado em", rotulo)
        ws_resumo.write(11, 1, f"{datetime.now():%d/%m/%Y %H:%M}")
        ws_resumo.set_column("A:A", 26)
        ws_resumo.set_column("B:B", 18)

        chart = workbook.add_chart({"type": "line"})
        chart.add_series({
            "name": "Selic (% a.a.)",
            "categories": ["Dados", 1, 0, len(dados_excel), 0],
            "values": ["Dados", 1, 1, len(dados_excel), 1],
            "line": {"color": NAVY, "width": 2.25},
            "marker": {"type": "circle", "size": 4, "border": {"color": ORANGE}, "fill": {"color": ORANGE}},
        })
        chart.set_title({"name": "Evolução da Selic"})
        chart.set_x_axis({"name": "Data", "date_axis": True, "num_format": "dd/mm"})
        chart.set_y_axis({"name": "Selic (% a.a.)", "num_format": "0.00"})
        chart.set_legend({"none": True})
        chart.set_size({"width": 720, "height": 380})
        ws_resumo.insert_chart("D2", chart)


def gerar_grafico(tabela: pd.DataFrame) -> None:
    logging.info("Gerando gráfico PNG...")
    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.plot(tabela["data"], tabela["valor"], color=NAVY, linewidth=2,
            marker="o", markerfacecolor=ORANGE, markeredgecolor=ORANGE)
    ax.set_title(f"Evolução da Selic (% a.a.) - Últimas {len(tabela)} observações")
    ax.set_xlabel("Data")
    ax.set_ylabel("Selic (% a.a.)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: br(v)))
    minimo, maximo = tabela["valor"].min(), tabela["valor"].max()
    folga = max((maximo - minimo) * 0.25, 0.1)
    ax.set_ylim(minimo - folga, maximo + folga)
    ax.grid(True, alpha=0.25)
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    fig.savefig(GRAFICO_PATH, dpi=180)
    plt.close(fig)


def gerar_pdf(resumo: dict, fonte: str, ao_vivo: bool) -> None:
    logging.info("Gerando relatório PDF...")
    c = canvas.Canvas(str(PDF_PATH), pagesize=A4)
    c.setTitle("Relatório Executivo - Selic")
    c.setAuthor("Oficina de Robôs - BMA FIDC")
    w, h = A4
    navy = colors.HexColor(NAVY)
    orange = colors.HexColor(ORANGE)
    light = colors.HexColor("#F3F5F8")

    c.setFillColor(navy)
    c.rect(0, h - 110, w, 110, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(42, h - 60, "OFICINA DE ROBÔS - BMA FIDC")
    c.setFont("Helvetica", 12)
    c.drawString(42, h - 84, "Relatório Executivo - Selic")

    if not ao_vivo:
        c.setFillColor(orange)
        c.roundRect(42, h - 138, w - 84, 22, 5, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(52, h - 131, "ATENÇÃO: dados de contingência, não da consulta ao vivo. Veja a fonte no rodapé.")

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(42, h - 170, f'Selic - Últimas {resumo["registros"]} observações')

    indicadores = [
        (f'Primeiro valor ({resumo["data_inicial"]})', f'{br(resumo["primeiro"])}%'),
        (f'Último valor ({resumo["data_final"]})', f'{br(resumo["ultimo"])}%'),
        ("Variação no período", f'{"+" if resumo["variacao_pp"] > 0 else ""}{br(resumo["variacao_pp"])} p.p.'),
        ("Maior valor", f'{br(resumo["maior"])}%'),
        ("Menor valor", f'{br(resumo["menor"])}%'),
        ("Média", f'{br(resumo["media"])}%'),
    ]
    x0, y0 = 42, h - 240
    for i, (rotulo, valor) in enumerate(indicadores):
        col, row = i % 3, i // 3
        x, y = x0 + col * 175, y0 - row * 75
        c.setFillColor(light)
        c.roundRect(x, y, 155, 55, 8, fill=1, stroke=0)
        c.setFillColor(navy)
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
    texto = (
        f'A Selic anualizada base 252 passou de {br(resumo["primeiro"])}% para '
        f'{br(resumo["ultimo"])}% entre {resumo["data_inicial"]} e {resumo["data_final"]}, '
        f'com {movimento} ({"+" if resumo["variacao_pct"] > 0 else ""}{br(resumo["variacao_pct"])}%).'
    )
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(42, h - 405, "Resumo executivo")
    bloco = c.beginText(42, h - 425)
    bloco.setFont("Helvetica", 10)
    bloco.setLeading(15)
    for linha in textwrap.wrap(texto, 95):
        bloco.textLine(linha)
    c.drawText(bloco)
    c.drawImage(ImageReader(str(GRAFICO_PATH)), 48, 90, width=500, height=270, preserveAspectRatio=True)
    c.setFillColor(orange if not ao_vivo else colors.grey)
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
        logging.warning("Não foi possível abrir o PDF automaticamente: %s", erro)


def executar(args: argparse.Namespace) -> int:
    logging.info("=" * 52)
    logging.info("OFICINA DE ROBÔS - BMA FIDC  |  Robô Selic v%s", VERSAO)
    logging.info("=" * 52)
    tabela, fonte, ao_vivo = obter_dados(args.offline)
    resumo = calcular_resumo(tabela)
    logging.info("Período: %s a %s | Registros: %s", resumo["data_inicial"], resumo["data_final"], resumo["registros"])
    logging.info("Último valor: %s%% | Variação: %s p.p.", br(resumo["ultimo"]), br(resumo["variacao_pp"]))
    gerar_excel(tabela, resumo, fonte)
    gerar_grafico(tabela)
    gerar_pdf(resumo, fonte, ao_vivo)
    logging.info("Excel: %s", EXCEL_PATH)
    logging.info("Gráfico: %s", GRAFICO_PATH)
    logging.info("PDF: %s", PDF_PATH)
    logging.info("Fonte dos dados: %s", fonte)
    if ao_vivo:
        logging.info("Processo concluído com sucesso (dados ao vivo do Banco Central).")
    else:
        logging.warning("Processo concluído com DADOS DE CONTINGÊNCIA (não é a consulta ao vivo).")
    if not args.no_open:
        abrir_arquivo(PDF_PATH)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Robô Selic - Oficina de Robôs BMA")
    parser.add_argument("--offline", action="store_true", help="Não usa a internet (última consulta salva ou exemplo).")
    parser.add_argument("--no-open", action="store_true", help="Não abre o PDF ao final.")
    parser.add_argument("--no-pause", action="store_true", help="Não espera ENTER ao final (executável).")
    args = parser.parse_args()
    preparar_pastas()
    configurar_log()
    try:
        codigo = executar(args)
    except Exception:  # noqa: BLE001 - qualquer falha precisa aparecer na tela e no log
        logging.exception("O robô falhou. Detalhes acima e em %s", LOG_DIR / "oficina.log")
        codigo = 1
    if getattr(sys, "frozen", False) and not args.no_pause and sys.stdin and sys.stdin.isatty():
        print(f"\nResultados em: {OUTPUT_DIR}")
        input("Pressione ENTER para fechar...")
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
