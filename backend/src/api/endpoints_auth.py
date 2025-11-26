from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from ..core.config import settings
from ..database.connection import get_db 
from ..services import service_auth 
from ..models.models import Usuario, Universidade
from ..schemas.jwt import Token, LoginRequest

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
        
@router.post("/login",
             response_model=Token)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Endpoint de login: valida credenciais e retorna access + refresh tokens.

    Se o email pertence a uma `Universidade`, delega para `login_university` (placeholder).
    Se o email pertencer a um `Usuário`, delega para `login_user` (placeholder)
    """
    
    # Verifica se é uma universidade (login separado)
    
    university = db.query(Universidade).filter(Universidade.email == data.email).first()
    if university:
        # Delegar para o serviço especializado (em service_auth)
        token = service_auth.login_university(university=university, password=data.password)
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas (university)")
        return token

    # Autentica usuário padrão via service
    token = service_auth.login_user(db=db, email=data.email, password=data.password)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Credenciais inválidas",
                            headers={"WWW-Authenticate": "Bearer"})

    return token

