# Oficina de Robôs - BMA FIDC

## O que o robô faz
- consulta a Selic na API pública do Banco Central;
- usa dados de exemplo se a API estiver indisponível;
- gera Excel, gráfico PNG, PDF e log;
- abre o PDF automaticamente.

## Como executar
1. Instale Python 3.11 ou superior.
2. Abra a pasta `codigo`.
3. Execute `executar_oficina.bat`.

Para apresentar sem depender da internet, execute `executar_offline.bat`.

## Saídas
- `output/selic.xlsx`
- `output/selic.png`
- `output/resumo_selic.pdf`
- `logs/oficina.log`

## QR Code
O QR incluído usa uma URL de exemplo. Crie o repositório no GitHub, altere `GITHUB_URL` em `qr-code/gerar_qrcode.py` e gere o QR definitivo.
