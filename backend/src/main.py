import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)
from src.models.models import Base
from src.database.connection import engine # Se você usa um engine global
from src.api import endpoints_auth # Importa o seu router de autenticação
from src.api import endpoints_events
from src.api import endpoints_users

# 1. Inicializa a aplicação FastAPI
app = FastAPI(
    title="Agendai API",
    description="API para gerenciamento de eventos e usuários.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"]
)
# 2. Configuração do Banco de Dados (Opcional, mas útil para o dev)
# Descomente a linha abaixo se quiser que as tabelas sejam criadas automaticamente
# na primeira inicialização (apenas se não estiver usando Alembic para migrações).
# models.Base.metadata.create_all(bind=engine) 

# 3. Inclui as rotas de autenticação
# O módulo endpoints_auth deve ser acessível via importação relativa.
app.include_router(endpoints_auth.router)
app.include_router(endpoints_events.router)
app.include_router(endpoints_users.router)

# 4. Rota de Saúde (Health Check)
@app.get("/")
def read_root():
    return {"message": "API Agendai está rodando com FastAPI!"}

# Se o seu Docker está chamando 'src.main:app', este arquivo deve estar em 'src/main.py'.
# Se o arquivo estiver em 'backend/main.py', verifique se o caminho no docker-compose está correto.