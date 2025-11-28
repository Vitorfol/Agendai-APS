from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from ..core.config import settings
from ..database.connection import get_db
from ..services import service_auth
from ..schemas import schema
from ..schemas.jwt import TokenPayload
from typing import Union
from sqlalchemy import text
from fastapi.responses import JSONResponse

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
    # Se for aluno, fazer JOIN com a tabela `aluno` para obter `matricula` (coluna existe apenas em `aluno`)
    if current_payload.tag == "aluno":
        stmt = text(
            "SELECT u.id, u.nome, u.email, u.cpf, a.matricula "
            "FROM usuario u JOIN aluno a ON a.id_usuario = u.id "
            "WHERE u.email = :email"
        )
    else:
        # outros tipos (professor, etc.) não têm matrícula na tabela `usuario`
        stmt = text("SELECT id, nome, email, cpf FROM usuario WHERE email = :email")

    row = db.execute(stmt, {"email": email}).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    result = dict(row._mapping)
    return JSONResponse(content=result)

#   Testes manuais com curl:
#   RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login \
#   -H "Content-Type: application/json" \
#   -d '{"email":"contato@uece.br","password":"dedelbrabo"}')
#   ACCESS_TOKEN=$(python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))"
#   <<< "$RESPONSE") && curl -s -H "Authorization: Bearer $ACCESS_TOKEN"
#   http://localhost:8000/api/users/me | python3 -m json.tool
    
    