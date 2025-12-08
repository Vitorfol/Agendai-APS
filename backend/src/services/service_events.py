from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from fastapi import HTTPException, status
from ..models import models # Onde está sua classe Evento
from sqlalchemy import delete
from datetime import datetime, timedelta, date

def criar_evento_logica(db: Session, dados, disciplina = None,dias = None):
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
        db.flush()  # Garante que o ID seja gerado
        if dados.categoria == "Disciplina" and disciplina is not None and dias is not None:
            nova_disciplina, dias = criar_disciplina_logica(db=db, disciplina=disciplina, dias=dias)
            nova_disciplina.id_evento = novo_evento.id
            dias.id_disciplina = novo_evento.id
            db.add(nova_disciplina)
            db.add(dias)
        db.commit() # Salva permanentemente no banco
        db.refresh(novo_evento) # Recarrega o objeto com o ID gerado pelo banco
        db.refresh(nova_disciplina) if disciplina is not None else None
        novo_evento.disciplina = nova_disciplina if disciplina is not None else None
        novo_evento.disciplina.disciplina_dias = [dias] if disciplina is not None else None

        return novo_evento

    except Exception as e:
        db.rollback() # Desfaz tudo se der erro
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao persistir evento no banco: {str(e)}"
        )
    


def criar_disciplina_logica(db: Session, disciplina,dias):
    try:
        nova_disciplina = models.Disciplina(
            id_evento=0,  # Será atualizado depois
            id_professor=disciplina.id_professor,
            horario=disciplina.horario,
            nome = disciplina.nome
        )
        dias = models.DisciplinaDias(
            id_disciplina=0,  # Será atualizado depois
            dia = dias.dia

        )
    

        return nova_disciplina,dias

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao persistir disciplina no banco: {str(e)}"
        )
    
def listar_ocorrencias_por_evento(db, id_evento):
    try:
        ocorrencias = db.query(models.OcorrenciaEvento).filter(models.OcorrenciaEvento.id_evento == id_evento).all()
        return ocorrencias
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar ocorrências do evento: {str(e)}"
        )
    
def listar_ocorrencias_por_evento_usuario(db, id_evento, email_user):
    try:
        ocorrencias = db.query(models.OcorrenciaEvento).join(models.Evento).filter(
            models.Evento.id == id_evento
        ).all()
        return ocorrencias
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar ocorrências do evento para o usuário: {str(e)}"
        )
    

def listar_ocorrencias_por_usuario(db: Session, id_user: str):
    try:
        ocorrencias = db.query(models.OcorrenciaEvento).join(models.Presenca).filter(
            models.Presenca.id_aluno == id_user
        ).all()
        return ocorrencias
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar ocorrências para o usuário: {str(e)}"
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


def pegar_evento_por_id(db: Session, id_evento: int):
    evento = db.query(models.Evento).filter(models.Evento.id == id_evento).first()
    return evento


def pegar_ocorrencias_evento(db: Session, id_evento: int):
    ocorrencias = db.query(models.OcorrenciaEvento).filter(models.OcorrenciaEvento.id_evento == id_evento).all()
    return ocorrencias

def pegar_ocorrencia_evento_por_data(db: Session, id_evento: int, date: date) -> dict | None: 
    
    start = datetime(date.year, date.month, date.day) 
    end = start + timedelta(days=1)  
    
    ocorrencia = db.query(models.OcorrenciaEvento).options(
        # Eager-load evento + disciplina + disciplina_dias para evitar N+1
        joinedload(models.OcorrenciaEvento.evento)
        .joinedload(models.Evento.disciplina)
        .joinedload(models.Disciplina.disciplina_dias)
    ).filter(
        models.OcorrenciaEvento.id_evento == id_evento,
        models.OcorrenciaEvento.data >= start,
        models.OcorrenciaEvento.data < end
    ).first()
    
    if not ocorrencia:
        return None

    # Se for disciplina, buscar os dias diretamente via SQL para evitar limitações
    # do mapeamento ORM (onde a PK atual de DisciplinaDias pode colidir e sobrescrever
    # múltiplas linhas com o mesmo id_disciplina). Isso garante que retornemos todos
    # os dias armazenados no banco.
    dias_list = None
    try:
        disciplina = getattr(ocorrencia.evento, 'disciplina', None)
        if disciplina:
            # Ordena os dias na ordem da semana usando FIELD para garantir ordem previsível
            result = db.execute(text(
                "SELECT dia FROM disciplina_dias WHERE id_disciplina = :id "
                "ORDER BY FIELD(dia, 'Segunda','Terça','Quarta','Quinta','Sexta','Sábado','Domingo')"
            ), {"id": disciplina.id_evento})
            dias_list = [row[0] for row in result.fetchall()]
    except Exception:
        dias_list = None

    return montar_informacoes_ocorrencia(ocorrencia, dias_list=dias_list)


def montar_informacoes_ocorrencia(ocorrencia: models.OcorrenciaEvento, dias_list: list[str] | None = None) -> dict:
    """
    Função responsável por selecionar e formatar os dados da ocorrência e do evento relacionado.
    Você pode customizar aqui quais campos quer retornar.
    """
    # data: apenas data (sem horário)
    data_only = ocorrencia.data.date() if isinstance(ocorrencia.data, datetime) else ocorrencia.data

    # por padrão, hora será o horário da ocorrência no formato HH:MM:SS
    hora_val: str | None = None
    try:
        hora_val = ocorrencia.data.time().isoformat()
    except Exception:
        hora_val = None

    # coletar recorrência do evento
    recorrencia_val = ocorrencia.evento.recorrencia if hasattr(ocorrencia.evento, 'recorrencia') else None

    # se for Disciplina, pegar horario da disciplina (string como 'AB'/'CD') e os dias
    if getattr(ocorrencia.evento, 'categoria', None) and ocorrencia.evento.categoria.lower() == 'disciplina':
        disciplina = getattr(ocorrencia.evento, 'disciplina', None)
        if disciplina:
            # sobrescreve hora com o valor textual da disciplina
            hora_val = disciplina.horario
            # if dias_list was not provided, attempt to read via relationship as fallback
            if dias_list is None:
                dias_list = [d.dia for d in (disciplina.disciplina_dias or [])]

    # retorna dict flat (sem subdivisão de evento)
    info = {
        "local": ocorrencia.local,
        "data": data_only,
        "hora": hora_val,
        "nome": ocorrencia.evento.nome,
        "categoria": ocorrencia.evento.categoria,
        "descricao": ocorrencia.evento.descricao,
        "recorrencia": recorrencia_val,
    }
    # incluir 'dias' somente quando existir lista de dias (apenas para Disciplina)
    if dias_list is not None:
        info["dias"] = dias_list
    return info