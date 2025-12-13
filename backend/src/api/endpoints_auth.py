from fastapi import APIRouter, Depends, status, HTTPException, Header
from sqlalchemy.orm import Session
from ..core.config import settings
from ..database.connection import get_db 
from ..services import service_auth 
from ..models.models import Usuario, Universidade
from ..schemas.jwt import Token, LoginRequest
from ..schemas.jwt import TokenPayload
from ..core import security
from ..schemas import schema

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
             response_model=Token,
             status_code=status.HTTP_200_OK,
             summary="Realizar login e retornar tokens")
def login(data: LoginRequest, db: Session = Depends(get_db)) -> Token:
    """Endpoint de login: valida credenciais e retorna access + refresh tokens.

    Se o email pertence a uma `Universidade`, delega para `login_university`.
    Se o email pertencer a um `Usuário`, delega para `login_user`.
    """
    
    # Verifica se é uma universidade (login separado)
    university = db.query(Universidade).filter(Universidade.email == data.email).first()
    if university:
        token = service_auth.login_university(university=university, password=data.password)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token

    # Autentica usuário padrão via service
    token = service_auth.login_user(db=db, email=data.email, password=data.password)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Credenciais inválidas",
                            headers={"WWW-Authenticate": "Bearer"})

    return token

@router.post("/refresh",
            response_model=Token,
            status_code=status.HTTP_200_OK,
            summary="Atualizar tokens usando refresh token")
def refresh_token(token: str = Depends(service_auth.oauth2_scheme)) -> Token:
    """Atualiza os tokens de acesso e refresh usando o refresh token válido."""
    
    current_payload = security.decode_token(token)
    
    if not current_payload or getattr(current_payload, "type", None) != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido para refresh",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    email = getattr(current_payload, "sub", None)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: sub ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = security.create_access_token(subject=str(email), tag=getattr(current_payload, "tag", None))
    refresh_token = security.create_refresh_token(subject=str(email), tag=getattr(current_payload, "tag", None))
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


# ============================================================
# ROTAS DE RECUPERAÇÃO DE SENHA
# ============================================================

@router.post("/request-password-reset", 
             status_code=status.HTTP_200_OK, 
             summary="Solicitar recuperação de senha")
def request_password_reset(data: schema.RequestPasswordResetSchema, db: Session = Depends(get_db)):
    """
    Solicita recuperação de senha. Envia um código de 6 dígitos para o email informado.
    
    - **email**: Email cadastrado no sistema
    """
    return service_auth.request_password_reset(db, data.email)

@router.post("/validate-reset-code", 
             status_code=status.HTTP_200_OK, 
             summary="Validar código de recuperação")
def validate_reset_code(data: schema.ValidateResetCodeSchema):
    """
    Valida o código de 6 dígitos enviado por email.
    
    - **code**: Código de 6 dígitos recebido por email
    
    Retorna um token de recuperação que deve ser usado no próximo passo.
    """
    return service_auth.validate_reset_code(data.code)

@router.post("/reset-password", 
             status_code=status.HTTP_200_OK, 
             summary="Redefinir senha")
def reset_password(
    data: schema.ResetPasswordSchema, 
    x_recovery_token: str = Header(None), 
    db: Session = Depends(get_db)
):
    """
    Redefine a senha do usuário usando o token de recuperação.
    
    - **new_password**: Nova senha (mínimo 6 caracteres)
    - **confirm_password**: Confirmação da nova senha
    - **X-Recovery-Token** (Header): Token de recuperação obtido na validação do código
    """
    if not x_recovery_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Token de recuperação é obrigatório. Envie no header 'X-Recovery-Token'."
        )
    return service_auth.reset_password_with_token(
        db, 
        x_recovery_token, 
        data.new_password, 
        data.confirm_password
    )