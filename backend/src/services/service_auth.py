# ...existing code...
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from ..core.config import settings
from ..schemas import schema
from ..models import models
from ..core import security
from ..schemas.jwt import Token, TokenPayload
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
from datetime import datetime, timedelta
import uuid

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Store reset codes by code -> { email, expires_at, attempts }
reset_codes = {}
# Temporary recovery tokens by token -> { email, expires_at }
recovery_tokens = {}

# ----------------------------------------------------------------------
# ENVIAR EMAIL DE BOAS-VINDAS (PORTUGUÊS)
# ----------------------------------------------------------------------
def send_welcome_email(email: str, name: str, role: str):
    """Envia um email de boas-vindas simples."""
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USER
        msg['To'] = email
        msg['Subject'] = "Bem-vindo ao Agendai "

        role_pt = "professor" if role == "professor" else "aluno"
        
        body = f"""Olá {name},

Bem-vindo ao Agendai APS! Sua conta de {role_pt} foi criada com sucesso.

Você já pode fazer login no sistema.

Atenciosamente,
Equipe Agendai """
        
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        # Log e continua; não interrompe a criação do usuário
        print(f"Erro ao enviar email de boas-vindas: {e}")

# ----------------------------------------------------------------------
# RECUPERAÇÃO DE SENHA (PORTUGUÊS)
# ----------------------------------------------------------------------
def request_password_reset(db: Session, email: str):
    """Gera um código de 6 dígitos e envia para o email do usuário."""
    user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email não cadastrado.")

    code = ''.join(random.choices(string.digits, k=6))
    expires = datetime.utcnow() + timedelta(minutes=15)

    # Salva pelo código para que o cliente envie apenas o código no passo 2
    reset_codes[code] = {"email": email, "expires_at": expires, "attempts": 0}

    try:
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USER
        msg['To'] = email
        msg['Subject'] = "Código de Recuperação de Senha - Agendai "

        body = f"""Olá {user.nome},

Você solicitou a recuperação de senha para o Agendai APS.

Seu código de recuperação é: {code}

Este código expira em 15 minutos.

Se você não solicitou esta recuperação, por favor ignore este email.

Atenciosamente,
Equipe Agendai """
        
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()

        return {"message": "Código de recuperação enviado para seu email."}
    except Exception as e:
        print(f"Erro ao enviar email de recuperação: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao enviar email.")

def validate_reset_code(code: str):
    """
    Valida o código de 6 dígitos.
    Entrada: apenas `code` (sem email).
    Em caso de sucesso retorna um token de recuperação temporário (use-o para definir a nova senha).
    """
    if code not in reset_codes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Não há solicitação de recuperação ativa para este código.")

    record = reset_codes[code]

    if datetime.utcnow() > record["expires_at"]:
        del reset_codes[code]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código expirado.")

    if record["attempts"] >= 3:
        del reset_codes[code]
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Muitas tentativas. Solicite um novo código.")

    # Código válido: emite um token de recuperação único e remove/reseta o código
    token = str(uuid.uuid4())
    recovery_tokens[token] = {"email": record["email"], "expires_at": datetime.utcnow() + timedelta(minutes=15)}

    # Remove o código usado para evitar reutilização
    del reset_codes[code]

    return {"recovery_token": token, "message": "Código validado. Use o token de recuperação para redefinir sua senha."}

