#!/usr/bin/env python3
"""
Script para criar os cursos da UECE para a apresentação.

Cursos criados:
- Ciência da Computação (Graduação e Pós-Graduação)
- Matemática (Graduação)
- Química (Pós-Graduação)
- Física (Graduação e Pós-Graduação)

Uso: python scripts/insert_uece_courses.py
"""
import sys
import os
import logging

# Silenciar logs do SQLAlchemy
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

from src.models.models import Curso, Universidade
from src.database.connection import SessionLocal


# Definição dos cursos para a apresentação
COURSES = [
    {
        "nome": "Ciência da Computação",
        "sigla": "CC",
        "email": "computacao@uece.br",
        "graduacao": True
    },
    {
        "nome": "Ciência da Computação - Pós-Graduação",
        "sigla": "CC-POS",
        "email": "computacao.pos@uece.br",
        "graduacao": False
    },
    {
        "nome": "Matemática",
        "sigla": "MAT",
        "email": "matematica@uece.br",
        "graduacao": True
    },
    {
        "nome": "Química - Pós-Graduação",
        "sigla": "QUIM-POS",
        "email": "quimica.pos@uece.br",
        "graduacao": False
    },
    {
        "nome": "Física",
        "sigla": "FIS",
        "email": "fisica@uece.br",
        "graduacao": True
    },
    {
        "nome": "Física - Pós-Graduação",
        "sigla": "FIS-POS",
        "email": "fisica.pos@uece.br",
        "graduacao": False
    },
]


def insert_uece_courses():
    """Insere os cursos da UECE para a apresentação."""
    db = SessionLocal()
    
    try:
        # Buscar UECE
        uece = db.query(Universidade).filter(
            Universidade.email == "contato@uece.br"
        ).first()
        
        if not uece:
            return False
        
        for course_data in COURSES:
            # Verificar se curso já existe
            curso_existente = db.query(Curso).filter(
                Curso.email == course_data["email"]
            ).first()
            
            if curso_existente:
                continue
            
            # Criar curso
            curso = Curso(
                nome=course_data["nome"],
                sigla=course_data["sigla"],
                email=course_data["email"],
                id_universidade=uece.id,
                graduacao=course_data["graduacao"]
            )
            db.add(curso)
            db.commit()
            db.refresh(curso)
        
        return True
        
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = insert_uece_courses()
    sys.exit(0 if success else 1)
