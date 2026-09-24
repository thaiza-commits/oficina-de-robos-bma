"""Instalador da Oficina de Robôs BMA (Robô Selic).

Instala para o usuário atual, sem precisar de Python nem de administrador:
  - programa em %LOCALAPPDATA%\\Programs\\OficinaRobosBMA
  - resultados, prompt e apostila em Documentos\\Oficina de Robos BMA
  - atalhos na Área de Trabalho e no Menu Iniciar
  - entrada em "Aplicativos instalados" para desinstalar

Uso: Instalador_OficinaRobos_BMA.exe            (janela)
     Instalador_OficinaRobos_BMA.exe --silencioso (sem janela; usado nos testes)
"""
from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys
import threading
import zipfile
from pathlib import Path

VERSAO = "1.0.0"
NOME = "Oficina de Robôs BMA"
APP_ID = "OficinaRobosBMA"
NAVY = "#0B1D3A"
ORANGE = "#F28C2B"

RECURSOS = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
PAYLOAD = RECURSOS / "payload.zip"
EXTRAS = RECURSOS / "extras"  # prompt, apostila, leia-me -> Documentos

SEM_JANELA = 0x08000000  # CREATE_NO_WINDOW


def pasta_especial(csidl: int) -> Path:
    buffer = ctypes.create_unicode_buffer(260)
    if ctypes.windll.shell32.SHGetFolderPathW(None, csidl, None, 0, buffer) != 0:
        raise OSError(f"Pasta do Windows não encontrada (CSIDL {csidl}).")
    return Path(buffer.value)


APP_DIR = Path(os.environ["LOCALAPPDATA"]) / "Programs" / APP_ID
DOCS_DIR = pasta_especial(5) / "Oficina de Robos BMA"            # Documentos
DESKTOP_DIR = pasta_especial(16)                                   # Área de Trabalho
MENU_DIR = pasta_especial(2) / NOME                                # Menu Iniciar > Programas
EXE = APP_DIR / "RoboSelic.exe"
UNINSTALL_KEY = rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_ID}"


def ps_str(texto: str | Path) -> str:
    return "'" + str(texto).replace("'", "''") + "'"


def criar_atalhos(na_area_de_trabalho: bool) -> list[Path]:
    atalhos = [
        (MENU_DIR / "Robô Selic.lnk", EXE, "", "Consulta a Selic ao vivo no Banco Central"),
        (MENU_DIR / "Robô Selic (offline).lnk", EXE, "--offline", "Roda sem internet (última consulta salva)"),
        (MENU_DIR / "Resultados do Robô Selic.lnk", DOCS_DIR, "", "Excel, gráfico, PDF, prompt e apostila"),
        (MENU_DIR / "Desinstalar.lnk", APP_DIR / "desinstalar.cmd", "", "Remove a Oficina de Robôs BMA"),
    ]
    if na_area_de_trabalho:
        atalhos += [
            (DESKTOP_DIR / "Robô Selic.lnk", EXE, "", "Consulta a Selic ao vivo no Banco Central"),
            (DESKTOP_DIR / "Robô Selic (offline).lnk", EXE, "--offline", "Roda sem internet (última consulta salva)"),
            (DESKTOP_DIR / "Resultados do Robô Selic.lnk", DOCS_DIR, "", "Excel, gráfico, PDF, prompt e apostila"),
        ]
    MENU_DIR.mkdir(parents=True, exist_ok=True)
    linhas = ["$s = New-Object -ComObject WScript.Shell"]
    for lnk, alvo, argumentos, descricao in atalhos:
        linhas += [
            f"$l = $s.CreateShortcut({ps_str(lnk)})",
            f"$l.TargetPath = {ps_str(alvo)}",
            f"$l.Arguments = {ps_str(argumentos)}",
            f"$l.WorkingDirectory = {ps_str(APP_DIR)}",
            f"$l.Description = {ps_str(descricao)}",
            f"$l.IconLocation = {ps_str(str(EXE) + ',0')}",
            "$l.Save()",
        ]
    script = APP_DIR / "criar_atalhos.ps1"
    script.write_text("\r\n".join(linhas), encoding="utf-8-sig")
    resultado = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
        capture_output=True, text=True, creationflags=SEM_JANELA,
    )
    script.unlink(missing_ok=True)
    faltando = [lnk for lnk, *_ in atalhos if not lnk.exists()]
    if resultado.returncode != 0 or faltando:
        raise OSError(f"Atalhos não criados: {resultado.stderr.strip() or faltando}")
    return [lnk for lnk, *_ in atalhos]


