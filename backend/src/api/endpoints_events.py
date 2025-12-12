from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from ..core.config import settings
from ..database.connection import get_db 
from ..services import service_events, service_auth
from ..schemas import schema
from ..schemas.jwt import TokenPayload
from datetime import date

router = APIRouter(prefix=f"{settings.API_V1_STR.rstrip('/')}/events", tags=["Eventos"])

@router.post(
    "/", 
    response_model=schema.EventoResponse,
    status_code=status.HTTP_201_CREATED
)
def criar_evento(
    payload: schema.EventoComplexoCreate,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(service_auth.get_current_user_email)):
    try:
        novo_evento = service_events.criar_evento_logica(
            db=db,
            dados=payload.evento,
            disciplina=payload.disciplina,
            current_email = current_user_email
        )

   

        return novo_evento

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao criar evento: {str(e)}"
        )
    

@router.delete("/{id_evento}", status_code=status.HTTP_200_OK)
def deletar_evento_endpoint(id_evento: int, db: Session = Depends(get_db),
                            current_user_email: str = Depends(service_auth.get_current_user_email)):
    """
    Deleta um evento e toda a sua cadeia de dependências.
    """

    try:
        return service_events.deletar_evento(db, id_evento, current_email= current_user_email)
    except HTTPException as e:
        # Erros lançados no service retornam diretamente
        raise e
    except Exception as e:
        # Erros inesperados
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao deletar evento: {str(e)}"
        )
    


@router.get("/", response_model=list[schema.OcorrenciaEventoComIdResponse], status_code=status.HTTP_200_OK, response_model_exclude_none=True)
def listar_ocorrencias_de_evento_de_um_usuario(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(service_auth.get_current_user_email),
    data: date | None = None,
    categoria: str | None = None
):
    """
    Lista todas as ocorrencias de eventos associados ao usuário autenticado, com filtros opcionais por data e categoria.
    Retorna o id_evento junto com cada ocorrência para identificação no frontend.
    Campos None não são incluídos na resposta (ex: 'dias' só aparece para eventos tipo Disciplina).
    """
    try:
        ocorrencias = service_events.listar_ocorrencias_de_evento_usuario(
            db=db,
            user_email=current_user_email,
            data=data,
            categoria=categoria
        )
        return ocorrencias
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao listar ocorrencias de eventos do usuário: {str(e)}"
        )

@router.get("/{id_evento}/occurrences", response_model=list[schema.OcorrenciaEventoResponse], status_code=status.HTTP_200_OK)
def listar_ocorrencias_evento(id_evento: int, db: Session = Depends(get_db)):
    """
    Lista todas as ocorrências associadas a um evento.
    """
    try:
        ocorrencias = service_events.listar_ocorrencias_por_evento(db, id_evento)
        return ocorrencias
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao listar ocorrências do evento: {str(e)}"
        )

@router.get("/{id_evento}/participants", response_model=list[schema.ParticipantResponse], status_code=status.HTTP_200_OK)
def listar_participantes_evento(
    id_evento: int, 
    db: Session = Depends(get_db)
):
    """
    Lista todos os participantes de um evento específico.

    Parâmetros:
        - id_evento: ID do evento
    """
    try:
        participantes = service_events.listar_participantes_evento(
            db=db,
            id_evento=id_evento
        )
        return participantes
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao listar participantes: {str(e)}"
        )

@router.post("/{id_evento}/participants", status_code=status.HTTP_200_OK)
def adicionar_participante_evento(
    id_evento: int, 
    email_usuario: str,
    db: Session = Depends(get_db),
    current_user: TokenPayload = Depends(service_auth.get_current_user)
):
    """
    Adiciona um participante a um evento específico.

    Parâmetros:
        - id_evento: ID do evento
        - email_usuario: Email do usuário a ser adicionado como participante

    Apenas o proprietário do evento pode adicionar participantes.
    """
    try:
        resultado = service_events.adicionar_participante_evento(
            db=db,
            id_evento=id_evento,
            email_usuario=email_usuario,
            current_user=current_user
        )
        return resultado
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao adicionar participante: {str(e)}"
        )
        
