from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from ..core.config import settings
from ..database.connection import get_db 
from ..services import service_events
from ..schemas import schema

router = APIRouter(prefix=f"{settings.API_V1_STR.rstrip('/')}/events", tags=["Eventos"])

@router.post("/", 
             response_model=schema.EventoResponse, 
             status_code=status.HTTP_201_CREATED)
def criar_evento(
    dados: schema.EventoCreate,
    disciplina: schema.DisciplinaCreate = None,
    db: Session = Depends(get_db)
):
    try:
        # Delega a lógica para o service
        novo_evento = service_events.criar_evento_logica(db=db, dados=dados, disciplina=disciplina)
        return novo_evento
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao criar evento: {str(e)}"
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