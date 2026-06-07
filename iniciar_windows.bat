@echo off

cd /d "%~dp0"


if not exist .venv (
    echo Primeira execucao...
    python -m venv .venv

if errorlevel 1 (
    echo Erro ao criar ambiente virtual
    pause
    exit /b
)

    call .venv\Scripts\activate

    pip install --upgrade pip
    pip install -r requirements.txt

    playwright install
) else (
    call .venv\Scripts\activate
)
cd /d "%~dp0components"


python -m uvicorn main:app --reload
echo Server running on http://127.0.0.1:8000/
pause
