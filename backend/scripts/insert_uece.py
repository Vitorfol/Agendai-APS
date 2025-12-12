"""Pequeno utilitário para inserir um registro de Universidade (UECE) no banco.

Uso: python src/models/insert_uece.py
Este script assume que a aplicação consegue criar uma sessão via
`src.database.connection.SessionLocal` (mesma configuração usada pelo app).
O arquivo segue o mesmo padrão do `src/database/popule.py` mas insere apenas
uma Universidade.
"""
import sys
import os
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

from src.models.models import Universidade
from src.database.connection import SessionLocal
from src.core.security import pegar_senha_hash


def insert_uece():
    """Insere um registro de Universidade chamado UECE se não existir."""
    db = SessionLocal()
    # ---- Edit these params as needed ----
    UECE_PARAMS = {
        "nome": "Universidade Estadual do Ceará",
        "sigla": "UECE",
        "cnpj": "12345678000195",
        "email": "contato@uece.br",
        # plain password here will be hashed before saving
        "senha": "dedelbrabo",
    }

    try:
        # Verifica duplicidade por email ou cnpj
        existing = db.query(Universidade).filter(
            (Universidade.email == UECE_PARAMS["email"]) | (Universidade.cnpj == UECE_PARAMS["cnpj"])
        ).first()
        if existing:
            print(f"Universidade já existe (id={existing.id}, email={existing.email}). Nada a fazer.")
            return existing

        senha_hash = pegar_senha_hash(UECE_PARAMS["senha"])

        uni = Universidade(
            nome=UECE_PARAMS["nome"],
            sigla=UECE_PARAMS["sigla"],
            cnpj=UECE_PARAMS["cnpj"],
            email=UECE_PARAMS["email"],
            senha=senha_hash
        )
        db.add(uni)
        db.commit()
        db.refresh(uni)
        print(f"Universidade criada: id={uni.id}, nome={uni.nome}, email={uni.email}")
        return uni
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    insert_uece()
