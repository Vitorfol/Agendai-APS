import sqlalchemy as db
from sqlalchemy.orm import sessionmaker
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)
from src.models.models import Base


user = "root"
senha = "admin123"
connect_string = f"mysql+mysqlconnector://{user}:{senha}@localhost:3307/agendai"
engine = db.create_engine(connect_string, echo = True)
conn = engine.connect()
Session = sessionmaker(bind=engine)
session = Session()

metadata = Base.metadata

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Criar as tabelas no DB (se ainda não existirem)
class Conn():
    def create_tables(self):
        Base.metadata.create_all(bind=engine)

# 5. Criar uma função utilitária para obter a sessão (boa prática em Flask/FastAPI)
    def get_db(self):
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
