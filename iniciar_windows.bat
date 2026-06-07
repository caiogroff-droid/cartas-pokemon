@echo off

if not exist .venv (
    echo Primeira execucao...
    python -m venv .venv

    call .venv\Scripts\activate

    pip install --upgrade pip
    pip install -r requirements.txt

    playwright install
) else (
    call .venv\Scripts\activate
)

uvicorn components.main:app --host 0.0.0.0 --port 8000