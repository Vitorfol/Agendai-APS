from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from ..core.config import settings
from ..database.connection import get_db
from ..services import service_auth
from ..schemas import schema
from ..schemas.jwt import TokenPayload
from typing import Union
from sqlalchemy import text

router = APIRouter(prefix=f"{settings.API_V1_STR.rstrip('/')}/users", tags=["Usuários"])

@router.get(
    "/me",
    response_model=Union[schema.UsuarioResponse, schema.UniversidadeResponse],
    status_code=status.HTTP_200_OK,
    summary="Obter informações do usuário autenticado",
)
def user_me(
    current_payload: TokenPayload = Depends(service_auth.get_current_user),
    db: Session = Depends(get_db),
) -> Union[schema.UsuarioResponse, schema.UniversidadeResponse]:
    """Retorna os dados do usuário autenticado.

    Usa a `tag` presente no payload do token para decidir em qual tabela buscar
    (ex: 'universidade' -> tabela `universidade`, caso contrário -> `usuario`).
    """
    email = service_auth.get_current_user_email(current_payload)
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    if current_payload.tag == "universidade":
        stmt = text("SELECT id, nome, sigla, cnpj, email FROM universidade WHERE email = :email")
        row = db.execute(stmt, {"email": email}).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Universidade não encontrada")
        return dict(row._mapping)

    # Por padrão, assume usuário 'usuario'
    stmt = text("SELECT id, nome, email, cpf FROM usuario WHERE email = :email")
    row = db.execute(stmt, {"email": email}).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return dict(row._mapping)
    
    