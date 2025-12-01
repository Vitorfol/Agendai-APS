from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from ..core.config import settings
from ..database.connection import get_db
from typing import List    
from ..services import service_courses
from ..schemas import schema

router = APIRouter(prefix=f"{settings.API_V1_STR.rstrip('/')}/courses")

@router.get("/", response_model=List[schema.CursoResponse])
def listar_cursos(
    graduacao: bool | None = None,
    id_universidade: int | None = None,
    db: Session = Depends(get_db)
):
    try:
        cursos = service_courses.listar_cursos(db, graduacao, id_universidade)
        return cursos
    except Exception as e:
        raise HTTPException(500, f"Erro interno ao buscar cursos: {e}")