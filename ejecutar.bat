@echo off
cd /d "%~dp0"
if not exist .venv (
    echo Creando entorno virtual...
    python -m venv .venv
    .venv\Scripts\python.exe -m pip install --upgrade pip
    .venv\Scripts\python.exe -m pip install -r requirements.txt
)
echo Iniciando dashboard en http://127.0.0.1:8050 ...
start "" http://127.0.0.1:8050
.venv\Scripts\python.exe app.py
pause
