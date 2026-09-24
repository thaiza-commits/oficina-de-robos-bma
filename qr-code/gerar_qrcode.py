from pathlib import Path
import qrcode

GITHUB_URL = "https://github.com/SEU-USUARIO/oficina-de-robos-bma"
saida = Path(__file__).with_name("QRCode_GitHub.png")

qr = qrcode.QRCode(version=4, box_size=12, border=4)
qr.add_data(GITHUB_URL)
qr.make(fit=True)
qr.make_image(fill_color="#0B1D3A", back_color="white").save(saida)
print(f"QR Code gerado em: {saida}")
