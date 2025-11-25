from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from ..core.config import settings
# Ajuste os imports abaixo conforme a estrutura das suas pastas
from ..schemas import schema
from ..models import models
from ..core import security # Importa seu arquivo com passlib

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# ----------------------------------------------------------------------
# FUNÇÕES AUXILIARES DE BUSCA
# ----------------------------------------------------------------------
def buscar_usuario_por_email_ou_cpf(db: Session, email: str, cpf: str):
    return db.query(models.Usuario).filter(
        (models.Usuario.email == email) | (models.Usuario.cpf == cpf)
    ).first()

def buscar_aluno_por_matricula(db: Session, matricula: str):
    return db.query(models.Aluno).filter(models.Aluno.matricula == matricula).first()

# ----------------------------------------------------------------------
# FUNÇÃO GENÉRICA: CRIAR USUÁRIO BASE
# ----------------------------------------------------------------------
def criar_usuario_base(db: Session, dados):
    """
    Função auxiliar que insere o Usuário na tabela pai (Usuario).
    Realiza verificações de duplicidade e hash de senha.
    Retorna a instância do usuário (com ID gerado pelo flush).
    """
    # 1. Verifica duplicidade de Email ou CPF
    db_user = buscar_usuario_por_email_ou_cpf(db, dados.email, dados.cpf)
    if db_user:
        if db_user.email == dados.email:
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já cadastrado.")
        if db_user.cpf == dados.cpf:
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CPF já cadastrado.")

    # 2. Gera o Hash da senha
    senha_hash_gerada = security.pegar_senha_hash(dados.senha)
    
    # 3. Cria o objeto Usuario
    novo_usuario = models.Usuario(
        email=dados.email,
        nome=dados.nome,
        cpf=dados.cpf,
        senha=senha_hash_gerada
    )
    
    db.add(novo_usuario)
    db.flush() # Gera o ID do usuário para ser usado nas tabelas filhas
    
    return novo_usuario

# ----------------------------------------------------------------------
# FUNÇÃO 1: REGISTRO DE PROFESSOR
# ----------------------------------------------------------------------
def registrar_professor(db: Session, dados: schema.RegistroProfessor):
    try:
        # 1. Chama a função genérica para criar o usuário base
        novo_usuario = criar_usuario_base(db, dados)

        # 2. Cria o registro específico de Professor
        novo_professor = models.Professor(
            idUsuario=novo_usuario.id,
            idUniversidade=dados.idUniversidade,
            dataAdmissao=dados.dataAdmissao,
            titulacao=dados.titulacao
        )
        db.add(novo_professor)
        
        # 3. Efetiva a transação
        db.commit()
        db.refresh(novo_usuario)
        return novo_usuario
        
    except HTTPException:
        db.rollback()
        raise # Relança erros HTTP (como duplicidade)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao registrar professor: {str(e)}"
        )

# ----------------------------------------------------------------------
# FUNÇÃO 2: REGISTRO DE ALUNO
# ----------------------------------------------------------------------
def registrar_aluno(db: Session, dados: schema.RegistroAluno):
    # 1. Verificação específica antes de criar qualquer coisa
    if buscar_aluno_por_matricula(db, dados.matricula):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Matrícula já cadastrada.")

    try:
        # 2. Chama a função genérica para criar o usuário base
        novo_usuario = criar_usuario_base(db, dados)

        # 3. Cria o registro específico de Aluno
        novo_aluno = models.Aluno(
            idUsuario=novo_usuario.id,
            idCurso=dados.idCurso,
            matricula=dados.matricula
        )
        db.add(novo_aluno)

        # 4. Efetiva a transação
        db.commit()
        db.refresh(novo_usuario)
        return novo_usuario
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao registrar aluno: {str(e)}"
        )
        
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
