#!/bin/bash

python3 -m venv .venv

source .venv/bin/activate

pip install -U pip

pip install -r requirements.txt

playwright install chrome

apt install uvicorn -y

echo "Instalação concluída!"