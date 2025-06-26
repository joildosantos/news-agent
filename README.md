# Agente de Notícias

Sistema automatizado de curadoria de notícias com interface web para configuração.

## Funcionalidades

- ✅ Busca automatizada de notícias via NewsAPI
- ✅ Interface web completa para configuração
- ✅ Sistema de login e autenticação
- ✅ Gerenciamento de tópicos, fontes e destinatários
- ✅ Envio automatizado via WhatsApp e email
- ✅ Agendamento diário configurável
- ✅ Curadoria inteligente de notícias

## Tecnologias

- **Backend:** Flask + SQLAlchemy
- **Frontend:** React + Vite
- **Banco de dados:** SQLite (desenvolvimento) / PostgreSQL (produção)
- **Deploy:** Render.com

## Configuração

### Variáveis de ambiente necessárias:

- `SECRET_KEY`: Chave secreta do Flask
- `DATABASE_URL`: URL do banco de dados (opcional, usa SQLite se não definida)

### Credenciais padrão:

- **Usuário:** admin
- **Senha:** admin123

## Deploy no Render

1. Conecte este repositório ao Render
2. Configure como Web Service
3. Use as configurações do arquivo `render.yaml`

## Desenvolvimento local

```bash
# Backend
cd src
python main.py

# Frontend (em outro terminal)
cd ../news-agent-frontend
pnpm run dev
```

