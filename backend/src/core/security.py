from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import jwt, JWTError
from .config import settings
from ..models.jwt import TokenPayload

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_senha(senha_pura: str, senha_hash: str) -> bool:
    return pwd_context.verify(senha_pura, senha_hash)

def pegar_senha_hash(senha: str) -> str:
    return pwd_context.hash(senha)

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Cria um JWT de acesso (access token).

    subject: normalmente o identificador do usuário (ex: email ou user_id)
    expires_delta: timedelta opcional para sobrescrever a expiração padrão nas settings
    Retorna: token JWT (string)
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": subject, "type": "access", "exp": int(expire.timestamp())}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Cria um JWT de refresh (refresh token).

    Por padrão usa REFRESH_TOKEN_EXPIRE_DAYS das settings. expires_delta pode sobrescrever.
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": subject, "type": "refresh", "exp": int(expire.timestamp())}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenPayload:
    """Decodifica e valida um JWT retornando um TokenPayload.

    Lança `jose.JWTError` em caso de token inválido/expirado. O chamador deve tratar o erro
    e converter em HTTPException quando for o caso.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # jose já valida `exp` automaticamente e lança JWTError se expirado
        return TokenPayload(**payload)
    except JWTError:
        # Propaga o erro para o chamador tratar (ex: lançar HTTPException 401)
        raise