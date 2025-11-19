import sqlalchemy as db
from sqlalchemy.orm import sessionmaker
from ..models.models import Base

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
def create_tables():
    Base.metadata.create_all(bind=engine)

# 5. Criar uma função utilitária para obter a sessão (boa prática em Flask/FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

create_tables()