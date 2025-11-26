from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from ..database.connection import get_db 
from ..services import service_evento # Supondo que você criou este arquivo
from ..schemas import schema

router = APIRouter(prefix="/eventos", tags=["Eventos"])

@router.post("/", 
             response_model=schema.EventoResponse, 
             status_code=status.HTTP_201_CREATED)
def criar_evento(
    dados: schema.EventoCreate,
    db: Session = Depends(get_db)
):
    try:
        # Delega a lógica para o service
        novo_evento = service_evento.criar_evento_logica(db=db, dados=dados)
        return novo_evento
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao criar evento: {str(e)}"
        )