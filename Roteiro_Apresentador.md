# Roteiro do apresentador - 30 minutos

Slides: `apresentacao/BMA-Oficina-de-Robos_com_QR.pptx` (15 slides).

## Na véspera (10 minutos)

1. Instale com `Instalador_OficinaRobos_BMA.exe` no notebook da apresentação e
   rode o atalho **Robô Selic** uma vez com internet. Isso deixa a "última
   consulta salva" pronta como plano B e deixa a primeira execução mais rápida.
2. Feche o robô e o PDF. Deixe à mão: a apresentação, a pasta do instalador e o
   atalho **Resultados do Robô Selic**.
3. Teste o QR do slide 15 com a câmera do celular.

## No dia

| # | Slide | Tempo | O que fazer |
| --- | --- | --- | --- |
| 1 | 01 Capa | 1 min | Objetivo: sair sabendo transformar uma tarefa repetitiva em robô. |
| 2 | 02 O problema | 2 min | Pergunte quem faz alguma dessas tarefas toda semana. |
| 3 | 03 O que é um robô | 2 min | Robô de software: faz no computador o que faríamos à mão. |
| 4 | 04 O segredo | 2 min | Antes: a pessoa faz tudo. Depois: o robô faz e a pessoa recebe o resultado. |
| 5 | 05 Desafio Selic | 1 min | Dados oficiais, públicos e gratuitos. |
| 6 | 06 O prompt | 2 min | Quanto melhor a instrução, melhor o código. O prompt completo está no repositório. |
| 7 | 07 IAs gratuitas | 2 min | Qualquer uma serve; compare as respostas. **Nunca cole dados internos.** |
| 8 | Demo: instalador | 3 min | Dois cliques em `Instalador_OficinaRobos_BMA.exe` → **Instalar** (ou ENTER). A etapa "Criando atalhos" leva até 1 minuto: aproveite para explicar que não precisa de Python. |
| 9 | 08 Demo: robô | 5 min | Clique em **Abrir o Robô Selic** (ou no atalho da Área de Trabalho). Mostre as mensagens na janela e o PDF abrindo sozinho. Termine com ENTER na janela preta. |
| 10 | 09 Resultado | 3 min | Atalho **Resultados do Robô Selic** → `output\selic.xlsx`: abas Dados e Resumo, com gráfico. |
| 11 | 10 Resumo executivo | 2 min | Mostre o PDF e confira um valor no site do Banco Central. |
| 12 | 11 Outras aplicações | 2 min | PTAX, IPCA, CNPJ, CNAB, relatórios... |
| 13 | 12 Desafio | 2 min | Cada um pensa numa tarefa semanal que pode virar robô. |
| 14 | 13 Próxima oficina | 1 min | Votação do próximo robô. |
| 15 | 14-15 Encerramento e QR | 1 min | Peça para escanearem o QR: instalador, código, prompt e apostila. |

Os números dos slides 08 a 10 são da consulta de 23/09/2026 (13,90% → 13,65%).
Ao vivo o robô traz o dia mais recente; se as datas mudarem, é o esperado.

## Plano B (se algo falhar ao vivo)

| Problema | O que fazer |
| --- | --- |
| Sem internet ou Banco Central fora do ar | O robô usa sozinho a última consulta salva e avisa em laranja. Diga: "é a contingência funcionando". Ou use o atalho **Robô Selic (offline)**. |
| Windows diz "O Windows protegeu o computador" | **Mais informações → Executar assim mesmo** (o instalador não é assinado). |
| Instalador avisa que não criou os atalhos | O robô foi instalado mesmo assim: abra o `RoboSelic.exe` no caminho que o aviso mostra (política da máquina bloqueou o PowerShell). |
| Antivírus bloqueou o instalador | Use `RoboSelic_portatil.zip` (extrair e rodar `RoboSelic.exe`) ou `codigo\executar_offline.bat` (precisa de Python). |
| A janela preta demora para mostrar algo | Na primeira execução o Windows verifica os arquivos; leva de 10 a 30 segundos. |
| PDF não abriu | Atalho **Resultados do Robô Selic** → `output\resumo_selic.pdf`. |
| Precisa mostrar o log | `Documentos\Oficina de Robos BMA\logs\oficina.log`. |
