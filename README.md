# Oficina de Robôs - BMA FIDC

**Automatize tarefas. Ganhe tempo. Gere valor.**

Material da Oficina de Robôs: um robô em Python que consulta a Selic no Banco
Central e mostra os resultados **num painel visual na tela**, com a identidade
da BMA FIDC, além de **Excel, gráfico, PDF e log**. Aqui também estão a
apresentação, a apostila, o guia executivo e o prompt para você gerar o seu
robô com uma IA gratuita.

## Baixar e instalar (Windows)

1. Baixe o **[Instalador_OficinaRobos_BMA.exe](https://github.com/thaiza-commits/oficina-de-robos-bma/releases/latest/download/Instalador_OficinaRobos_BMA.exe)** (~64 MB).
2. Dê dois cliques e clique em **Instalar**. Não precisa de Python nem de administrador.
   - Se o Windows mostrar *"O Windows protegeu o computador"*, clique em
     **Mais informações → Executar assim mesmo** (o instalador não é assinado
     digitalmente).
3. Na Área de Trabalho aparecem quatro atalhos:
   - **Robô Selic**: consulta os últimos 12 meses ao vivo e abre o painel;
   - **Robô Selic (escolher período)**: pergunta as datas antes de consultar;
   - **Robô Selic (offline)**: roda sem internet (usa a última consulta salva);
   - **Resultados do Robô Selic**: abre a pasta com painel, Excel, gráfico,
     PDF, prompt e apostila.

No Menu Iniciar (pasta **Oficina de Robôs BMA**) há também **Parâmetros do
Robô Selic**, que abre o `parametros.ini`, e **Desinstalar**.

Prefere não instalar? Baixe o
[RoboSelic_portatil.zip](https://github.com/thaiza-commits/oficina-de-robos-bma/releases/latest/download/RoboSelic_portatil.zip),
extraia e rode `RoboSelic.exe`.

Para desinstalar: Configurações → Aplicativos → **Oficina de Robôs BMA** →
Desinstalar. Os resultados em Documentos são preservados.

## O painel

Ao final de cada execução, o robô abre `painel_selic.html` no navegador:

- **indicadores:** Selic atual, variação no período, mudanças da taxa, maior, menor e média;
- **gráfico da Selic** em degraus, com as decisões do Copom marcadas e o valor ao passar o mouse;
- **tabela de mudanças da taxa**, com a comparação com 12 meses atrás;
- **média mensal**;
- **filtros 1M, 3M, 6M, 12M e Tudo**, além de datas livres, que recalculam tudo na hora.

É um arquivo único, sem internet: dá para abrir de novo, enviar por e-mail
ou apresentar offline.

## Escolher o período

O padrão são os **últimos 12 meses**. Para mudar, use uma destas opções (a
mais forte primeiro):

| Onde | Como |
| --- | --- |
| Linha de comando | `--meses 24`, ou `--inicio 01/01/2020 --fim 31/12/2025` |
| Atalho **Robô Selic (escolher período)** | digite as datas na tela (ENTER mantém o padrão) |
| `parametros.ini` | edite `meses` ou `data_inicial` / `data_final` no Bloco de Notas |

O `parametros.ini` também define o que abrir ao final: `painel`, `pdf`,
`ambos` ou `nenhum`. Períodos longos são consultados em blocos de 10 anos (a
série começa em 1986).

## O que o robô faz

1. Consulta a série 1178 (Selic anualizada base 252) na API pública SGS do
   Banco Central. Se a conexão oscilar, tenta de novo até 3 vezes.
2. Guarda tudo o que já consultou, para usar se a internet falhar.
3. Gera `painel_selic.html`, `selic.xlsx` (abas Dados, Resumo e Mudanças,
   com gráfico), `selic.png` e `resumo_selic.pdf`, e registra tudo em
   `oficina.log`.
4. Abre o painel.

Sem internet, o robô usa a **última consulta salva** ou, se não houver
nenhuma, os **dados de exemplo**. Ele avisa em laranja na tela, no painel, no
Excel e no PDF, e nunca apresenta dados de contingência como se fossem da
consulta ao vivo.

| Onde ficam os resultados | Instalado | Rodando pelo Python |
| --- | --- | --- |
| Painel, Excel, gráfico e PDF | `Documentos\Oficina de Robos BMA\output` | `output\` |
| Parâmetros | `Documentos\Oficina de Robos BMA\parametros.ini` | `parametros.ini` |
| Log | `Documentos\Oficina de Robos BMA\logs\oficina.log` | `logs\oficina.log` |
| Consultas salvas | `Documentos\Oficina de Robos BMA\dados` | `dados\ultima_consulta_selic.csv` |

## Rodar pelo código (com Python)

1. Instale o [Python 3.11 ou superior](https://www.python.org/downloads/)
   marcando **Add python.exe to PATH**.
2. Na pasta `codigo`, dê dois cliques em `executar_oficina.bat`,
   `executar_escolher_periodo.bat` ou `executar_offline.bat`. Na primeira
   vez eles instalam as bibliotecas do `requirements.txt`.

Pela linha de comando: `python codigo/main.py [--meses N | --inicio DD/MM/AAAA --fim DD/MM/AAAA] [--perguntar] [--offline] [--abrir painel|pdf|ambos|nenhum]`.

## Faça o seu com IA gratuita

O arquivo [`prompt/prompt_oficina.txt`](prompt/prompt_oficina.txt) tem o
**prompt completo** que descreve este robô: painel, período, Excel, PDF e
contingência. Cole em qualquer IA gratuita (ChatGPT, Claude, Gemini,
Microsoft Copilot…) para obter o mesmo resultado. O slide 07 lista oito IAs
gratuitas e para que cada uma serve.

> Nunca cole dados de clientes, senhas ou informações internas em uma IA pública.

## Conteúdo do repositório

| Pasta / arquivo | O que é |
| --- | --- |
| `apresentacao/` | Slides da oficina (`_com_QR` é a versão completa, com o QR Code) |
| `apostila/` | Guia rápido de 1 página para o participante (e o script que o gera) |
| `Guia-Executivo-BMA-Profissional.docx` | Guia executivo do participante |
| `Roteiro_Apresentador.md` | Roteiro de 30 minutos e plano B para a apresentação ao vivo |
| `codigo/` | Robô Selic (`main.py`), modelo do painel, logo, bibliotecas e atalhos `.bat` |
| `parametros.ini` | Período padrão e o que abrir ao final |
| `dados/exemplo_selic.csv` | Dados de exemplo (251 observações reais, 24/09/2025 a 23/09/2026) |
| `output/`, `logs/` | Exemplo de painel, Excel, gráfico, PDF e log gerados pelo robô |
| `prompt/` | Prompt completo para gerar o robô com IA |
| `instalador/` | Código do instalador e `gerar_instalador.bat` para gerar o `.exe` |
| `qr-code/` | QR Code deste repositório e o script que o gera |
| `links/links_uteis.txt` | Links do Banco Central, Python, VS Code e IAs gratuitas |

## Gerar o instalador de novo

Com Python 3.11+ e internet, rode `instalador\gerar_instalador.bat`. Ele cria
um ambiente em `%TEMP%`, gera o `RoboSelic.exe`, **testa o robô em modo
offline** (inclusive a geração do painel) e só então monta
`instalador\dist\Instalador_OficinaRobos_BMA.exe` e `RoboSelic_portatil.zip`.

Identidade visual: cores e logo de [bmafidc.com.br](https://bmafidc.com.br).
Fonte dos dados: Banco Central do Brasil, SGS, série 1178. Dados públicos e gratuitos.
