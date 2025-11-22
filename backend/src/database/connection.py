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
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



