from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from ..core.config import settings
from ..database.connection import get_db
from ..services import service_notifications
from ..schemas import schema

router = APIRouter(prefix=f"{settings.API_V1_STR.rstrip('/')}/notifications", tags=["Notificações"])


@router.post("/", response_model=schema.NotificacaoResponse, status_code=status.HTTP_201_CREATED)
def criar_notificacao_endpoint(dados: schema.NotificacaoCreate, db: Session = Depends(get_db)):
	try:
		novo = service_notifications.criar_notificacao(db, dados)
		return novo
	except HTTPException as e:
		raise e
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Erro interno ao criar notificação: {str(e)}",
		)


@router.get("/user/{id_user}", response_model=list[schema.NotificacaoResponse], status_code=status.HTTP_200_OK)
def listar_notificacoes(id_user: int, db: Session = Depends(get_db)):
	try:
		return service_notifications.listar_notificacoes_por_usuario(db, id_user)
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Erro interno ao listar notificações: {str(e)}",
		)


@router.delete("/{id_notificacao}", status_code=status.HTTP_200_OK)
def deletar_notificacao(id_notificacao: int, db: Session = Depends(get_db)):
	try:
		return service_notifications.deletar_notificacao(db, id_notificacao)
	except HTTPException as e:
		raise e
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Erro interno ao deletar notificação: {str(e)}",
		)

