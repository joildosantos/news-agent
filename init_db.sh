#!/bin/bash

cd /home/ubuntu/news-agent/src

# Remove o banco de dados existente, se houver
rm -f database/app.db

# Cria o diretório do banco de dados se não existir
mkdir -p database

# Executa o script principal para criar as tabelas
python -c "from main import app, db; with app.app_context(): db.create_all()"

echo "Banco de dados inicializado com sucesso."


