@echo off
chcp 65001 >nul
rem Robô Selic - Oficina de Robôs BMA (pergunta o período na tela)
pushd "%~dp0"
python --version >nul 2>nul
if errorlevel 1 (
    echo Python nao encontrado. Instale o Python 3.11+ em https://www.python.org/downloads/
    echo marcando "Add python.exe to PATH" - ou use o instalador Instalador_OficinaRobos_BMA.exe.
    pause
    exit /b 1
)
python -c "import requests, pandas, matplotlib, xlsxwriter, reportlab, truststore" >nul 2>nul
if errorlevel 1 (
    echo Instalando bibliotecas - somente na primeira vez...
    python -m pip install --disable-pip-version-check -r requirements.txt
)
python main.py --perguntar
popd
pause
