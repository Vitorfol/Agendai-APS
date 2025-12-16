from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text, func
from fastapi import HTTPException, status
from ..models import models # Onde está sua classe Evento
from sqlalchemy import delete
from datetime import datetime, timedelta, date
from ..core.constants import HORARIOS, DIAS_MAP, NUM_PARA_DIA
from ..schemas.jwt import TokenPayload
from ..services.service_notifications import notificar_usuarios_em_massa,criar_notificacao

def criar_evento_logica(db: Session, dados, disciplina=None, current_email: str = None):

    # 1. Validar datas
    if dados.data_termino <= dados.data_inicio and dados.recorrencia != "unico":
        raise HTTPException(
            status_code=400,
            detail="A data de término deve ser posterior à data de início."
        )
    
    if dados.horario_termino <= dados.horario_inicio:
        raise HTTPException(
            status_code=400,
            detail="O horário de término deve ser posterior ao horário de início."
        )

    # 2. Validar proprietário (pode ser Usuario ou Universidade)
    usuario = None
    if current_email is not None:
        # Tentar buscar em Usuario primeiro
        usuario = db.query(models.Usuario).filter(
            models.Usuario.email == current_email
        ).first()
        
        # Se não encontrou em Usuario, tentar em Universidade
        if not usuario:
            universidade = db.query(models.Universidade).filter(
                models.Universidade.email == current_email
            ).first()
            if not universidade:
                raise HTTPException(status_code=404, detail="Proprietário não encontrado.")

    try:
        # 3. Criar evento
        novo_evento = models.Evento(
            id_universidade=dados.id_universidade,
            nome=dados.nome,
            descricao=dados.descricao,
            data_inicio=dados.data_inicio,
            data_termino=dados.data_termino,
            recorrencia=dados.recorrencia,
            horario_inicio=dados.horario_inicio,
            horario_termino=dados.horario_termino,
            local_padrao=dados.local_padrao,
            categoria=dados.categoria,
            email_proprietario=current_email 
        )

        db.add(novo_evento)
        db.flush()  # agora novo_evento.id está disponível

        # 4. Criar disciplina se for categoria "Disciplina"
        if dados.categoria == "Disciplina" and disciplina:

            nova_disciplina = criar_disciplina(
                db=db,
                id_evento=novo_evento.id,
                disciplina=disciplina,
                id_professor=usuario.id if usuario else None
            )

            novo_evento.disciplina = nova_disciplina

        if novo_evento.categoria != "Disciplina":
            # Gerar ocorrências para eventos que não são disciplinas
            gerar_ocorrencias_evento(db, novo_evento)
        else:
            gerar_ocorrencias_disciplina(db, novo_evento, novo_evento.disciplina)

        # 5. Adicionar o proprietário como convidado automaticamente (se for usuário)
        if usuario:  # Se o proprietário for um usuário (não universidade)
            convidado_proprietario = models.Convidado(
                id_evento=novo_evento.id,
                id_usuario=usuario.id
            )
            db.add(convidado_proprietario)

        db.commit()
        db.refresh(novo_evento)  
        # Notificar o proprietário do evento (se houver usuário identificado)
        '''
        mandar_noticacao_proprietario_evento(db=db, novo_evento=novo_evento, usuario=usuario, 
        mensagem=f"Seu evento '{novo_evento.nome}' foi criado para {novo_evento.data_inicio.strftime('%d/%m/%Y às %H:%M')}")   
        mandar_notificacao_evento_usuario_atual(db=db, novo_evento=novo_evento, current_email=current_email,
        mensagem=f"Seu evento '{novo_evento.nome}' foi criado para {novo_evento.data_inicio.strftime('%d/%m/%Y às %H:%M')}")
        '''
        return novo_evento

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao persistir evento no banco: {str(e)}"
        )
    
def mandar_noticacao_proprietario_evento(db: Session, novo_evento:models.Evento,usuario:models.Usuario,
                                   mensagem: str = None):
    if usuario:
            #mensagem_proprietario = 
            try:
                output_prop = notificar_usuarios_em_massa(
                    db=db,
                    ids_usuarios=[usuario.id],
                    mensagem=mensagem,
                    id_evento=novo_evento.id
                )
                print(output_prop)
            except Exception:
                # não falhar a criação do evento caso notificação falhe
                pass    


