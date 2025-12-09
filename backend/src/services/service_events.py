from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from fastapi import HTTPException, status
from ..models import models # Onde está sua classe Evento
from sqlalchemy import delete
from datetime import datetime, timedelta, date
from ..core.constants import HORARIOS, DIAS_MAP

def criar_evento_logica(db: Session, dados, disciplina=None, dias: list = None):

    # 1. Validar datas
    if dados.data_termino <= dados.data_inicio:
        raise HTTPException(
            status_code=400,
            detail="A data de término deve ser posterior à data de início."
        )

    # 2. Validar proprietário
    if dados.email_proprietario is not None:
        usuario = db.query(models.Usuario).filter(
            models.Usuario.email == dados.email_proprietario
        ).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuário proprietário não encontrado.")

    try:
        # 3. Criar evento
        novo_evento = models.Evento(
            id_universidade=dados.id_universidade,
            nome=dados.nome,
            descricao=dados.descricao,
            data_inicio=dados.data_inicio,
            data_termino=dados.data_termino,
            recorrencia=dados.recorrencia,
            categoria=dados.categoria,
            email_proprietario=dados.email_proprietario
        )

        db.add(novo_evento)
        db.flush()  # agora novo_evento.id está disponível

        # 4. Criar disciplina se for categoria "Disciplina"
        if dados.categoria == "Disciplina" and disciplina:

            nova_disciplina = criar_disciplina(
                db=db,
                id_evento=novo_evento.id,
                disciplina=disciplina
            )

            # Criar dias vinculados
            if dias:
                dias_criados = criar_dias_disciplina(
                    db=db,
                    id_disciplina=nova_disciplina.id_evento,
                    dias=dias
                )
                nova_disciplina.disciplina_dias = dias_criados

            novo_evento.disciplina = nova_disciplina

        if novo_evento.categoria != "Disciplina":
            # Gerar ocorrências para eventos que não são disciplinas
            gerar_ocorrencias_evento(db, novo_evento)
        else:
            gerar_ocorrencias_disciplina(db, novo_evento, novo_evento.disciplina)

        db.commit()
        db.refresh(novo_evento)

        return novo_evento

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao persistir evento no banco: {str(e)}"
        )

    


def criar_disciplina(db: Session, id_evento: int, disciplina):
    nova_disciplina = models.Disciplina(
        id_evento=id_evento,
        id_professor=disciplina.id_professor,
        horario=disciplina.horario,
        nome=disciplina.nome
    )

    db.add(nova_disciplina)
    db.flush()  # necessário para persistir antes de criar os dias

    return nova_disciplina

def parse_horario(horario: str):
    dias, blocos, turno = horario.split("-")

    return {
        "dias_semana": [d for d in dias],  # mantém como string
        "blocos": list(blocos),
        "turno": turno
    }

def gerar_ocorrencias_disciplina(db: Session, evento: models.Evento, disciplina: models.Disciplina):
    """
    Gera ocorrências semanais dentro do intervalo do EVENTO (não do semestre).
    """

    info = parse_horario(disciplina.horario)

    dias_semana = info["dias_semana"]
    blocos = info["blocos"]
    turno = info["turno"]

    data_inicio = evento.data_inicio
    data_fim = evento.data_termino

    ocorrencias = []

    for dia_str in dias_semana:
        weekday = DIAS_MAP[dia_str]   # agora funciona

        # encontrar a primeira data válida
        dt = data_inicio
        while dt.weekday() != weekday:
            dt += timedelta(days=1)

        # gerar todas as ocorrências semanais
        while dt <= data_fim:

            hora_inicio = HORARIOS[turno][blocos[0]][0]

            dt_inicio = datetime.combine(dt.date(), hora_inicio)

            ocorrencia = models.OcorrenciaEvento(
                id_evento=evento.id,
                data=dt_inicio,
            )

            db.add(ocorrencia)
            ocorrencias.append(ocorrencia)

            dt += timedelta(days=7)

    return ocorrencias

from datetime import timedelta

def gerar_ocorrencias_evento(db: Session, evento: models.Evento):
    """
    Gera ocorrências para o evento dentro do intervalo [data_inicio, data_termino].
    Tipos de recorrência:
        - "diario": todos os dias
        - "diario_uteis": apenas dias úteis (segunda a sexta)
        - "semanal": mesma data do dia da semana do início
    """

    if evento.data_inicio > evento.data_termino:
        raise HTTPException(
            status_code=500,
            detail="Inconsistência detectada: data_inicio > data_termino."
        )

    ocorrencias = []

    # Evento único
    if not evento.recorrencia == "unico":
        ocorrencia = models.OcorrenciaEvento(
            id_evento=evento.id,
            data=evento.data_inicio,
            local=None
        )
        db.add(ocorrencia)
        ocorrencias.append(ocorrencia)
        return ocorrencias

    # Evento recorrente
    data_atual = evento.data_inicio

    if evento.recorrencia == "diario":
        delta = timedelta(days=1)
        while data_atual <= evento.data_termino:
            ocorrencia = models.OcorrenciaEvento(
                id_evento=evento.id,
                data=data_atual,
                local=None
            )
            db.add(ocorrencia)
            ocorrencias.append(ocorrencia)
            data_atual += delta

    elif evento.recorrencia == "diario_uteis":
        while data_atual <= evento.data_termino:
            if data_atual.weekday() < 5:  # 0=segunda, 4=sexta
                ocorrencia = models.OcorrenciaEvento(
                    id_evento=evento.id,
                    data=data_atual,
                    local=None
                )
                db.add(ocorrencia)
                ocorrencias.append(ocorrencia)
            data_atual += timedelta(days=1)

    elif evento.recorrencia == "semanal":
        weekday_inicial = data_atual.weekday()
        while data_atual <= evento.data_termino:
            if data_atual.weekday() == weekday_inicial:
                ocorrencia = models.OcorrenciaEvento(
                    id_evento=evento.id,
                    data=data_atual,
                    local=None
                )
                db.add(ocorrencia)
                ocorrencias.append(ocorrencia)
            data_atual += timedelta(days=1)

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de recorrência desconhecido: {evento.recorrencia}"
        )

    return ocorrencias


    
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