def escrever_desinstalador(atalhos: list[Path]) -> None:
    remover = "\r\n".join(f"Remove-Item -LiteralPath {ps_str(a)} -Force -ErrorAction SilentlyContinue" for a in atalhos)
    ps1 = f"""$ErrorActionPreference = 'Continue'
{remover}
Remove-Item -LiteralPath {ps_str(MENU_DIR)} -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path 'HKCU:\\{UNINSTALL_KEY}' -Recurse -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1
Remove-Item -LiteralPath {ps_str(APP_DIR)} -Recurse -Force -ErrorAction SilentlyContinue
Write-Host 'Oficina de Robos BMA removida. Seus resultados continuam em: {str(DOCS_DIR).replace("'", "''")}'
"""
    (APP_DIR / "desinstalar.ps1").write_text(ps1, encoding="utf-8-sig")
    # Tudo numa linha terminada em "exit": o .cmd é apagado junto com a pasta,
    # e o cmd não pode tentar ler a linha seguinte de um arquivo que sumiu.
    temp = "%TEMP%\\desinstalar_oficina_bma.ps1"
    cmd = (
        "@echo off\r\n"
        f'copy /y "%~dp0desinstalar.ps1" "{temp}" >nul & cd /d "%TEMP%" & '
        f'powershell -NoProfile -ExecutionPolicy Bypass -File "{temp}" & del "{temp}" >nul 2>nul & pause & exit\r\n'
    )
    (APP_DIR / "desinstalar.cmd").write_text(cmd, encoding="ascii")


