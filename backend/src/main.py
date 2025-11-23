from fastapi import FastAPI
from . import models # Garante que os models SQLAlchemy sejam carregados
from .database.connection import engine # Se você usa um engine global
from .api import endpoints_auth # Importa o seu router de autenticação

# 1. Inicializa a aplicação FastAPI
app = FastAPI(
    title="Agendai API",
    description="API para gerenciamento de eventos e usuários.",
    version="1.0.0"
)

# 2. Configuração do Banco de Dados (Opcional, mas útil para o dev)
# Descomente a linha abaixo se quiser que as tabelas sejam criadas automaticamente
# na primeira inicialização (apenas se não estiver usando Alembic para migrações).
# models.Base.metadata.create_all(bind=engine) 

# 3. Inclui as rotas de autenticação
# O módulo endpoints_auth deve ser acessível via importação relativa.
app.include_router(endpoints_auth.router)

# 4. Rota de Saúde (Health Check)
@app.get("/")
def read_root():
    return {"message": "API Agendai está rodando com FastAPI!"}

# Se o seu Docker está chamando 'src.main:app', este arquivo deve estar em 'src/main.py'.
# Se o arquivo estiver em 'backend/main.py', verifique se o caminho no docker-compose está correto.