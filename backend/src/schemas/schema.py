from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime

# ==========================================
# UNIVERSIDADE
# ==========================================
class UniversidadeBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255)
    sigla: str = Field(..., max_length=20)
    cnpj: str = Field(..., max_length=14, description="Apenas números")
    email: Optional[EmailStr] = None

class UniversidadeCreate(UniversidadeBase):
    pass

class UniversidadeResponse(UniversidadeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# CURSO
# ==========================================
class CursoBase(BaseModel):
    nome: str = Field(..., max_length=255)
    sigla: str = Field(..., max_length=10)
    email: Optional[EmailStr] = None
    id_universidade: int
    graduacao: Optional[bool] = None

class CursoCreate(CursoBase):
    pass

class CursoResponse(CursoBase):
    id: int
    # Opcional: incluir nome da universidade na resposta
    # universidade: Optional[UniversidadeResponse] = None 
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# USUÁRIO (Base para Aluno e Professor)
# ==========================================
class UsuarioBase(BaseModel):
    nome: str = Field(..., max_length=255)
    email: EmailStr
    cpf: str = Field(..., min_length=11, max_length=11, description= "apenas numeros")

# 1. BASE: Schema com a Senha (Comum a ambos os novos registros)
class UsuarioBaseRegister(UsuarioBase):
    """
    Base para todos os schemas de registro. Inclui a senha.
    """
    senha: str = Field(..., min_length=6, description="Senha de acesso")

# 2. NOVO SCHEMA PARA PROFESSOR (Campos obrigatórios)
class RegistroProfessor(UsuarioBaseRegister):
    """
    Schema exclusivo para o registro de Professor. 
    Campos específicos são OBRIGATÓRIOS (sem Optional).
    """
    id_universidade: int # OBRIGATÓRIO no endpoint de Professor


# 3. NOVO SCHEMA PARA ALUNO (Campos obrigatórios)
class RegistroAluno(UsuarioBaseRegister):
    """
    Schema exclusivo para o registro de Aluno.
    Campos específicos são OBRIGATÓRIOS (sem Optional).
    """
    id_curso: int # OBRIGATÓRIO no endpoint de Aluno
    matricula: str = Field(..., max_length=7, description="Matrícula do aluno")

# 4. Schemas Antigos (Manutenção/Remoção)
# Você pode remover a classe UsuarioRegistro, pois ela será substituída por RegistroProfessor e RegistroAluno
# class UsuarioRegistro(UsuarioBase): # <- REMOVER OU COMENTAR
# ...

class UsuarioResponse(UsuarioBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# EVENTO
# ==========================================
class EventoBase(BaseModel):
    nome: str = Field(..., max_length=255)
    descricao: Optional[str] = Field(None, max_length=500)
    id_universidade: int
    data_inicio: datetime
    data_termino: datetime
    recorrencia: Optional[str] = None
    categoria: Optional[str] = None
    email_proprietario: Optional[str] = None # ID do Usuário dono

class EventoCreate(EventoBase):
    pass

class EventoResponse(EventoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# DISCIPLINA
# ==========================================
class DisciplinaBase(BaseModel):
    id_evento: int # PK e FK ao mesmo tempo
    id_professor: int
    horario: str = Field(..., max_length=10)
    nome: str = Field(..., max_length=255)

class DisciplinaCreate(DisciplinaBase):
    pass

class DisciplinaResponse(DisciplinaBase):
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# DIAS DA DISCIPLINA
# ==========================================
class DiasDisciplinaBase(BaseModel):
    id_disciplina: int
    dia: str

class DiasDisciplinaCreate(DiasDisciplinaBase):
    pass

class DiasDisciplinaResponse(DiasDisciplinaBase):
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# CURSO DISCIPLINA (Associação)
# ==========================================
class CursoDisciplinaBase(BaseModel):
    id_curso: int
    id_disciplina: int
    creditos: int

class CursoDisciplinaCreate(CursoDisciplinaBase):
    pass

class CursoDisciplinaResponse(CursoDisciplinaBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# OCORRÊNCIA EVENTO
# ==========================================
class OcorrenciaEventoBase(BaseModel):
    id_evento: int
    local: str = Field(..., max_length=255)
    data: datetime

class OcorrenciaEventoCreate(OcorrenciaEventoBase):
    pass

class OcorrenciaEventoResponse(OcorrenciaEventoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# NOTIFICAÇÃO
# ==========================================
class NotificacaoBase(BaseModel):
    id_usuario: int
    data: datetime
    evento: str
    mensagem: Optional[str] = None

class NotificacaoCreate(NotificacaoBase):
    pass

class NotificacaoResponse(NotificacaoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# CONVIDADO
# ==========================================
class ConvidadoBase(BaseModel):
    id_evento: int
    id_usuario: int
    status_vinculo: str

class ConvidadoCreate(ConvidadoBase):
    pass

class ConvidadoResponse(ConvidadoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# PRESENÇA
# ==========================================
class PresencaBase(BaseModel):
    id_ocorrenciaEvento: int
    id_aluno: int
    presente: bool = False

class PresencaCreate(PresencaBase):
    pass

class PresencaResponse(PresencaBase):
    id: int
    model_config = ConfigDict(from_attributes=True)