def mandar_notificacao_evento_usuario_atual(db: Session, novo_evento:models.Evento, current_email: str, mensagem: str = None):
# --- NOTIFICAR O USUÁRIO ATUAL (a partir do TokenPayload) ---
    try:
            if current_email:
                usuario_token = db.query(models.Usuario).filter(models.Usuario.email == current_email).first()
                if usuario_token:
                    #mensagem_token = f"Seu evento '{novo_evento.nome}' foi criado para {novo_evento.data_inicio.strftime('%d/%m/%Y às %H:%M')}"
                    # não deixar falha na notificação interromper a criação do evento
                    '''
                    try:
                        notificar_usuarios_em_massa(
                            db=db,
                            ids_usuarios=[usuario_token.id],
                            mensagem=mensagem,
                            id_evento=novo_evento.id
                        )
                    except Exception:
                            pass
                    '''
    except Exception:
        pass
    
def criar_disciplina(db: Session, id_evento: int, disciplina, id_professor: int):
    nova_disciplina = models.Disciplina(
        id_evento=id_evento,
        id_professor=id_professor,
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
        dia_nome = NUM_PARA_DIA[dia_str]
        criar_dias_disciplina(db, evento.id, dia_nome)

        # encontrar a primeira data válida
        dt = data_inicio
        while dt.weekday() != weekday:
            dt += timedelta(days=1)

        # gerar todas as ocorrências semanais
        while dt <= data_fim:

            horario_inicio = HORARIOS[turno][blocos[0]][0]
            horario_termino = HORARIOS[turno][blocos[-1]][1]

            dt_inicio = dt.date()

            ocorrencia = models.OcorrenciaEvento(
                id_evento=evento.id,
                data=dt_inicio,
                local = evento.local_padrao,
                horario_inicio = horario_inicio,
                horario_termino = horario_termino
            )

            db.add(ocorrencia)
            ocorrencias.append(ocorrencia)

            dt += timedelta(days=7)

    return ocorrencias

def criar_dias_disciplina(db, id_disciplina: int, dia: str):
            dia_disciplina = models.DisciplinaDias(
                id_disciplina=id_disciplina,
                dia=dia
            )
            db.add(dia_disciplina)
            return dia_disciplina





def gerar_ocorrencias_evento(db: Session, evento: models.Evento):
    """
    Gera ocorrências para o evento dentro do intervalo [data_inicio, data_termino].
    Tipos de recorrência:
        - "diario": todos os dias
        - "diario_uteis": apenas dias úteis (segunda a sexta)
        - "semanal": mesma data do dia da semana do início
    """

    if evento.data_inicio > evento.data_termino and evento.recorrencia != "unico":
        raise HTTPException(
            status_code=500,
            detail="Inconsistência detectada: data_inicio > data_termino."
        )

    ocorrencias = []

    # Evento único
    if evento.recorrencia == "unico":
        ocorrencia = models.OcorrenciaEvento(
            id_evento=evento.id,
            data=evento.data_inicio,
            horario_inicio=evento.horario_inicio,
            horario_termino=evento.horario_termino,
            local=evento.local_padrao
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
                horario_inicio=evento.horario_inicio,
                horario_termino=evento.horario_termino,

                local=evento.local_padrao
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
                    horario_inicio=evento.horario_inicio,
                    horario_termino=evento.horario_termino,
                    local=evento.local_padrao
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
                    horario_inicio=evento.horario_inicio,
                    horario_termino=evento.horario_termino,
                    local=evento.local_padrao
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
    
def listar_ocorrencias_de_evento_usuario(db, user_email, data, categoria):
    """
    Lista todas as ocorrências de eventos associados ao usuário autenticado,
    com filtros opcionais por data e categoria.
    
    Args:
        db: Sessão do banco de dados
        user_email: Email do usuário autenticado (pode ser Usuario ou Universidade)
        data: Data específica para filtrar ocorrências (opcional)
        categoria: Categoria de evento para filtrar (opcional)
    
    Returns:
        Lista de dicts formatados usando montar_informacoes_ocorrencia
    """
    # 1. Buscar usuário ou universidade pelo email
    user = db.query(models.Usuario).filter(models.Usuario.email == user_email).first()
    
    # Se não encontrou em Usuario, tentar em Universidade
    if not user:
        universidade = db.query(models.Universidade).filter(models.Universidade.email == user_email).first()
        if not universidade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário ou universidade não encontrado."
            )
        # Usar universidade como "user" para continuar o fluxo
        # Neste caso, vamos buscar eventos onde a universidade é proprietária
        user_id = None  # Universidade não tem id_usuario
        is_universidade = True
    else:
        user_id = user.id
        is_universidade = False
    
    # 2. Buscar IDs dos eventos baseado no tipo de usuário
    if is_universidade:
        # Para universidade: buscar eventos onde ela é proprietária
        ids_eventos_usuario = db.query(models.Evento.id).filter(
            models.Evento.email_proprietario == user_email
        ).distinct().subquery()
    else:
        # Para usuário comum: buscar eventos onde está convidado
        ids_eventos_usuario = db.query(models.Convidado.id_evento).filter(
            models.Convidado.id_usuario == user_id
        ).distinct().subquery()
    
    # 3. Montar query de ocorrências fazendo join com Evento
    # O join é necessário para acessar dados do evento e aplicar filtros
    query_ocorrencias = db.query(models.OcorrenciaEvento).join(
        models.Evento,
        models.OcorrenciaEvento.id_evento == models.Evento.id
    ).filter(
        models.OcorrenciaEvento.id_evento.in_(ids_eventos_usuario)
    )
    
    # 4. Aplicar filtro de data (se fornecido)
    if data is not None:
        query_ocorrencias = query_ocorrencias.filter(
            func.date(models.OcorrenciaEvento.data) == data
        )
    
    # 5. Aplicar filtro de categoria (se fornecido)
    if categoria is not None:
        query_ocorrencias = query_ocorrencias.filter(
            models.Evento.categoria == categoria
        )
    
    # 6. Executar query com eager loading para evitar N+1 ao acessar relacionamentos
    # Após aplicar todos os filtros, carregamos os relacionamentos necessários
    query_ocorrencias = query_ocorrencias.options(
        joinedload(models.OcorrenciaEvento.evento)
        .joinedload(models.Evento.disciplina)
        .joinedload(models.Disciplina.disciplina_dias)
    )
    
    ocorrencias = query_ocorrencias.all()
    
    # 7. Processar cada ocorrência para montar resposta formatada
    resultado = []
    for ocorrencia in ocorrencias:
        # Verificar se o usuário é proprietário do evento
        # ocorrencia.evento funciona porque temos o relationship definido no model
        is_proprietario = ocorrencia.evento.email_proprietario == user_email
        
        # Buscar dias da disciplina se for evento do tipo disciplina
        dias_list = None
        if (ocorrencia.evento.categoria and 
            ocorrencia.evento.categoria.lower() == 'disciplina'):
            # disciplina funciona porque Evento tem relationship("Disciplina")
            disciplina = getattr(ocorrencia.evento, 'disciplina', None)
            if disciplina:
                try:
                    # Buscar dias diretamente do banco para garantir todos os registros
                    result = db.execute(text(
                        "SELECT dia FROM disciplina_dias WHERE id_disciplina = :id "
                        "ORDER BY FIELD(dia, 'Segunda','Terça','Quarta','Quinta','Sexta','Sábado','Domingo')"
                    ), {"id": disciplina.id_evento})
                    dias_list = [row[0] for row in result.fetchall()]
                except Exception:
                    # Fallback: usar relationship ORM se houver erro na query SQL
                    dias_list = [d.dia for d in (disciplina.disciplina_dias or [])]
        
        # Montar informações da ocorrência usando a função auxiliar
        info = montar_informacoes_ocorrencia(
            ocorrencia, 
            dias_list=dias_list, 
            is_proprietario=is_proprietario
        )
        # Adicionar id_evento ao dict de resposta (necessário para o frontend)
        info["id_evento"] = ocorrencia.id_evento
        resultado.append(info)
    
    return resultado 
    
    

def deletar_evento(db: Session, id_evento: int, current_email:str = None):

    # 1. Buscar o evento
    evento = db.query(models.Evento).filter(models.Evento.id == id_evento).first()
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado."
        )
    '''
    mandar_noticacao_proprietario_evento(db=db, novo_evento=evento, usuario=evento, 
    mensagem=f"O evento '{evento.nome}' foi cancelado!")   
    mandar_notificacao_evento_usuario_atual(db=db, novo_evento=evento, current_email=current_email,
    mensagem=f"O evento '{evento.nome}' foi cancelado!")
    '''

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

