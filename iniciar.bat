@echo off
cd /d "%~dp0"
if not exist venv (
    echo Creando entorno virtual...
    python -m venv venv
    venv\Scripts\pip install -r requirements.txt
)
echo.
echo Abriendo http://localhost:5001
start http://localhost:5001
venv\Scripts\python app.py
pause
