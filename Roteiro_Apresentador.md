# Roteiro do apresentador - 30 minutos

Slides: `apresentacao/BMA-Oficina-de-Robos_com_QR.pptx` (16 slides).

## Na véspera (10 minutos)

1. Instale com `Instalador_OficinaRobos_BMA.exe` no computador da
   apresentação e rode o atalho **Robô Selic** uma vez com a internet de lá.
   Confira que o painel abre com o selo azul **DADOS AO VIVO**. Isso deixa a
   "última consulta salva" pronta como plano B e a primeira execução mais
   rápida.
2. Feche o robô e o navegador. Deixe à mão: a apresentação, a pasta do
   instalador e o atalho **Resultados do Robô Selic**.
3. Teste o QR do slide 16 com a câmera do celular.

## No dia

| # | Slide | Tempo | O que fazer |
| --- | --- | --- | --- |
| 1 | 01 Capa | 1 min | Objetivo: sair sabendo transformar uma tarefa repetitiva em robô. |
| 2 | 02 O problema | 2 min | Pergunte quem faz alguma dessas tarefas toda semana. |
| 3 | 03 O que é um robô | 1 min | Robô de software: faz no computador o que faríamos à mão. |
| 4 | 04 O segredo | 1 min | Antes: a pessoa faz tudo. Depois: o robô faz e a pessoa recebe o resultado. |
| 5 | 05 Desafio Selic | 1 min | Dados oficiais, públicos e gratuitos. |
| 6 | 06 O prompt | 2 min | Quanto melhor a instrução, melhor o código. Mostre por que cada linha está ali: sem "dataInicial e dataFinal" a IA costuma usar um endereço da API que falha; sem "avisar em destaque" ela inventa dados quando a internet cai; sem "HTML offline" o painel depende de internet. O slide é um resumo; o prompt completo (QR do final) gera o mesmo robô da demonstração. |
| 7 | 07 IAs gratuitas | 2 min | Qualquer uma serve; compare as respostas. **Nunca cole dados internos.** |
| 8 | Demo: instalador | 3 min | Dois cliques em `Instalador_OficinaRobos_BMA.exe` → **Instalar** (ou ENTER). A etapa "Criando atalhos" leva até 1 minuto: aproveite para explicar que não precisa de Python. |
| 9 | 08 Demo: robô | 3 min | Clique em **Abrir o Robô Selic**. Mostre as mensagens na janela preta; ao final o painel abre sozinho no navegador. |
| 10 | 09 O painel na tela | 5 min | No painel ao vivo: passe o mouse no gráfico, mostre os 5 cortes do Copom na tabela e clique em **3M** e **12M**. Deixe a plateia escolher um período: feche o painel, dê ENTER na janela preta e rode **Robô Selic (escolher período)**, por exemplo com 01/01/2020. |
| 11 | 10 Resultado | 2 min | Atalho **Resultados do Robô Selic** → `output\selic.xlsx`: abas Dados, Resumo e Mudanças. |
| 12 | 11 Resumo executivo | 1 min | Abra o `resumo_selic.pdf` e confira um valor no site do Banco Central. |
| 13 | 12 Outras aplicações | 2 min | PTAX, IPCA, CNPJ, CNAB, relatórios... |
| 14 | 13 Desafio | 2 min | Cada um pensa numa tarefa semanal que pode virar robô. |
| 15 | 14 Próxima oficina | 1 min | Votação do próximo robô. |
| 16 | 15-16 Encerramento e QR | 1 min | Peça para escanearem o QR: instalador, código, prompt e apostila. |

Os números dos slides 08 a 11 são dos últimos 12 meses até 23/09/2026
(14,90% → 13,65%, 5 cortes de 0,25). Ao vivo o robô traz o dia mais recente;
se as datas mudarem um dia, é o esperado.

## Plano B (se algo falhar ao vivo)

| Problema | O que fazer |
| --- | --- |
| Internet oscilou | O robô tenta 3 vezes sozinho (aparece "Tentativa 1 de 3 falhou" na janela). |
| Sem internet ou Banco Central fora do ar | O robô usa a última consulta salva e mostra o selo laranja **CONTINGÊNCIA** no painel. Diga: "é a contingência funcionando". Ou use o atalho **Robô Selic (offline)**. |
| O painel não abriu | Atalho **Resultados do Robô Selic** → `output\painel_selic.html` (abre em qualquer navegador, sem internet). Se nada abrir, o slide 09 mostra o painel. |
| Windows diz "O Windows protegeu o computador" | **Mais informações → Executar assim mesmo** (o instalador não é assinado). |
| Instalador avisa que não criou os atalhos | O robô foi instalado mesmo assim: abra o `RoboSelic.exe` no caminho que o aviso mostra (política da máquina bloqueou o PowerShell). |
| Antivírus bloqueou o instalador | Use `RoboSelic_portatil.zip` (extrair e rodar `RoboSelic.exe`) ou `codigo\executar_offline.bat` (precisa de Python). |
| A janela preta demora para mostrar algo | Na primeira execução o Windows verifica os arquivos; leva de 10 a 30 segundos. |
| Digitou uma data errada no "escolher período" | O robô pergunta de novo; datas invertidas aparecem como "Não foi possível rodar: Período inválido". |
| Precisa mostrar o log | `Documentos\Oficina de Robos BMA\logs\oficina.log`. |