def pegar_ocorrencia_evento_por_data(db: Session, id_evento: int, date: date, current_user_email: str) -> dict | None: 
    
    evento = db.query(models.Evento).filter(models.Evento.id == id_evento).first()
    if not evento:
        return None
        
    is_proprietario = evento.email_proprietario == current_user_email 
    
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
        # Verificar se a categoria do evento é "Disciplina" antes de buscar os dias
        if ocorrencia.evento.categoria and ocorrencia.evento.categoria.lower() == 'disciplina':
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

    return montar_informacoes_ocorrencia(ocorrencia, dias_list=dias_list, is_proprietario=is_proprietario)


def montar_informacoes_ocorrencia(ocorrencia: models.OcorrenciaEvento, dias_list: list[str] | None = None, is_proprietario: bool = False) -> dict:
    """
    Função responsável por selecionar e formatar os dados da ocorrência e do evento relacionado.
    Você pode customizar aqui quais campos quer retornar.
    """
    # data: apenas data (sem horário)
    data_only = ocorrencia.data.date() if isinstance(ocorrencia.data, datetime) else ocorrencia.data

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
        "horario_inicio": ocorrencia.horario_inicio,
        "horario_termino": ocorrencia.horario_termino,
        "nome": ocorrencia.evento.nome,
        "categoria": ocorrencia.evento.categoria,
        "descricao": ocorrencia.evento.descricao,
        "recorrencia": recorrencia_val,
        "is_proprietario": is_proprietario
    }
    # incluir 'dias' somente quando existir lista de dias (apenas para Disciplina)
    if dias_list is not None:
        info["dias"] = dias_list
    return info


