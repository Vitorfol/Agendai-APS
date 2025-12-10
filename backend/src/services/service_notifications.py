from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..models import models
from ..schemas import schema
from typing import List


def criar_notificacao(db: Session, dados: schema.NotificacaoCreate):
	"""Cria uma notificação para um usuário.

	Valida que o usuário exista, insere a notificação e retorna o objeto persistido.
	"""
	try:
		usuario = db.query(models.Usuario).filter(models.Usuario.id == dados.id_usuario).first()
		if not usuario:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

		nova = models.Notificacao(
			id_usuario=dados.id_usuario,
			data=dados.data,
			evento=getattr(dados, "evento", None),
			mensagem=getattr(dados, "mensagem", None)
		)

		db.add(nova)
		db.commit()
		db.refresh(nova)
		return nova

	except HTTPException:
		db.rollback()
		raise
	except Exception as e:
		db.rollback()
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Falha ao criar notificação: {str(e)}",
		)


def listar_notificacoes_por_usuario(db: Session, id_usuario: int) -> List[models.Notificacao]:
	try:
		return db.query(models.Notificacao).filter(models.Notificacao.id_usuario == id_usuario).all()
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Falha ao listar notificações: {str(e)}",
		)


def deletar_notificacao(db: Session, id_notificacao: int):
	try:
		notif = db.query(models.Notificacao).filter(models.Notificacao.id == id_notificacao).first()
		if not notif:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificação não encontrada.")

		db.delete(notif)
		db.commit()
		return {"detail": "Notificação removida."}

	except HTTPException:
		db.rollback()
		raise
	except Exception as e:
		db.rollback()
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Falha ao deletar notificação: {str(e)}",
		)


