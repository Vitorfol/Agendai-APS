from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..models import models # Onde está sua classe Evento

def criar_evento_logica(db: Session, dados):
    # 1. Validação de Negócio: Datas Coerentes
    # Não faz sentido o evento terminar antes de começar
    if dados.dataTermino <= dados.dataInicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A data de término deve ser posterior à data de início."
        )

    # 2. Validação de Integridade (Opcional, mas recomendado)
    # Verificar se o proprietário existe antes de tentar criar
    if dados.idProprietario is not None:
        usuario = db.query(models.Usuario).filter(models.Usuario.id == dados.id_proprietario).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuário proprietário não encontrado.")

    try:
        # 3. Criação do Objeto Evento
        # Note que mapeamos os campos do Pydantic (dados) para o SQLAlchemy (models)
        novo_evento = models.Evento(
            idUniversidade=dados.id_universidade,
            dataInicio=dados.data_inicio,
            dataTermino=dados.data_termino,
            recorrente=dados.recorrente,
            categoria=dados.categoria,
            idProprietario=dados.id_proprietario
        )

        db.add(novo_evento)
        db.commit() # Salva permanentemente no banco
        db.refresh(novo_evento) # Recarrega o objeto com o ID gerado pelo banco

        return novo_evento

    except Exception as e:
        db.rollback() # Desfaz tudo se der erro
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao persistir evento no banco: {str(e)}"
        )