def atualizar_ocorrencia_evento_por_data(
    db: Session, 
    id_evento: int, 
    date: date, 
    payload, 
    current_user_email: str
) -> dict:
    """
    Atualiza uma ocorrência específica de um evento.
    
    Parâmetros:
        db: Sessão do banco de dados
        id_evento: ID do evento
        date: Data da ocorrência a ser atualizada
        payload: Dados para atualização (OcorrenciaEventoUpdate)
        current_user_email: Email do usuário autenticado
    
    Retorna:
        Dict com os dados da ocorrência atualizada
    
    Raises:
        HTTPException: Se o evento não existir, usuário não for proprietário, 
                       ocorrência não existir, ou nenhum campo for fornecido
    """
    # 1. Verificar se o evento existe
    evento = db.query(models.Evento).filter(models.Evento.id == id_evento).first()
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado."
        )
    
    # 2. Verificar se o usuário atual é o proprietário do evento
    if evento.email_proprietario != current_user_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para atualizar este evento."
        )
    
    # 3. Buscar a ocorrência específica pela data
    start = datetime(date.year, date.month, date.day)
    end = start + timedelta(days=1)
    
    ocorrencia = db.query(models.OcorrenciaEvento).options(
        joinedload(models.OcorrenciaEvento.evento)
        .joinedload(models.Evento.disciplina)
        .joinedload(models.Disciplina.disciplina_dias)
    ).filter(
        models.OcorrenciaEvento.id_evento == id_evento,
        models.OcorrenciaEvento.data >= start,
        models.OcorrenciaEvento.data < end
    ).first()
    
    if not ocorrencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ocorrência não encontrada para a data especificada."
        )
    
    # 4. Verificar se há pelo menos um campo para atualizar
    if payload.local is None and payload.data is None and payload.horario_inicio is None and payload.horario_termino is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo fornecido para atualização. Forneça 'local', 'data' e/ou horários."
        )
    
    # 5. Atualizar os campos fornecidos
    campos_atualizados = []
    
    if payload.local is not None:
        ocorrencia.local = payload.local
        campos_atualizados.append("local")
    
    if payload.data is not None:
        # Validar que a nova data está dentro do intervalo do evento
        if payload.data < evento.data_inicio or payload.data > evento.data_termino:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A nova data deve estar dentro do intervalo do evento."
            )
        ocorrencia.data = payload.data
        campos_atualizados.append("data")

    horario_inicio = ocorrencia.horario_inicio
    horario_termino = ocorrencia.horario_termino

    if payload.horario_inicio is not None:
        horario_inicio = payload.horario_inicio

    if payload.horario_termino is not None:
        horario_termino = payload.horario_termino

    # ⬅ Verificação do horário
    if horario_inicio is not None and horario_termino is not None:
            if horario_termino <= horario_inicio:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="O horário de término deve ser maior que o horário de início."
                )

    # Atualizar campos após validação
    ocorrencia.horario_inicio = horario_inicio
    ocorrencia.horario_termino = horario_termino
    if payload.horario_inicio is not None:
        campos_atualizados.append("horario_inicio")
    if payload.horario_termino is not None:
        campos_atualizados.append("horario_termino")
                
    # 6. Persistir as mudanças
    try:
        db.commit()
        db.refresh(ocorrencia)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar ocorrência: {str(e)}"
        )
    
    # 7. Buscar dias da disciplina (se aplicável) para retornar na resposta
    dias_list = None
    try:
        # Verificar se a categoria do evento é "Disciplina" antes de buscar os dias
        if ocorrencia.evento.categoria and ocorrencia.evento.categoria.lower() == 'disciplina':
            disciplina = getattr(ocorrencia.evento, 'disciplina', None)
            if disciplina:
                result = db.execute(text(
                    "SELECT dia FROM disciplina_dias WHERE id_disciplina = :id "
                    "ORDER BY FIELD(dia, 'Segunda','Terça','Quarta','Quinta','Sexta','Sábado','Domingo')"
                ), {"id": disciplina.id_evento})
                dias_list = [row[0] for row in result.fetchall()]
    except Exception:
        dias_list = None
    
    # 8. Verificar se o usuário atual é o proprietário
    is_proprietario = evento.email_proprietario == current_user_email
    '''
    mandar_notificacao_evento_usuario_atual(db=db,novo_evento=evento,current_email=current_user_email, mensagem= f"A Ocorrência do dia {ocorrencia.data} foi atualizada com sucesso!")
    '''
    # 9. Retornar a ocorrência atualizada formatada
    return montar_informacoes_ocorrencia(ocorrencia, dias_list=dias_list, is_proprietario=is_proprietario)


