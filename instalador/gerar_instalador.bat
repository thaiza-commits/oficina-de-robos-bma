@echo off
chcp 65001 >nul
rem Gera instalador\dist\Instalador_OficinaRobos_BMA.exe (precisa de Python 3.11+ e internet so no build)
pushd "%~dp0"
set VENV=%TEMP%\orbma_venv
if not exist "%VENV%\Scripts\python.exe" (
    echo Criando ambiente de build em %VENV% ...
    python -m venv "%VENV%" || goto erro
)
"%VENV%\Scripts\python" -m pip install --disable-pip-version-check -q -r ..\codigo\requirements.txt pyinstaller pillow || goto erro
"%VENV%\Scripts\python" build.py || goto erro
echo.
echo Pronto: %~dp0dist\Instalador_OficinaRobos_BMA.exe
popd
pause
exit /b 0
:erro
echo.
echo O build falhou - veja as mensagens acima.
popd
pause
exit /b 1
