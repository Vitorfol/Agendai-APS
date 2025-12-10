#!/usr/bin/env python3
"""
Script para criar o curso de Computação com email computacao@uece.br
"""
import sys
sys.path.append('/app/src')

from sqlalchemy.orm import Session
from database.connection import get_db
from models.models import Curso, Universidade

def criar_curso_computacao():
    db = next(get_db())
    
    try:
        # Buscar UECE
        uece = db.query(Universidade).filter(Universidade.email == "contato@uece.br").first()
        if not uece:
            print("❌ UECE não encontrada!")
            return
        
        # Verificar se curso já existe
        curso_existente = db.query(Curso).filter(Curso.email == "computacao@uece.br").first()
        if curso_existente:
            print(f"✅ Curso já existe: {curso_existente.nome} (ID: {curso_existente.id})")
            return
        
        # Criar curso
        curso = Curso(
            nome="Ciência da Computação",
            sigla="CC",
            email="computacao@uece.br",
            id_universidade=uece.id,
            graduacao=True
        )
        db.add(curso)
        db.commit()
        db.refresh(curso)
        
        print(f"✅ Curso criado com sucesso!")
        print(f"   Nome: {curso.nome}")
        print(f"   Email: {curso.email}")
        print(f"   ID: {curso.id}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao criar curso: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    criar_curso_computacao()