def cancelar_ocorrencia_evento_por_data(
    db: Session,
    id_evento: int,
    date: date,
    current_user_email: str
) -> dict:
    """
    Cancela (deleta) uma ocorrência específica de um evento.
    Apenas o proprietário do evento pode cancelar suas ocorrências.
    """
    # 1. Buscar o evento
    evento = db.query(models.Evento).filter(models.Evento.id == id_evento).first()
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado."
        )
    
    # 2. Verificar se o usuário atual é o proprietário do evento
    if evento.email_proprietario != current_user_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para cancelar ocorrências deste evento."
        )
    
    # 3. Buscar a ocorrência específica (comparando apenas a parte DATE do datetime)
    ocorrencia = db.query(models.OcorrenciaEvento).filter(
        models.OcorrenciaEvento.id_evento == id_evento,
        func.date(models.OcorrenciaEvento.data) == date
    ).first()
    
    if not ocorrencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ocorrência não encontrada para a data {date}."
        )
    
    # 4. Deletar a ocorrência
    try:
        db.delete(ocorrencia)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao cancelar ocorrência: {str(e)}"
        )
    '''
    mandar_notificacao_evento_usuario_atual(db=db, novo_evento=evento, current_email=current_user_email,
    mensagem=f"A Ocorrencia do dia {ocorrencia.data} foi cancelada!")
    '''
    return {"message": "Ocorrência cancelada com sucesso."}


# ========================================
# GERENCIAMENTO DE CONVIDADOS

