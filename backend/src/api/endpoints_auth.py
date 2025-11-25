from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from ..database.connection import get_db 
from ..services import service_auth 
from ..schemas import schema # Importa o schema.py modificado
from ..core.config import settings

router = APIRouter(prefix=f"{settings.API_V1_STR.rstrip('/')}/auth", tags=["Autenticação"])

@router.post("/register/professor", 
             response_model=schema.UsuarioResponse, 
             status_code=status.HTTP_201_CREATED,
             summary="Registrar novo Professor")
def registrar_professor(
    dados: schema.RegistroProfessor, 
    db: Session = Depends(get_db)
):
    """
    Registra um novo professor.
    
    - **Requer**: idUniversidade, dataAdmissao, titulacao.
    - **Valida**: Se o email/cpf já existem.
    """
    try:
        usuario = service_auth.registrar_professor(db=db, dados=dados)
        return usuario
        
    except HTTPException as e:
        raise e
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao registrar professor: {str(e)}"
        )
    
@router.post("/register/aluno", 
             response_model=schema.UsuarioResponse, 
             status_code=status.HTTP_201_CREATED,
             summary="Registrar novo Aluno")
def registrar_aluno(
    dados: schema.RegistroAluno, 
    db: Session = Depends(get_db)
):
    """
    Registra um novo aluno.
    
    - **Requer**: idCurso, matricula.
    - **Valida**: Se email/cpf ou matrícula já existem.
    """
    try:
        usuario = service_auth.registrar_aluno(db=db, dados=dados)
        return usuario
        
    except HTTPException as e:
        raise e
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao registrar aluno: {str(e)}"
        )    