@router.delete("/{id_evento}/participants", status_code=status.HTTP_200_OK)
def remover_participante_evento(
    id_evento: int, 
    email_usuario: str,
    db: Session = Depends(get_db),
    current_user: TokenPayload = Depends(service_auth.get_current_user)
):
    """
    Remove um participante de um evento específico.

    Parâmetros:
        - id_evento: ID do evento
        - email_usuario: Email do usuário a ser removido como participante

    Apenas o proprietário do evento pode remover participantes.
    """
    try:
        resultado = service_events.remover_participante_evento(
            db=db,
            id_evento=id_evento,
            email_usuario=email_usuario,
            current_user=current_user
        )
        return resultado
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao remover participante: {str(e)}"
        )

@router.get("/{id_evento}", response_model=schema.EventoResponse, status_code=status.HTTP_200_OK)
def obter_evento(id_evento: int, db: Session = Depends(get_db)):
    """
    Obtém um evento pelo seu ID.
    """
    try:
        evento = service_events.pegar_evento_por_id(db, id_evento)
        if not evento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento não encontrado."
            )
        return evento
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao obter evento: {str(e)}"
        )

@router.delete("/{id_evento}", status_code=status.HTTP_200_OK)
def deletar_evento_endpoint(id_evento: int, db: Session = Depends(get_db)):
    """
    Deleta um evento e toda a sua cadeia de dependências.
    """

    try:
        return service_events.deletar_evento(db, id_evento)
    except HTTPException as e:
        # Erros lançados no service retornam diretamente
        raise e
    except Exception as e:
        # Erros inesperados
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao deletar evento: {str(e)}"
        )

@router.get("/{id_evento}/{date}", response_model=schema.OcorrenciaEventoResponse, status_code=status.HTTP_200_OK, response_model_exclude_none=True)
def obter_ocorrencia_evento_data(id_evento: int, date: date, db: Session = Depends(get_db), current_user_email: str = Depends(service_auth.get_current_user_email)):
    """
    Obtém a ocorrência de um evento em uma data específica com dados selecionados.
    """
    try:
        # `pegar_ocorrencia_evento_por_data` aceita date/datetime and normalizes internaly,
        # então basta passar o `date` recebido (date-only) diretamente.
        ocorrencia = service_events.pegar_ocorrencia_evento_por_data(db, id_evento, date, current_user_email)
        if not ocorrencia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ocorrência não encontrada para a data especificada."
            )
        return ocorrencia
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao obter ocorrência: {str(e)}"
        )
        
@router.put("/{id_evento}/{date}", response_model=schema.OcorrenciaEventoResponse, status_code=status.HTTP_200_OK, response_model_exclude_none=True)
def atualizar_ocorrencia_evento_data(
    id_evento: int, 
    date: date, 
    payload: schema.OcorrenciaEventoUpdate, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(service_auth.get_current_user_email)
):
    """
    Atualiza o local e/ou data de uma ocorrência específica de um evento.
    
    Parâmetros:
        - id_evento: ID do evento
        - date: Data da ocorrência a ser atualizada (formato: YYYY-MM-DD)
        - payload: Dados para atualização (local e/ou data)
    
    Apenas o proprietário do evento pode atualizar suas ocorrências.
    """
    try:
        ocorrencia_atualizada = service_events.atualizar_ocorrencia_evento_por_data(
            db=db,
            id_evento=id_evento,
            date=date,
            payload=payload,
            current_user_email=current_user_email
        )
        return ocorrencia_atualizada
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao atualizar ocorrência: {str(e)}"
        )
        
#curl -X 'PUT' \
#  'http://localhost:8000/api/events/9/2025-12-01' \
#  -H 'accept: application/json' \
#  -H 'Content-Type: application/json' \
#  -d '{
#  "local": "string",
#  "data": "2025-12-09T14:38:52.293Z"
#}'

@router.delete("/{id_evento}/{date}", status_code=status.HTTP_200_OK)
def cancelar_ocorrencia_evento_data(
    id_evento: int, 
    date: date, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(service_auth.get_current_user_email)
):
    """
    Cancela (deleta) uma ocorrência específica de um evento.
    
    Parâmetros:
        - id_evento: ID do evento
        - date: Data da ocorrência a ser cancelada (formato: YYYY-MM-DD)
    
    Apenas o proprietário do evento pode cancelar suas ocorrências.
    """
    try:
        resultado = service_events.cancelar_ocorrencia_evento_por_data(
            db=db,
            id_evento=id_evento,
            date=date,
            current_user_email=current_user_email
        )
        return resultado
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao cancelar ocorrência: {str(e)}"
        )
    
    