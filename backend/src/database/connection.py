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
# Do not open a DB connection at import time. Create the engine with pool_pre_ping
# so connections are checked/renewed when used. SessionLocal will create sessions
# on demand.
engine = db.create_engine(connect_string, echo=True, pool_pre_ping=True)
Session = sessionmaker(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
