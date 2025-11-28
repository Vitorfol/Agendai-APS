from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import timedelta
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
            idUniversidade=dados.idUniversidade,
            dataInicio=dados.dataInicio,
            dataTermino=dados.dataTermino,
            recorrencia=dados.recorrencia,
            categoria=dados.categoria,
            idProprietario=dados.idPproprietario
        )

        db.add(novo_evento)
        db.flush()
        gerar_ocorrencias_evento(db, novo_evento)
        db.commit()
        db.refresh(novo_evento) # Recarrega o objeto com o ID gerado pelo banco

        return novo_evento

    except Exception as e:
        db.rollback() # Desfaz tudo se der erro
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao persistir evento no banco: {str(e)}"
        )
    
def gerar_ocorrencias_evento(db: Session, evento: models.Evento):
    ocorrencias = []

    recorrencia = evento.recorrencia.lower() if evento.recorrencia else None

    # Caso não tenha recorrência definida → apenas uma ocorrência
    if recorrencia not in ["diario", "diario_uteis", "semanal"]:
        ocorrencia = models.OcorrenciaEvento(
            idEvento=evento.id,
            data=evento.dataInicio,
            local=evento.local
        )
        db.add(ocorrencia)
        ocorrencias.append(ocorrencia)
        return ocorrencias

    data_atual = evento.dataInicio
    dia_semana_inicial = evento.dataInicio.weekday()  # 0 = seg ... 6 = dom

    while data_atual.date() <= evento.dataTermino.date():

        gerar = False

        # --- 1. RECORRÊNCIA DIÁRIA ---
        if recorrencia == "Diário":
            gerar = True

        # --- 2. RECORRÊNCIA DIÁRIA (DIAS ÚTEIS) ---
        elif recorrencia == "Diário (Dias úteis)":
            # weekday 0 a 4 = seg a sex
            if 0 <= data_atual.weekday() <= 4:
                gerar = True

        # --- 3. RECORRÊNCIA SEMANAL ---
        elif recorrencia == "Semanal":
            if data_atual.weekday() == dia_semana_inicial:
                gerar = True

        # Criar ocorrência se permitido pela regra
        if gerar:
            ocorrencia = models.OcorrenciaEvento(
                idEvento=evento.id,
                data=data_atual,
                local=evento.local
            )
            db.add(ocorrencia)
            ocorrencias.append(ocorrencia)

        data_atual += timedelta(days=1)

    return ocorrencias