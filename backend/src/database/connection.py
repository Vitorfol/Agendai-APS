import sqlalchemy as db
from sqlalchemy.orm import sessionmaker
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)
from src.models.models import Base
from dotenv import load_dotenv

load_dotenv()

user = os.getenv("DATABASE_USER")
senha = os.getenv("DATABASE_PASSWORD")
host = os.getenv("DATABASE_HOST")
port = os.getenv("DATABASE_PORT")
database = os.getenv("DATABASE_NAME")

connect_string = f"mysql+pymysql://{user}:{senha}@{host}:{port}/{database}"
engine = db.create_engine(connect_string, echo=True)
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
