from pathlib import Path
import qrcode

GITHUB_URL = "https://github.com/thaiza-commits/oficina-de-robos-bma"
saida = Path(__file__).with_name("QRCode_GitHub.png")

# Correção de erro "Q" (25%): lê bem mesmo projetado numa tela a distância.
qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q, box_size=16, border=4)
qr.add_data(GITHUB_URL)
qr.make(fit=True)
qr.make_image(fill_color="#0B1D3A", back_color="white").save(saida)
print(f"QR Code gerado em: {saida}")
