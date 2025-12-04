from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..models import models # Onde está sua classe Evento
from sqlalchemy import delete

def criar_evento_logica(db: Session, dados, disciplina = None):
    # 1. Validação de Negócio: Datas Coerentes
    # Não faz sentido o evento terminar antes de começar
    if dados.data_termino <= dados.data_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A data de término deve ser posterior à data de início."
        )

    # 2. Validação de Integridade (Opcional, mas recomendado)
    # Verificar se o proprietário existe antes de tentar criar
    if dados.email_proprietario is not None:
        usuario = db.query(models.Usuario).filter(models.Usuario.email == dados.email_proprietario).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuário proprietário não encontrado.")

    try:
        # 3. Criação do Objeto Evento
        # Note que mapeamos os campos do Pydantic (dados) para o SQLAlchemy (models)
        novo_evento = models.Evento(
            id_universidade=dados.id_universidade,
            nome = dados.nome,
            descricao = dados.descricao,
            data_inicio=dados.data_inicio,
            data_termino=dados.data_termino,
            recorrencia=dados.recorrencia,
            categoria=dados.categoria,
            email_proprietario=dados.email_proprietario
        )


        db.add(novo_evento)
        if dados.categoria == "Disciplina" and dados.id_disciplina is not None:
            nova_disciplina = criar_disciplina_logica(db=db, dados=disciplina)
            nova_disciplina.id_evento = novo_evento.id
            db.add(nova_disciplina)
        db.commit() # Salva permanentemente no banco
        db.refresh(novo_evento) # Recarrega o objeto com o ID gerado pelo banco
        db.refresh(nova_disciplina)

        return {"evento":novo_evento} if dados.categoria != "Disciplina" else {"evento":novo_evento,"disciplina":nova_disciplina}

    except Exception as e:
        db.rollback() # Desfaz tudo se der erro
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao persistir evento no banco: {str(e)}"
        )
    


def criar_disciplina_logica(db: Session, dados):
    try:
        nova_disciplina = models.Disciplina(
            nome=dados.nome,
            codigo=dados.codigo,
            nome_curso=dados.id_curso
        )

        return nova_disciplina

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao persistir disciplina no banco: {str(e)}"
        )

def deletar_evento(db: Session, id_evento: int):

    # 1. Buscar o evento
    evento = db.query(models.Evento).filter(models.Evento.id == id_evento).first()
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado."
        )

    # 2. Remover PRESENÇAS das ocorrências desse evento
    db.query(models.Presenca).filter(
        models.Presenca.id_ocorrencia_evento.in_(
            db.query(models.OcorrenciaEvento.id).filter(models.OcorrenciaEvento.id_evento == id_evento)
        )
    ).delete(synchronize_session=False)

    # 3. Remover OCORRÊNCIAS do evento
    db.query(models.OcorrenciaEvento).filter(
        models.OcorrenciaEvento.id_evento == id_evento
    ).delete(synchronize_session=False)

    # 4. Remover CONVIDADOS do evento
    db.query(models.Convidado).filter(
        models.Convidado.id_evento == id_evento
    ).delete(synchronize_session=False)

    # 5. Remover disciplina associada (caso exista)
    disciplina = db.query(models.Disciplina).filter(
        models.Disciplina.id_evento == id_evento
    ).first()

    if disciplina:
        # 5.1 Remover dias da disciplina
        db.query(models.DisciplinaDias).filter(
            models.DisciplinaDias.id_disciplina == disciplina.id_evento
        ).delete(synchronize_session=False)

        # 5.2 Remover curso_disciplina
        db.query(models.CursoDisciplina).filter(
            models.CursoDisciplina.id_disciplina == disciplina.id_evento
        ).delete(synchronize_session=False)

        # 5.3 Remover a disciplina em si
        db.query(models.Disciplina).filter(
            models.Disciplina.id_evento == id_evento
        ).delete(synchronize_session=False)

    # 6. Finalmente, remover o EVENTO
    db.query(models.Evento).filter(models.Evento.id == id_evento).delete(synchronize_session=False)

    db.commit()

    return {"mensagem": "Evento e suas dependências deletados com sucesso!"}

