@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creando entorno virtual...
    py -3 -m venv .venv
)

echo Instalando dependencias si hace falta...
".venv\Scripts\python.exe" -m pip install -r requirements.txt

echo Abriendo catalogo local...
start "" powershell -NoProfile -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:5000'"

echo Servidor iniciado. Cerra esta ventana para apagar la web.
".venv\Scripts\python.exe" run.py