def adicionar_participante_evento(
    db: Session, 
    id_evento: int, 
    email_usuario: str, 
    current_user: TokenPayload
):
    """
    Adiciona um ou múltiplos usuários como convidados de um evento.
    
    Suporta 3 tipos de convites:
    1. todos@<dominio>.br - Convida todos os usuários com @<dominio> no email
    2. email_curso@<dominio>.br - Convida todos os alunos do curso (busca curso.email)
    3. email@individual.br - Convida um usuário específico
    
    Args:
        db: Sessão do banco de dados
        id_evento: ID do evento
        email_usuario: Email ou padrão de email para convite
        current_user: Token payload do usuário autenticado
    
    Returns:
        Dict com estatísticas: total adicionado, já existentes, e lista de adicionados
    
    Raises:
        HTTPException: Se o evento não existir, usuário não for proprietário, etc.
    """
    # 1. Verificar se o evento existe
    evento = db.query(models.Evento).filter(models.Evento.id == id_evento).first()
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado."
        )
    
    # 2. Extrair informações do token do usuário atual
    current_user_email = getattr(current_user, 'sub', None)
    current_user_tag = getattr(current_user, 'tag', None)

    # 3. Verificar se quem está fazendo a requisição é o proprietário do evento
    if evento.email_proprietario != current_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas o proprietário do evento pode adicionar participantes."
        )
    
    # 4. Buscar convidados já existentes para evitar duplicatas
    convidados_existentes = db.query(models.Convidado.id_usuario).filter(
        models.Convidado.id_evento == id_evento
    ).all()
    ids_existentes = {c.id_usuario for c in convidados_existentes}
    
    # 5. Determinar tipo de convite e buscar usuários
    usuarios_para_convidar = []
    
    # CASO 1: todos@<dominio> - convida todos com esse domínio no email (APENAS UNIVERSIDADE)
    if email_usuario.lower().startswith("todos@"):
        # Verificar se o usuário atual é uma universidade
        if current_user_tag != 'universidade':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas universidades podem usar o convite em massa 'todos@dominio'."
            )
        
        dominio_parte = email_usuario.split("@", 1)[1]  # ex: "uece.br"
        
        # Buscar todos emails que contenham o domínio completo (incluindo subdomínios)
        # Exemplos: @uece.br, @aluno.uece.br, @prof.uece.br
        usuarios_para_convidar = db.query(models.Usuario).filter(
            models.Usuario.email.like(f'%@%.{dominio_parte}') | 
            models.Usuario.email.like(f'%@{dominio_parte}')
        ).all()
        
        if not usuarios_para_convidar:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nenhum usuário encontrado com domínio '{dominio_parte}' no email."
            )
    
    # CASO 2: email de curso - convida todos alunos do curso (APENAS UNIVERSIDADE)
    else:
        curso = db.query(models.Curso).filter(models.Curso.email == email_usuario).first()
        
        if curso:
            # Verificar se o usuário atual é uma universidade
            if current_user_tag != 'universidade':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Apenas universidades podem convidar curso completo."
                )
            # Buscar todos os alunos do curso e seus usuários
            alunos = db.query(models.Aluno).filter(
                models.Aluno.id_curso == curso.id
            ).all()
            
            if not alunos:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Curso '{curso.nome}' encontrado mas não possui alunos cadastrados."
                )
            
            # Buscar os usuários dos alunos
            ids_usuarios_alunos = [aluno.id_usuario for aluno in alunos]
            usuarios_para_convidar = db.query(models.Usuario).filter(
                models.Usuario.id.in_(ids_usuarios_alunos)
            ).all()
        
        # CASO 3: email individual
        else:
            usuario_individual = db.query(models.Usuario).filter(
                models.Usuario.email == email_usuario
            ).first()
            
            if not usuario_individual:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário não encontrado."
                )
            
            usuarios_para_convidar = [usuario_individual]
    
    # 6. Filtrar usuários que já são convidados e preparar bulk insert
    novos_convidados = []
    ja_convidados = []
    
    for usuario in usuarios_para_convidar:
        if usuario.id in ids_existentes:
            ja_convidados.append({
                "id_usuario": usuario.id,
                "nome": usuario.nome,
                "email": usuario.email
            })
        else:
            novos_convidados.append(
                models.Convidado(
                    id_evento=id_evento,
                    id_usuario=usuario.id
                )
            )
    
    # 7. Inserir novos convidados em batch
    try:
        if novos_convidados:
            db.bulk_save_objects(novos_convidados)
            db.commit()
        
        # Montar resposta
        adicionados = []
        for convidado in novos_convidados:
            usuario = next((u for u in usuarios_para_convidar if u.id == convidado.id_usuario), None)
            if usuario:
                adicionados.append({
                    "id_usuario": usuario.id,
                    "nome": usuario.nome,
                    "email": usuario.email
                })

                
        '''
        notificar_usuarios_em_massa(db=db,
                                    id_usuarios= [adicionado.id_usuario for adicionado in adicionados],
                                    mensagem= f"Você foi convidado para o evento: {evento.nome}.")
        mandar_notificacao_evento_usuario_atual(db=db, novo_evento=evento, current_email=current_user_email,
                                    mensagem=f"{len(adicionados)} participante(s) adicionado(s) com sucesso.\ntotal adicionados: {len(adicionados)},\ntotal já existentes: {len(ja_convidados)}.")
        '''
        return {
            "message": f"{len(adicionados)} participante(s) adicionado(s) com sucesso.",
            "total_adicionados": len(adicionados),
            "total_ja_existentes": len(ja_convidados),
            "adicionados": adicionados,
            "ja_existentes": ja_convidados
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao adicionar participantes: {str(e)}"
        )



