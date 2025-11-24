from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .config import settings
# Ajuste os imports abaixo conforme a estrutura das suas pastas
from ..models import models
from ..core import security # Importa seu arquivo com passlib

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def buscar_usuario_por_email_ou_cpf(db: Session, email: str, cpf: str):
    return db.query(models.Usuario).filter(
        (models.Usuario.email == email) | (models.Usuario.cpf == cpf)
    ).first()

def registrar_usuario_automatico(db: Session, dados):
    # 1. Verifica duplicidade
    db_user = buscar_usuario_por_email_ou_cpf(db, dados.email, dados.cpf)
    if db_user:
        if db_user.email == dados.email:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já cadastrado.")
        if db_user.cpf == dados.cpf:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CPF já cadastrado.")

    # 2. Gera o Hash da senha usando seu arquivo security
    senha_hash_gerada = security.pegar_senha_hash(dados.senha)
    email = dados.email
    
    try:
        # 3. Cria o Usuário (Agora salvando a senha corretamente)
        novo_usuario = models.Usuario(
            email=dados.email,
            nome=dados.nome,
            cpf=dados.cpf,
            senha=senha_hash_gerada  # Mapeando para a coluna 'senha' do seu model
        )
        db.add(novo_usuario)
        db.flush() # Gera o ID do usuário

        # 4. Define se é Aluno ou Professor
        if email.endswith('@aluno.uece.br'):
            if not dados.matricula or not dados.idCurso:
                 raise HTTPException(status_code=400, detail="Alunos precisam de matricula e idCurso.")
            return criar_aluno(db, novo_usuario, dados) 

        elif email.endswith('@uece.br') and not email.endswith('@aluno.uece.br'):
            if not dados.idUniversidade:
                raise HTTPException(status_code=400, detail="Professores precisam de idUniversidade.")
            return criar_professor(db, novo_usuario, dados)

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Domínio de e-mail inválido. Use @aluno.uece.br ou @uece.br."
            )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha na transação de registro: {str(e)}"
        )

def criar_professor(db: Session, novo_usuario: models.Usuario, dados): 
    try:
        novo_professor = models.Professor(
            idUsuario=novo_usuario.id,
            idUniversidade=dados.idUniversidade,
            dataAdmissao=dados.dataAdmissao,
            titulacao=dados.titulacao # Agora salva a titulação!
        )
        db.add(novo_professor)
        
        db.commit()
        db.refresh(novo_usuario)
        return novo_usuario
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao registrar professor: {str(e)}")
    
def criar_aluno(db: Session, novo_usuario: models.Usuario, dados):
    # Verifica unicidade da matrícula
    if db.query(models.Aluno).filter(models.Aluno.matricula == dados.matricula).first():
          db.rollback()
          raise HTTPException(status_code=400, detail="Matrícula já cadastrada.")
          
    try:
        novo_aluno = models.Aluno(
            idUsuario=novo_usuario.id,
            idCurso=dados.idCurso,
            matricula=dados.matricula
        )
        db.add(novo_aluno)
        db.commit()
        db.refresh(novo_usuario)
        return novo_usuario
    except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Erro ao registrar aluno: {str(e)}")
        
def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Valida o token de acesso e retorna o email do usuário presente em `sub`.

    Esta função NÃO consulta o banco: ela apenas valida o JWT (assinatura/expiração)
    e extrai o campo `sub` (assumido como email). Endpoints protegidos podem usar
    esse email para buscar o usuário no banco se necessário.
    """
    payload = security.decode_token(token)

    if not payload or not payload.sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload.sub
