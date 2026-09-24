# Oficina de Robôs - BMA FIDC

**Automatize tarefas. Ganhe tempo. Gere valor.**

Material da Oficina de Robôs: um robô em Python que consulta a Selic no Banco
Central e entrega **Excel, gráfico, PDF e log**, mais a apresentação, a apostila,
o guia executivo e o prompt para você gerar o seu com uma IA gratuita.

## Baixar e instalar (Windows)

1. Baixe o **[Instalador_OficinaRobos_BMA.exe](https://github.com/thaiza-commits/oficina-de-robos-bma/releases/latest/download/Instalador_OficinaRobos_BMA.exe)** (~64 MB).
2. Dê dois cliques e clique em **Instalar**. Não precisa de Python nem de administrador.
   - Se o Windows mostrar *"O Windows protegeu o computador"*, clique em
     **Mais informações → Executar assim mesmo** (o instalador não é assinado
     digitalmente).
3. Na Área de Trabalho aparecem três atalhos:
   - **Robô Selic**: consulta a Selic ao vivo no Banco Central;
   - **Robô Selic (offline)**: roda sem internet (usa a última consulta salva);
   - **Resultados do Robô Selic**: abre a pasta com Excel, gráfico, PDF, prompt e apostila.

Prefere não instalar? Baixe o
[RoboSelic_portatil.zip](https://github.com/thaiza-commits/oficina-de-robos-bma/releases/latest/download/RoboSelic_portatil.zip),
extraia e rode `RoboSelic.exe`.

Para desinstalar: Configurações → Aplicativos → **Oficina de Robôs BMA** →
Desinstalar (ou Menu Iniciar → Oficina de Robôs BMA → Desinstalar). Os
resultados em Documentos são preservados.

## O que o robô faz

1. Consulta a série 1178 (Selic anualizada base 252) na API pública SGS do
   Banco Central e fica com as **últimas 30 observações**.
2. Salva uma cópia da consulta para usar se a internet falhar.
3. Gera `selic.xlsx` (abas Dados e Resumo, com gráfico), `selic.png` e
   `resumo_selic.pdf`, e registra tudo em `oficina.log`.
4. Abre o PDF ao final.

Sem internet, o robô usa a **última consulta salva** ou, se não houver
nenhuma, os **dados de exemplo**, e avisa isso na tela, no Excel (linha
*Fonte*) e no PDF (faixa laranja). Ele nunca apresenta dados de contingência
como se fossem da consulta ao vivo.

| Onde ficam os resultados | Instalado | Rodando pelo Python |
| --- | --- | --- |
| Excel, gráfico e PDF | `Documentos\Oficina de Robos BMA\output` | `output\` |
| Log | `Documentos\Oficina de Robos BMA\logs\oficina.log` | `logs\oficina.log` |
| Última consulta salva | `Documentos\Oficina de Robos BMA\dados` | `dados\ultima_consulta_selic.csv` |

## Rodar pelo código (com Python)

1. Instale o [Python 3.11 ou superior](https://www.python.org/downloads/)
   marcando **Add python.exe to PATH**.
2. Abra a pasta `codigo` e dê dois cliques em `executar_oficina.bat`
   (ou `executar_offline.bat` para rodar sem internet). Na primeira vez ele
   instala as bibliotecas do `requirements.txt`.

Pela linha de comando: `python codigo/main.py [--offline] [--no-open]`.

## Faça o seu com IA gratuita

O arquivo [`prompt/prompt_oficina.txt`](prompt/prompt_oficina.txt) tem o
**prompt completo** que descreve este robô. Cole em qualquer IA gratuita
(ChatGPT, Claude, Gemini, Microsoft Copilot…) para obter o mesmo resultado.
O slide 07 da apresentação lista oito IAs gratuitas e para que cada uma serve.

> Nunca cole dados de clientes, senhas ou informações internas em uma IA pública.

## Conteúdo do repositório

| Pasta / arquivo | O que é |
| --- | --- |
| `apresentacao/` | Slides da oficina (`_com_QR` é a versão completa, com o QR Code) |
| `apostila/` | Guia rápido de 1 página para o participante |
| `Guia-Executivo-BMA-Profissional.docx` | Guia executivo do participante |
| `Roteiro_Apresentador.md` | Roteiro de 30 minutos e plano B para a apresentação ao vivo |
| `codigo/` | Robô Selic (`main.py`), bibliotecas e atalhos `.bat` |
| `dados/exemplo_selic.csv` | Dados de exemplo (30 observações reais de 12/08 a 23/09/2026) |
| `output/`, `logs/` | Exemplo de Excel, gráfico, PDF e log gerados pelo robô |
| `prompt/` | Prompt completo para gerar o robô com IA |
| `instalador/` | Código do instalador e `gerar_instalador.bat` para gerar o `.exe` |
| `qr-code/` | QR Code deste repositório e o script que o gera |
| `links/links_uteis.txt` | Links do Banco Central, Python, VS Code e IAs gratuitas |

## Gerar o instalador de novo

Com Python 3.11+ e internet, rode `instalador\gerar_instalador.bat`. Ele cria
um ambiente em `%TEMP%`, gera o `RoboSelic.exe`, **testa o robô em modo
offline** e só então monta `instalador\dist\Instalador_OficinaRobos_BMA.exe`
e `RoboSelic_portatil.zip`.

Fonte dos dados: Banco Central do Brasil, SGS, série 1178. Dados públicos e gratuitos.
