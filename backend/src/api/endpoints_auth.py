from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from ..core.config import settings
from ..database.connection import get_db 
from ..services import service_auth 
from ..schemas import schema # Importa o schema.py modificado

router = APIRouter(prefix=f"{settings.API_V1_STR.rstrip('/')}/auth", tags=["Autenticação"])

@router.post("/register", 
             response_model=schema.UsuarioResponse, 
             status_code=status.HTTP_201_CREATED)
def registrar_usuario(
    dados: schema.UsuarioRegistro,
    db: Session = Depends(get_db)
):
    try:
        usuario = service_auth.registrar_usuario_automatico(db=db, dados=dados)
        return usuario
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )