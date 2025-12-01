from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..models import models

def listar_cursos(db: Session, graduacao: bool | None, id_universidade: int | None):
    query = db.query(models.Curso)

    if graduacao is not None:
        query = query.filter(models.Curso.graduacao == graduacao)

    if id_universidade is not None:
        query = query.filter(models.Curso.id_universidade == id_universidade)

    return query.all()