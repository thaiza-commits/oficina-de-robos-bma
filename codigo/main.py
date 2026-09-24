from __future__ import annotations

import argparse
import logging
import os
import platform
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import requests
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

SERIE_SELIC = 1178
API_URL = (
    "https://api.bcb.gov.br/dados/serie/"
    f"bcdata.sgs.{SERIE_SELIC}/dados/ultimos/30?formato=json"
)

BASE_DIR = Path(__file__).resolve().parent.parent
DADOS_DIR = BASE_DIR / "dados"
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"

EXCEL_PATH = OUTPUT_DIR / "selic.xlsx"
GRAFICO_PATH = OUTPUT_DIR / "selic.png"
PDF_PATH = OUTPUT_DIR / "resumo_selic.pdf"
ARQUIVO_FALLBACK = DADOS_DIR / "exemplo_selic.csv"


def preparar_pastas() -> None:
    for pasta in (DADOS_DIR, OUTPUT_DIR, LOG_DIR):
        pasta.mkdir(parents=True, exist_ok=True)


def configurar_log() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "oficina.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def consultar_bacen() -> pd.DataFrame:
    logging.info("Consultando a API do Banco Central...")
    resposta = requests.get(API_URL, timeout=30)
    resposta.raise_for_status()
    dados = resposta.json()
    if not dados:
        raise ValueError("A API não retornou dados.")

    tabela = pd.DataFrame(dados)
    tabela["data"] = pd.to_datetime(tabela["data"], format="%d/%m/%Y")
    tabela["valor"] = pd.to_numeric(
        tabela["valor"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )
    tabela = tabela.dropna().sort_values("data").reset_index(drop=True)
    if tabela.empty:
        raise ValueError("Os dados retornados não puderam ser processados.")
    return tabela


def carregar_exemplo() -> pd.DataFrame:
    logging.warning("Usando dados de exemplo para garantir a demonstração.")
    tabela = pd.read_csv(
        ARQUIVO_FALLBACK,
        sep=";",
        decimal=",",
        parse_dates=["data"],
        dayfirst=True,
    )
    return tabela.sort_values("data").reset_index(drop=True)


def obter_dados(modo_offline: bool) -> pd.DataFrame:
    if modo_offline:
        return carregar_exemplo()
    try:
        return consultar_bacen()
    except (requests.RequestException, ValueError, KeyError) as erro:
        logging.error("Falha na consulta online: %s", erro)
        return carregar_exemplo()


def calcular_resumo(tabela: pd.DataFrame) -> dict:
    primeiro = float(tabela.iloc[0]["valor"])
    ultimo = float(tabela.iloc[-1]["valor"])
    variacao_pp = ultimo - primeiro
    variacao_pct = (variacao_pp / primeiro * 100) if primeiro else 0.0
    return {
        "data_inicial": tabela.iloc[0]["data"].strftime("%d/%m/%Y"),
        "data_final": tabela.iloc[-1]["data"].strftime("%d/%m/%Y"),
        "primeiro": primeiro,
        "ultimo": ultimo,
        "maior": float(tabela["valor"].max()),
        "menor": float(tabela["valor"].min()),
        "media": float(tabela["valor"].mean()),
        "variacao_pp": variacao_pp,
        "variacao_pct": variacao_pct,
    }


def gerar_excel(tabela: pd.DataFrame, resumo: dict) -> None:
    logging.info("Gerando planilha Excel...")
    dados_excel = tabela.rename(columns={"data": "Data", "valor": "Selic (% a.a.)"})
    with pd.ExcelWriter(EXCEL_PATH, engine="xlsxwriter", datetime_format="dd/mm/yyyy") as writer:
        dados_excel.to_excel(writer, sheet_name="Dados", index=False)
        resumo_df = pd.DataFrame({
            "Indicador": ["Primeiro valor","Último valor","Maior valor","Menor valor","Média","Variação (p.p.)","Variação (%)"],
            "Valor": [resumo["primeiro"],resumo["ultimo"],resumo["maior"],resumo["menor"],resumo["media"],resumo["variacao_pp"],resumo["variacao_pct"]/100],
        })
        resumo_df.to_excel(writer, sheet_name="Resumo", index=False)

        workbook = writer.book
        ws_dados = writer.sheets["Dados"]
        ws_resumo = writer.sheets["Resumo"]
        navy = "#0B1D3A"; orange = "#F28C2B"
        header = workbook.add_format({"bold":True,"font_color":"white","bg_color":navy,"align":"center"})
        taxa = workbook.add_format({"num_format":"0.00"})
        pct = workbook.add_format({"num_format":"0.00%"})
        ws_dados.set_row(0,24,header); ws_dados.set_column("A:A",15); ws_dados.set_column("B:B",18,taxa)
        ws_dados.freeze_panes(1,0); ws_dados.autofilter(0,0,len(dados_excel),1)
        ws_resumo.set_row(0,24,header); ws_resumo.set_column("A:A",24); ws_resumo.set_column("B:B",18,taxa)
        ws_resumo.set_column("B8:B8",18,pct)

        chart = workbook.add_chart({"type":"line"})
        chart.add_series({
            "name":"Selic (% a.a.)",
            "categories":["Dados",1,0,len(dados_excel),0],
            "values":["Dados",1,1,len(dados_excel),1],
            "line":{"color":navy,"width":2.25},
            "marker":{"type":"circle","size":4,"border":{"color":orange}},
        })
        chart.set_title({"name":"Evolução da Selic"})
        chart.set_x_axis({"name":"Data","date_axis":True,"num_format":"dd/mm"})
        chart.set_y_axis({"name":"Selic (% a.a.)"})
        chart.set_legend({"none":True})
        chart.set_size({"width":720,"height":380})
        ws_resumo.insert_chart("D2",chart)


def gerar_grafico(tabela: pd.DataFrame) -> None:
    logging.info("Gerando gráfico PNG...")
    plt.figure(figsize=(10,5.4))
    plt.plot(tabela["data"],tabela["valor"],marker="o",linewidth=2)
    plt.title("Evolução da Selic (% a.a.) - Últimas 30 observações")
    plt.xlabel("Data"); plt.ylabel("Selic (% a.a.)")
    plt.grid(True,alpha=.25); plt.xticks(rotation=45); plt.tight_layout()
    plt.savefig(GRAFICO_PATH,dpi=180); plt.close()


def gerar_pdf(resumo: dict) -> None:
    logging.info("Gerando relatório PDF...")
    c = canvas.Canvas(str(PDF_PATH), pagesize=A4)
    w,h=A4
    navy=colors.HexColor("#0B1D3A"); light=colors.HexColor("#F3F5F8")
    c.setFillColor(navy); c.rect(0,h-110,w,110,fill=1,stroke=0)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold",22)
    c.drawString(42,h-60,"OFICINA DE ROBÔS - BMA FIDC")
    c.setFont("Helvetica",12); c.drawString(42,h-84,"Relatório Executivo - Selic")
    c.setFillColor(colors.black); c.setFont("Helvetica-Bold",18)
    c.drawString(42,h-145,"Selic - Últimas 30 observações")

    indicadores=[
        ("Primeiro valor",f'{resumo["primeiro"]:.2f}%'),
        ("Último valor",f'{resumo["ultimo"]:.2f}%'),
        ("Maior valor",f'{resumo["maior"]:.2f}%'),
        ("Menor valor",f'{resumo["menor"]:.2f}%'),
        ("Média",f'{resumo["media"]:.2f}%'),
        ("Variação",f'{resumo["variacao_pp"]:+.2f} p.p.'),
    ]
    x0,y0=42,h-210
    for i,(rotulo,valor) in enumerate(indicadores):
        col=i%3; row=i//3; x=x0+col*175; y=y0-row*75
        c.setFillColor(light); c.roundRect(x,y,155,55,8,fill=1,stroke=0)
        c.setFillColor(navy); c.setFont("Helvetica",9); c.drawString(x+12,y+35,rotulo)
        c.setFont("Helvetica-Bold",16); c.drawString(x+12,y+14,valor)

    c.setFillColor(colors.black); c.setFont("Helvetica-Bold",12)
    c.drawString(42,h-380,"Resumo executivo")
    texto=(f'A Selic anualizada base 252 passou de {resumo["primeiro"]:.2f}% para '
           f'{resumo["ultimo"]:.2f}% entre {resumo["data_inicial"]} e {resumo["data_final"]}, '
           f'com variação de {resumo["variacao_pp"]:+.2f} ponto percentual.')
    bloco=c.beginText(42,h-400); bloco.setFont("Helvetica",10); bloco.setLeading(15)
    for i in range(0,len(texto),95): bloco.textLine(texto[i:i+95])
    c.drawText(bloco)
    c.drawImage(ImageReader(str(GRAFICO_PATH)),48,90,width=500,height=270,preserveAspectRatio=True)
    c.setFillColor(colors.grey); c.setFont("Helvetica",8)
    c.drawString(42,42,"Fonte: Banco Central do Brasil - SGS, série 1178.")
    c.save()


def abrir_arquivo(caminho: Path) -> None:
    try:
        sistema=platform.system()
        if sistema=="Windows":
            os.startfile(caminho)  # type: ignore[attr-defined]
        elif sistema=="Darwin":
            subprocess.run(["open",str(caminho)],check=False)
        else:
            subprocess.run(["xdg-open",str(caminho)],check=False)
    except OSError as erro:
        logging.warning("Não foi possível abrir o PDF automaticamente: %s",erro)


def main() -> int:
    parser=argparse.ArgumentParser(description="Robô Selic - Oficina de Robôs BMA")
    parser.add_argument("--offline",action="store_true",help="Usa o arquivo de exemplo.")
    parser.add_argument("--no-open",action="store_true",help="Não abre o PDF ao final.")
    args=parser.parse_args()
    preparar_pastas(); configurar_log()
    logging.info("="*52); logging.info("OFICINA DE ROBÔS - BMA FIDC"); logging.info("="*52)
    tabela=obter_dados(args.offline)
    resumo=calcular_resumo(tabela)
    gerar_excel(tabela,resumo); gerar_grafico(tabela); gerar_pdf(resumo)
    logging.info("Excel: %s",EXCEL_PATH); logging.info("Gráfico: %s",GRAFICO_PATH)
    logging.info("PDF: %s",PDF_PATH); logging.info("Processo concluído com sucesso.")
    if not args.no_open: abrir_arquivo(PDF_PATH)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
