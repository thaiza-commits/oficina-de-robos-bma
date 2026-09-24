"""Gera Apostila_Oficina_de_Robos.pdf (1 página A4). Rode: python gerar_apostila.py"""
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "codigo"))
from main import LARANJA, PRIMARIA, desenhar_logo  # noqa: E402 - mesma identidade e logo do robô

SAIDA = Path(__file__).with_name("Apostila_Oficina_de_Robos.pdf")
NAVY = colors.HexColor(PRIMARIA)
ORANGE = colors.HexColor(LARANJA)
LIGHT = colors.HexColor("#F1F2F5")
CINZA = colors.HexColor("#555555")
REPO = "github.com/thaiza-commits/oficina-de-robos-bma"

c = canvas.Canvas(str(SAIDA), pagesize=A4)
c.setTitle("Apostila - Oficina de Robôs BMA")
c.setAuthor("Oficina de Robôs - BMA FIDC")
w, h = A4

c.setFillColor(NAVY)
c.rect(0, h - 100, w, 100, fill=1, stroke=0)
desenhar_logo(c, w - 38 - 100, h - 78, 100)
c.setFillColor(colors.white)
c.setFont("Helvetica-Bold", 24)
c.drawString(38, h - 52, "OFICINA DE ROBÔS")
c.setFillColor(ORANGE)
c.setFont("Helvetica", 12)
c.drawString(38, h - 76, "Guia rápido para criar sua primeira automação")

passos = [
    ("Identifique", "Escolha uma tarefa repetitiva e com regra clara."),
    ("Descreva", "Explique para a IA a fonte, as regras, as etapas e o resultado esperado."),
    ("Gere", "Peça código simples e somente bibliotecas gratuitas."),
    ("Teste", "Use poucos dados e compare o resultado com a fonte oficial."),
    ("Melhore", "Inclua contingência, tratamento de erros, logs e saída visual."),
]
y = h - 148
for i, (titulo, texto) in enumerate(passos, start=1):
    c.setFillColor(ORANGE)
    c.circle(55, y + 8, 15, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(55, y + 4, str(i))
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(82, y + 12, titulo)
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    c.drawString(82, y - 4, texto)
    y -= 56

# Como rodar o robô da oficina
y = h - 432
c.setFillColor(NAVY)
c.setFont("Helvetica-Bold", 13)
c.drawString(40, y, "Como rodar o Robô Selic")
c.setFont("Helvetica", 9.5)
c.setFillColor(colors.black)
linhas = [
    "1. Baixe Instalador_OficinaRobos_BMA.exe pelo QR Code ou em " + REPO + ".",
    "2. Dois cliques > Instalar. Se o Windows avisar, clique em Mais informações > Executar assim mesmo.",
    "3. Abra o atalho Robô Selic: o painel com os últimos 12 meses abre sozinho no navegador.",
    "Outro período? Use Robô Selic (escolher período). Sem internet? Use Robô Selic (offline).",
]
for k, linha in enumerate(linhas):
    c.drawString(40, y - 18 - k * 14, linha)

# IAs gratuitas
y = h - 522
c.setFillColor(NAVY)
c.setFont("Helvetica-Bold", 13)
c.drawString(40, y, "IAs gratuitas para colar o prompt")
ias = [("ChatGPT", "chatgpt.com"), ("Claude", "claude.ai"), ("Gemini", "gemini.google.com"),
       ("Microsoft Copilot", "copilot.microsoft.com"), ("Perplexity", "perplexity.ai"), ("NotebookLM", "notebooklm.google.com")]
for k, (nome, site) in enumerate(ias):
    col, lin = k % 2, k // 2
    x, yy = 40 + col * 260, y - 20 - lin * 15
    c.setFont("Helvetica-Bold", 9.5)
    c.setFillColor(colors.black)
    c.drawString(x, yy, nome)
    c.setFont("Helvetica", 9)
    c.setFillColor(CINZA)
    c.drawString(x + c.stringWidth(nome, "Helvetica-Bold", 9.5) + 5, yy, site)
c.setFillColor(ORANGE)
c.setFont("Helvetica-Bold", 9.5)
c.drawString(40, y - 70, "Nunca cole dados de clientes, senhas ou informações internas numa IA pública.")

# Prompt
c.setFillColor(LIGHT)
c.roundRect(38, 100, w - 76, 135, 8, fill=1, stroke=0)
c.setFillColor(NAVY)
c.setFont("Helvetica-Bold", 13)
c.drawString(52, 214, "Prompt utilizado")
c.setFont("Helvetica", 9.5)
prompt = [
    "Crie um programa em Python que consulte a API pública do Banco Central do Brasil (SGS) e obtenha a",
    "série 1178 (Selic anualizada base 252) no período escolhido - por padrão, os últimos 12 meses. O",
    "programa deve tratar erros e usar contingência se a internet falhar, gerar um painel visual em HTML",
    "com gráficos e indicadores, um Excel com as abas Dados, Resumo e Mudanças, um relatório PDF,",
    "registrar a execução em log e usar só bibliotecas gratuitas.",
]
for k, linha in enumerate(prompt):
    c.drawString(52, 196 - k * 14, linha)
c.setFillColor(ORANGE)
c.setFont("Helvetica-Bold", 9)
c.drawString(52, 110, "Prompt completo (mesmo resultado do robô da oficina): prompt/prompt_oficina.txt no repositório.")

c.setFillColor(NAVY)
c.setFont("Helvetica-Bold", 11)
c.drawString(40, 80, "Sua ideia de robô:")
c.setStrokeColor(colors.HexColor("#B8C0CC"))
for yy in (62, 44):
    c.line(40, yy, w - 40, yy)
c.setFillColor(CINZA)
c.setFont("Helvetica", 8)
c.drawString(40, 22, f"Oficina de Robôs - BMA FIDC  |  {REPO}")
c.save()
print(f"Apostila gerada em: {SAIDA}")