def reset_password_with_token(db: Session, recovery_token: str, new_password: str, confirm_password: str):
    """
    Redefine a senha do usuário usando um token de recuperação único.
    Cliente deve enviar o token retornado por validate_reset_code.
    """
    # Valida se as senhas coincidem
    if new_password != confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="As senhas não coincidem.")
    
    # Valida tamanho mínimo da senha
    if len(new_password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A senha deve ter no mínimo 6 caracteres.")
    
    if recovery_token not in recovery_tokens:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token de recuperação inválido ou expirado.")

    rec = recovery_tokens[recovery_token]
    if datetime.utcnow() > rec["expires_at"]:
        del recovery_tokens[recovery_token]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token de recuperação expirado.")

    email = rec["email"]
    user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not user:
        del recovery_tokens[recovery_token]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    try:
        hashed = security.pegar_senha_hash(new_password)
        user.senha = hashed
        db.commit()
        del recovery_tokens[recovery_token]
        return {"message": "Senha atualizada com sucesso."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Falha ao redefinir senha: {str(e)}")

# ----------------------------------------------------------------------
# Funções auxiliares restantes (inalteradas, mantém nomes originais)
# ----------------------------------------------------------------------
def buscar_usuario_por_email_ou_cpf(db: Session, email: str, cpf: str):
    return db.query(models.Usuario).filter(
        (models.Usuario.email == email) | (models.Usuario.cpf == cpf)
    ).first()

def buscar_aluno_por_matricula(db: Session, matricula: str):
    return db.query(models.Aluno).filter(models.Aluno.matricula == matricula).first()

def autenticar_usuario(db: Session, email: str, senha: str):
    user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not user:
        return None
    if not security.verificar_senha(senha, user.senha):
        return None
    return user

def login_user(db: Session, email: str, password: str) -> Token:
    user = autenticar_usuario(db=db, email=email, senha=password)
    if not user:
        return None
    if "@aluno." in user.email:
        tag = 'aluno'
    else:
        tag = 'professor'
    access_token = security.create_access_token(subject=str(user.email), tag=tag)
    refresh_token = security.create_refresh_token(subject=str(user.email), tag=tag)
    return Token(access_token=access_token, refresh_token=refresh_token)

def login_university(university: models.Universidade, password: str | None = None) -> Token:
    if password is None:
        return None
    if not security.verificar_senha(password, university.senha):
        return None
    access_token = security.create_access_token(subject=str(university.email), tag='universidade')
    refresh_token = security.create_refresh_token(subject=str(university.email), tag='universidade')
    return Token(access_token=access_token, refresh_token=refresh_token)

def criar_usuario_base(db: Session, dados):
    db_user = buscar_usuario_por_email_ou_cpf(db, dados.email, dados.cpf)
    if db_user:
        if db_user.email == dados.email:
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já cadastrado.")
        if db_user.cpf == dados.cpf:
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CPF já cadastrado.")
    senha_hash_gerada = security.pegar_senha_hash(dados.senha)
    novo_usuario = models.Usuario(
        email=dados.email,
        nome=dados.nome,
        cpf=dados.cpf,
        senha=senha_hash_gerada
    )
    db.add(novo_usuario)
    db.flush()
    return novo_usuario

def registrar_professor(db: Session, dados: schema.RegistroProfessor):
    try:
        novo_usuario = criar_usuario_base(db, dados)
        novo_professor = models.Professor(
            id_usuario=novo_usuario.id,
            id_universidade=dados.id_universidade,
        )
        db.add(novo_professor)
        db.commit()
        db.refresh(novo_usuario)
        send_welcome_email(novo_usuario.email, novo_usuario.nome, "professor")
        return novo_usuario
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Falha ao registrar professor: {str(e)}")

def registrar_aluno(db: Session, dados: schema.RegistroAluno):
    if buscar_aluno_por_matricula(db, dados.matricula):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Matrícula já existe.")
    try:
        novo_usuario = criar_usuario_base(db, dados)
        novo_aluno = models.Aluno(
            id_usuario=novo_usuario.id,
            id_curso=dados.id_curso,
            matricula=dados.matricula
        )
        db.add(novo_aluno)
        db.commit()
        db.refresh(novo_usuario)
        send_welcome_email(novo_usuario.email, novo_usuario.nome, "aluno")
        return novo_usuario
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Falha ao registrar aluno: {str(e)}")

def criar_universidade(db: Session, dados):
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

def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    payload = security.decode_token(token)
    if not payload or not payload.sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não foi possível validar as credenciais", headers={"WWW-Authenticate": "Bearer"})
    if payload.type != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tipo de token inválido", headers={"WWW-Authenticate": "Bearer"})
    return payload

def get_current_user_email(payload: TokenPayload = Depends(get_current_user)) -> str:
    return payload.sub