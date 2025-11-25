from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from ..core.config import settings
# Ajuste os imports abaixo conforme a estrutura das suas pastas
from ..models import models
from ..core import security # Importa seu arquivo com passlib
from ..schemas.jwt import Token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def buscar_usuario_por_email_ou_cpf(db: Session, email: str, cpf: str):
    return db.query(models.Usuario).filter(
        (models.Usuario.email == email) | (models.Usuario.cpf == cpf)
    ).first()


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

    access_token = security.create_access_token(subject=str(user.email))
    refresh_token = security.create_refresh_token(subject=str(user.email))
    return Token(access_token=access_token, refresh_token=refresh_token)


def login_university(university: models.Universidade, password: str | None = None) -> Token:
    """Autentica (ou emite token) para uma Universidade.

    Atualmente o model `Universidade` não tem campo de senha — por isso esta
    função apenas emite tokens com `sub` = university.email. Isso deve ser
    ajustado se for necessária autenticação (ex: adicionar credencial ou
    buscar um usuário admin associado à universidade).
    """
    # Agora a Universidade tem campo `senha`. Requeremos password e validamos.
    if password is None:
        return None

    # Se não houver senha cadastrada neste registro, não autenticamos.
    if not getattr(university, 'senha', None):
        return None

    # If plaintext mode is enabled, compare raw; otherwise verify hash.
    if settings.ALLOW_PLAINTEXT_PASSWORDS:
        if university.senha != password:
            return None
    else:
        if not security.verificar_senha(password, university.senha):
            return None

    access_token = security.create_access_token(subject=str(university.email))
    refresh_token = security.create_refresh_token(subject=str(university.email))
    return Token(access_token=access_token, refresh_token=refresh_token)

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

    # Decide whether to store raw password or hash based on settings
    if settings.ALLOW_PLAINTEXT_PASSWORDS:
        senha_para_salvar = dados.senha
    else:
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
