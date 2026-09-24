"""Gera instalador/dist/Instalador_OficinaRobos_BMA.exe.

Rode pelo gerar_instalador.bat (cria o ambiente e chama este script).
O build acontece numa pasta temporária local: PyInstaller em pasta de rede é
lento e o Windows sem "caminhos longos" quebra a instalação de bibliotecas.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

VERSAO = "1.1.0"
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
TRABALHO = Path(tempfile.gettempdir()) / "orbma_build"
SAIDA = AQUI / "dist"
NAVY, ORANGE, BLUE = (11, 29, 58), (242, 140, 43), (43, 76, 230)


def rodar(*args: str) -> None:
    print(">", " ".join(args))
    subprocess.run(args, check=True, cwd=TRABALHO)


def gerar_icone(destino: Path) -> None:
    """Ícone do robô nas cores da BMA (sem depender de arquivo externo)."""
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((8, 8, 248, 248), 56, fill=NAVY)
    d.line((128, 30, 128, 62), fill=ORANGE, width=10)
    d.ellipse((114, 18, 142, 46), fill=ORANGE)
    d.rounded_rectangle((52, 62, 204, 190), 30, fill="white")
    d.ellipse((80, 100, 116, 136), fill=BLUE)
    d.ellipse((140, 100, 176, 136), fill=BLUE)
    d.rounded_rectangle((92, 152, 164, 166), 7, fill=ORANGE)
    d.rounded_rectangle((34, 104, 52, 150), 8, fill=ORANGE)
    d.rounded_rectangle((204, 104, 222, 150), 8, fill=ORANGE)
    d.rounded_rectangle((84, 198, 172, 226), 12, fill=BLUE)
    img.save(destino, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


def arquivo_versao(destino: Path, descricao: str, nome_original: str) -> None:
    v = tuple(int(x) for x in VERSAO.split(".")) + (0,)
    destino.write_text(f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={v}, prodvers={v}, mask=0x3f, flags=0x0, OS=0x40004,
                    fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('041604B0', [
      StringStruct('CompanyName', 'BMA FIDC - Oficina de Robos'),
      StringStruct('FileDescription', '{descricao}'),
      StringStruct('FileVersion', '{VERSAO}'),
      StringStruct('ProductName', 'Oficina de Robos BMA'),
      StringStruct('ProductVersion', '{VERSAO}'),
      StringStruct('OriginalFilename', '{nome_original}')])]),
    VarFileInfo([VarStruct('Translation', [0x0416, 1200])])])
""", encoding="utf-8")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    shutil.rmtree(TRABALHO, ignore_errors=True)
    TRABALHO.mkdir(parents=True)
    icone = TRABALHO / "robo.ico"
    gerar_icone(icone)

    # 1) Robô Selic: executável com Python e bibliotecas embutidos (pasta única).
    shutil.copy2(RAIZ / "codigo" / "main.py", TRABALHO / "main.py")
    shutil.copytree(RAIZ / "dados", TRABALHO / "dados_src")
    arquivo_versao(TRABALHO / "versao_robo.txt", "Robo Selic - Oficina de Robos BMA", "RoboSelic.exe")
    rodar(sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir", "--console",
          "--name", "RoboSelic", "--icon", str(icone), "--version-file", "versao_robo.txt",
          "--add-data", f"{TRABALHO / 'dados_src' / 'exemplo_selic.csv'};dados",
          "--add-data", f"{RAIZ / 'codigo' / 'painel_template.html'};.",
          "--add-data", f"{RAIZ / 'codigo' / 'logo_bma_fidc.svg'};.",
          "--exclude-module", "tkinter", "--collect-data", "certifi",
          "main.py")
    robo_dir = TRABALHO / "dist" / "RoboSelic"

    # Teste de fumaça antes de empacotar: o .exe precisa rodar sozinho.
    teste = subprocess.run([str(robo_dir / "RoboSelic.exe"), "--offline", "--no-open", "--no-pause"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
    if teste.returncode != 0 or "Processo concluído" not in teste.stdout or "Painel:" not in teste.stdout:
        print(teste.stdout, teste.stderr)
        raise SystemExit("RoboSelic.exe falhou no teste offline - instalador NÃO gerado.")
    print("Teste do RoboSelic.exe (offline): OK")

    payload = TRABALHO / "payload.zip"
    with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for arquivo in robo_dir.rglob("*"):
            if arquivo.is_file():
                z.write(arquivo, arquivo.relative_to(robo_dir))

    # 2) Material do participante copiado para Documentos na instalação.
    extras = TRABALHO / "extras"
    extras.mkdir()
    for origem in [RAIZ / "prompt" / "prompt_oficina.txt",
                   RAIZ / "apostila" / "Apostila_Oficina_de_Robos.pdf",
                   RAIZ / "links" / "links_uteis.txt",
                   RAIZ / "parametros.ini",
                   RAIZ / "codigo" / "main.py"]:
        shutil.copy2(origem, extras / origem.name)
    (extras / "main.py").rename(extras / "codigo_robo_selic.py")

    # 3) Instalador: um único .exe com o robô dentro.
    shutil.copy2(AQUI / "instalador.py", TRABALHO / "instalador.py")
    arquivo_versao(TRABALHO / "versao_inst.txt", "Instalador - Oficina de Robos BMA", "Instalador_OficinaRobos_BMA.exe")
    rodar(sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--windowed",
          "--name", "Instalador_OficinaRobos_BMA", "--icon", str(icone), "--version-file", "versao_inst.txt",
          "--add-data", f"{payload};.", "--add-data", f"{extras};extras", "--add-data", f"{icone};.",
          "--distpath", str(TRABALHO / "dist_inst"), "instalador.py")

    SAIDA.mkdir(exist_ok=True)
    final = SAIDA / "Instalador_OficinaRobos_BMA.exe"
    shutil.copy2(TRABALHO / "dist_inst" / "Instalador_OficinaRobos_BMA.exe", final)
    portatil = SAIDA / "RoboSelic_portatil.zip"
    shutil.copy2(payload, portatil)
    print(f"\nInstalador: {final} ({final.stat().st_size / 1e6:.1f} MB)")
    print(f"Portátil:   {portatil} ({portatil.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
