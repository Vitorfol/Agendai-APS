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
    idUniversidade: int

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
    idUniversidade: int # OBRIGATÓRIO no endpoint de Professor


# 3. NOVO SCHEMA PARA ALUNO (Campos obrigatórios)
class RegistroAluno(UsuarioBaseRegister):
    """
    Schema exclusivo para o registro de Aluno.
    Campos específicos são OBRIGATÓRIOS (sem Optional).
    """
    idCurso: int # OBRIGATÓRIO no endpoint de Aluno
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
    idUniversidade: int
    dataInicio: datetime
    dataTermino: datetime
    recorrente: bool = False
    categoria: Optional[str] = None
    idProprietario: Optional[int] = None # ID do Usuário dono

class EventoCreate(EventoBase):
    pass

class EventoResponse(EventoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# DISCIPLINA
# ==========================================
class DisciplinaBase(BaseModel):
    idEvento: int # PK e FK ao mesmo tempo
    idProfessor: int
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
    idDisciplina: int
    dia: str

class DiasDisciplinaCreate(DiasDisciplinaBase):
    pass

class DiasDisciplinaResponse(DiasDisciplinaBase):
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# CURSO DISCIPLINA (Associação)
# ==========================================
class CursoDisciplinaBase(BaseModel):
    idCurso: int
    idDisciplina: int
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
    idEvento: int
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
    idUsuario: int
    data: datetime
    evento: str

class NotificacaoCreate(NotificacaoBase):
    pass

class NotificacaoResponse(NotificacaoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# CONVIDADO
# ==========================================
class ConvidadoBase(BaseModel):
    idEvento: int
    idUsuario: int
    statusVinculo: str

class ConvidadoCreate(ConvidadoBase):
    pass

class ConvidadoResponse(ConvidadoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# PRESENÇA
# ==========================================
class PresencaBase(BaseModel):
    idOcorrenciaEvento: int
    idAluno: int
    presente: bool = False

class PresencaCreate(PresencaBase):
    pass

class PresencaResponse(PresencaBase):
    id: int
    model_config = ConfigDict(from_attributes=True)