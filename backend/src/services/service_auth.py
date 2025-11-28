from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from ..core.config import settings
# Ajuste os imports abaixo conforme a estrutura das suas pastas
from ..schemas import schema
from ..models import models
from ..core import security # Importa seu arquivo com passlib
from ..schemas.jwt import Token, TokenPayload

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

def autenticar_usuario(db: Session, email: str, senha: str):
    """Verifica credenciais e retorna o usuário se autenticado, ou None."""
    user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not user:
        return None
    if not security.verificar_senha(senha, user.senha):
        return None
    return user 


def login_user(db: Session, email: str, password: str) -> Token:
    """Autentica um usuário e retorna um Token Pydantic (access + refresh).

    Usa `autenticar_usuario` para validar credenciais e, em caso de sucesso,
    gera tokens onde `sub` é o email do usuário (por decisão do time).
    """
    user = autenticar_usuario(db=db, email=email, senha=password)
    if not user:
        return None

    # Determina a tag para o frontend com base no e-mail:
    # - se o email contiver a substring "@aluno." => tag 'aluno'
    # - caso contrário => tag 'professor'
    # (pedido: não usar relações do ORM aqui, usar apenas o email)
    if "@aluno." in user.email:
        tag = 'aluno'
    else:
        tag = 'professor'

    access_token = security.create_access_token(subject=str(user.email), tag=tag)
    refresh_token = security.create_refresh_token(subject=str(user.email), tag=tag)
    return Token(access_token=access_token, refresh_token=refresh_token)


def login_university(university: models.Universidade, password: str | None = None) -> Token:
    """Autentica (ou emite token) para uma Universidade.

    O model `Universidade` possui campo `senha` armazenado como hash; por isso
    esta função requer a senha em texto plano para verificação via
    `security.verificar_senha` e, em caso de sucesso, emite tokens com
    `sub` = university.email.
    """
    # Requeremos password em texto plano para verificação.
    if password is None:
        return None

    # Verifica a senha (sempre como hash armazenado no banco).
    if not security.verificar_senha(password, university.senha):
        return None

    # Marca token com tag 'universidade' para o frontend
    access_token = security.create_access_token(subject=str(university.email), tag='universidade')
    refresh_token = security.create_refresh_token(subject=str(university.email), tag='universidade')
    return Token(access_token=access_token, refresh_token=refresh_token)

def criar_usuario_base(db: Session, dados):
    """
    Função auxiliar que insere o Usuário na tabela pai (Usuario).
    Realiza verificações de duplicidade e hash de senha.
    Retorna a instância do usuário (com ID gerado pelo flush).
    """
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
            id_usuario=novo_usuario.id,
            id_universidade=dados.idUniversidade,
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
            id_usuario=novo_usuario.id,
            id_curso=dados.idCurso,
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


def criar_universidade(db: Session, dados):
    """Cria uma Universidade e salva a senha já hasheada.

    Recebe um Pydantic `UniversidadeCreate` (ou similar) com campo `senha`.
    Garante unicidade de email/cnpj e salva o registro com hash da senha.
    Retorna o modelo `models.Universidade` persistido.
    """
    # Verifica duplicidade
    if db.query(models.Universidade).filter(models.Universidade.email == dados.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email da universidade já cadastrado.")
    if db.query(models.Universidade).filter(models.Universidade.cnpj == dados.cnpj).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CNPJ já cadastrado.")

    senha_para_salvar = security.pegar_senha_hash(dados.senha)

    try:
        nova_uni = models.Universidade(
            nome=dados.nome,
            sigla=dados.sigla,
            cnpj=dados.cnpj,
            email=dados.email,
            senha=senha_para_salvar
        )
        db.add(nova_uni)
        db.commit()
        db.refresh(nova_uni)
        return nova_uni
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar universidade: {str(e)}")

def criar_professor(db: Session, novo_usuario: models.Usuario, dados): 
    try:
        # models.Professor uses snake_case column names (id_usuario, id_universidade, data_admissao)
        novo_professor = models.Professor(
            id_usuario=novo_usuario.id,
            id_universidade=dados.idUniversidade,
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
        # models.Aluno defines id_usuario and id_curso (snake_case). Map incoming Pydantic fields
        # (which use camelCase) to the model column names here.
        novo_aluno = models.Aluno(
            id_usuario=novo_usuario.id,
            id_curso=dados.idCurso,
            matricula=dados.matricula
        )
        db.add(novo_aluno)
        db.commit()
        db.refresh(novo_usuario)
        return novo_usuario
    except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Erro ao registrar aluno: {str(e)}")
        
def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    """Valida o token de acesso e retorna o TokenPayload completo.

    Para endpoints que só precisam do email, use o wrapper `get_current_user_email`.
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

    return payload


# Compatibilidade: wrapper que retorna apenas o email (sub) para callers antigos.
def get_current_user_email(payload: TokenPayload = Depends(get_current_user)) -> str:
    return payload.sub
