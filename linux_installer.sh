#!/bin/bash

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "Primeira execução..."
    python3 -m venv .venv

    source .venv/bin/activate

    pip install --upgrade pip
    pip install -r requirements.txt

    playwright install chrome
else
    source .venv/bin/activate
fi

cd components

echo "Instalação concluída! Iniciando servidor..."
echo "Acesse http://127.0.0.1:8000"

python -m uvicorn main:app --reload