def remover_participante_evento(
    db: Session,
    id_evento: int,
    email_usuario: str,
    current_user: TokenPayload
):
    """
    Remove um usuário da lista de convidados de um evento.
    
    Args:
        db: Sessão do banco de dados
        id_evento: ID do evento
        email_convidado: Email do usuário a ser removido
        current_user_email: Email do usuário que está fazendo a requisição
    
    Returns:
        Mensagem de sucesso
    
    Raises:
        HTTPException: Se o evento não existir, se o usuário não for o proprietário,
                      ou se o convidado não estiver na lista
    """
    # 1. Verificar se o evento existe
    evento = db.query(models.Evento).filter(models.Evento.id == id_evento).first()
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado."
        )
    
    # 2. Extrair informações do token do usuário atual
    current_user_email = getattr(current_user, 'sub', None)
    current_user_tag = getattr(current_user, 'tag', None)

    # 3. Verificar se quem está fazendo a requisição é o proprietário do evento
    if evento.email_proprietario != current_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas o proprietário do evento pode remover participantes."
        )

    # TODO: Implementar verificação de privilégios para universidades
    # Se current_user.tag == 'universidade' permitir operações privilegiadas
    # (por enquanto, não há comportamento especial)
    
    # 3. Buscar o usuário convidado
    usuario_convidado = db.query(models.Usuario).filter(
        models.Usuario.email == email_usuario
    ).first()
    if not usuario_convidado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )
    
    # 4. Buscar o convidado
    convidado = db.query(models.Convidado).filter(
        models.Convidado.id_evento == id_evento,
        models.Convidado.id_usuario == usuario_convidado.id
    ).first()
    
    if not convidado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não é participante deste evento."
        )
    
    # 5. Remover o convidado
    try:
        db.delete(convidado)
        db.commit()
        '''
        criar_notificacao(db=db,dados= models.Notificacao(
                id_usuario = convidado.id_usuario,
                data = datetime.now(),
                mensagem = f"Você foi removido do evento '{evento.nome}'",
                evento = evento.id
            )
        )

        mandar_notificacao_evento_usuario_atual(db=db,novo_evento=evento,current_email=current_user_email,mensagem= f"O convidado {usuario_convidado.nome} foi removido do evento com sucesso!")
        '''
        return {"message": "Participante removido com sucesso."}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao remover participante: {str(e)}"
        )


def listar_participantes_evento(db: Session, id_evento: int):
    """
    Lista todos os participantes (convidados) de um evento.
    
    Args:
        db: Sessão do banco de dados
        id_evento: ID do evento
    
    Returns:
        Lista de convidados com informações do usuário
    
    Raises:
        HTTPException: Se o evento não existir
    """
    # 1. Verificar se o evento existe
    evento = db.query(models.Evento).filter(models.Evento.id == id_evento).first()
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado."
        )
    
    # 2. Buscar todos os convidados do evento com eager loading do usuário
    convidados = db.query(models.Convidado).options(
        joinedload(models.Convidado.usuario)
    ).filter(
        models.Convidado.id_evento == id_evento
    ).all()
    
    # 3. Formatar resposta com informações dos usuários
    participantes = []
    for convidado in convidados:
        participantes.append({
            "id_convidado": convidado.id,
            "id_usuario": convidado.usuario.id,
            "nome": convidado.usuario.nome,
            "email": convidado.usuario.email
        })
    
    return participantes