def registrar_desinstalacao() -> None:
    import winreg

    tamanho_kb = sum(f.stat().st_size for f in APP_DIR.rglob("*") if f.is_file()) // 1024
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as chave:
        valores = {
            "DisplayName": NOME,
            "DisplayVersion": VERSAO,
            "Publisher": "BMA FIDC - Oficina de Robôs",
            "DisplayIcon": str(EXE),
            "InstallLocation": str(APP_DIR),
            "UninstallString": f'"{APP_DIR / "desinstalar.cmd"}"',
        }
        for nome, valor in valores.items():
            winreg.SetValueEx(chave, nome, 0, winreg.REG_SZ, valor)
        winreg.SetValueEx(chave, "EstimatedSize", 0, winreg.REG_DWORD, tamanho_kb)
        winreg.SetValueEx(chave, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(chave, "NoRepair", 0, winreg.REG_DWORD, 1)


def instalar(na_area_de_trabalho: bool = True, progresso=lambda texto, pct: None) -> list[str]:
    """Instala e devolve avisos de etapas opcionais que falharam (atalhos, registro)."""
    progresso("Removendo versão anterior...", 5)
    if APP_DIR.exists():
        try:
            shutil.rmtree(APP_DIR)
        except PermissionError as erro:
            raise PermissionError(
                "O Robô Selic parece estar aberto. Feche a janela do robô e tente de novo."
            ) from erro
    APP_DIR.mkdir(parents=True)

    with zipfile.ZipFile(PAYLOAD) as pacote:
        arquivos = pacote.infolist()
        for i, item in enumerate(arquivos, start=1):
            pacote.extract(item, APP_DIR)
            if i % 25 == 0 or i == len(arquivos):
                progresso("Copiando o Robô Selic...", 5 + int(75 * i / len(arquivos)))
    if not EXE.exists():
        raise FileNotFoundError(f"Instalação incompleta: {EXE} não foi copiado.")

    progresso("Copiando prompt e apostila para Documentos...", 82)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    if EXTRAS.exists():
        for arquivo in EXTRAS.iterdir():
            shutil.copy2(arquivo, DOCS_DIR / arquivo.name)

    # Atalhos e registro são opcionais: se a política da máquina bloquear o
    # PowerShell ou o registro, o robô continua instalado e utilizável.
    avisos: list[str] = []
    progresso("Criando atalhos (pode levar até 1 minuto)...", 90)
    try:
        atalhos = criar_atalhos(na_area_de_trabalho)
    except Exception as erro:  # noqa: BLE001
        atalhos = []
        avisos.append(f"Os atalhos não puderam ser criados ({erro}).\n"
                      f"Abra o robô direto por: {EXE}\n(offline: acrescente --offline)")
    escrever_desinstalador(atalhos)
    try:
        registrar_desinstalacao()
    except OSError as erro:
        avisos.append(f"Não foi possível registrar em Aplicativos instalados ({erro}).\n"
                      f"Para desinstalar, use {APP_DIR / 'desinstalar.cmd'}")
    progresso("Instalação concluída!" if not avisos else "Instalação concluída, com avisos.", 100)
    return avisos


def abrir_robo() -> None:
    # O instalador também é um .exe PyInstaller: sem limpar o ambiente, o robô
    # herdaria as variáveis internas dele e fecharia antes de começar.
    ambiente = {k: v for k, v in os.environ.items() if not k.startswith(("_PYI", "_MEI", "TCL_", "TK_"))}
    ambiente["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    subprocess.Popen([str(EXE)], cwd=str(APP_DIR), env=ambiente, creationflags=subprocess.CREATE_NEW_CONSOLE)


def modo_silencioso() -> int:
    try:
        avisos = instalar(na_area_de_trabalho="--sem-atalho-desktop" not in sys.argv,
                          progresso=lambda texto, pct: print(f"[{pct:3d}%] {texto}"))
    except Exception as erro:  # noqa: BLE001
        print(f"ERRO: {erro}")
        return 1
    for aviso in avisos:
        print(f"AVISO: {aviso}")
    print(f"Instalado em {APP_DIR}")
    return 0


def modo_janela() -> int:
    import tkinter as tk
    from tkinter import messagebox, ttk

    janela = tk.Tk()
    janela.title(f"Instalador - {NOME}")
    janela.geometry("560x400")
    janela.resizable(False, False)
    janela.configure(bg="white")
    try:
        janela.iconbitmap(str(RECURSOS / "robo.ico"))
    except tk.TclError:
        pass

    topo = tk.Frame(janela, bg=NAVY, height=110)
    topo.pack(fill="x")
    tk.Label(topo, text="OFICINA DE ROBÔS", bg=NAVY, fg="white",
             font=("Segoe UI", 22, "bold")).place(x=28, y=18)
    tk.Label(topo, text="Automatize tarefas. Ganhe tempo. Gere valor.", bg=NAVY, fg=ORANGE,
             font=("Segoe UI", 11, "bold")).place(x=30, y=66)

    corpo = tk.Frame(janela, bg="white")
    corpo.pack(fill="both", expand=True, padx=28, pady=16)
    tk.Label(corpo, justify="left", anchor="w", bg="white", fg=NAVY, font=("Segoe UI", 10),
             text=(f"Este assistente instala o Robô Selic v{VERSAO}.\n"
                   "Não precisa de Python nem de permissão de administrador.\n\n"
                   f"Programa:   {APP_DIR}\n"
                   f"Resultados: {DOCS_DIR}")).pack(anchor="w")
    var_desktop = tk.BooleanVar(value=True)
    tk.Checkbutton(corpo, text="Criar atalhos na Área de Trabalho", variable=var_desktop,
                   bg="white", fg=NAVY, activebackground="white",
                   font=("Segoe UI", 10)).pack(anchor="w", pady=(12, 4))
    estilo = ttk.Style()
    estilo.theme_use("clam")
    estilo.configure("bma.Horizontal.TProgressbar", troughcolor="#E6EAF0", background=ORANGE)
    barra = ttk.Progressbar(corpo, length=500, maximum=100, style="bma.Horizontal.TProgressbar")
    barra.pack(anchor="w", pady=(8, 2))
    status = tk.Label(corpo, text="Pronto para instalar.", bg="white", fg="#555", font=("Segoe UI", 9))
    status.pack(anchor="w")

    botoes = tk.Frame(janela, bg="white")
    botoes.pack(fill="x", padx=28, pady=(0, 18))
    estilo_botao = {"font": ("Segoe UI", 10, "bold"), "relief": "flat", "padx": 18, "pady": 6, "cursor": "hand2"}
    btn_instalar = tk.Button(botoes, text="Instalar", bg=ORANGE, fg="white", activebackground=NAVY,
                             activeforeground="white", **estilo_botao)
    btn_fechar = tk.Button(botoes, text="Cancelar", bg="#E6EAF0", fg=NAVY, command=janela.destroy, **estilo_botao)
    btn_fechar.pack(side="right")
    btn_instalar.pack(side="right", padx=(0, 10))

    def atualizar(texto: str, pct: int) -> None:
        janela.after(0, lambda: (status.config(text=texto), barra.config(value=pct)))

    def concluir(erro: Exception | None, avisos: list[str] | None = None) -> None:
        if erro:
            status.config(text="A instalação não foi concluída.", fg="#B00020")
            btn_instalar.config(state="normal", text="Tentar de novo")
            btn_fechar.config(state="normal")
            messagebox.showerror(NOME, str(erro))
            return
        btn_fechar.config(state="normal", text="Fechar")
        btn_instalar.config(state="normal", text="Abrir o Robô Selic",
                            command=lambda: (abrir_robo(), janela.destroy()))
        if avisos and not os.environ.get("OFICINA_AUTOTESTE"):
            messagebox.showwarning(NOME, "O Robô Selic foi instalado.\n\n" + "\n\n".join(avisos))

    def trabalho() -> None:
        try:
            avisos = instalar(var_desktop.get(), atualizar)
        except Exception as erro:  # noqa: BLE001 - mostrar qualquer falha para quem instala
            janela.after(0, concluir, erro)
        else:
            janela.after(0, concluir, None, avisos)

    def iniciar() -> None:
        btn_instalar.config(state="disabled")
        btn_fechar.config(state="disabled")
        threading.Thread(target=trabalho, daemon=True).start()

    btn_instalar.config(command=iniciar)
    # ENTER aciona o botão principal (Instalar e, ao final, Abrir o Robô Selic).
    janela.bind("<Return>", lambda _evento: btn_instalar.invoke())
    btn_instalar.focus_set()

    if os.environ.get("OFICINA_AUTOTESTE"):
        # Teste automático da janela: aperta os mesmos botões que a pessoa aperta.
        registro = Path(os.environ["OFICINA_AUTOTESTE"])

        def anotar(texto: str) -> None:
            with registro.open("a", encoding="utf-8") as f:
                f.write(texto + "\n")

        def esperar_fim() -> None:
            if str(btn_instalar.cget("state")) == "disabled":
                janela.after(500, esperar_fim)
                return
            anotar(f"fim: botao={btn_instalar.cget('text')} status={status.cget('text')}")
            if btn_instalar.cget("text") == "Abrir o Robô Selic":
                btn_instalar.invoke()
                anotar("clicou: Abrir o Robô Selic")

        def comecar() -> None:
            anotar("clicou: Instalar")
            btn_instalar.invoke()
            janela.after(500, esperar_fim)

        janela.after(1500, comecar)
    janela.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(modo_silencioso() if "--silencioso" in sys.argv else modo_janela())
