from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, ForeignKey
import sqlalchemy as db
from sqlalchemy.orm import relationship, declarative_base
import sqlalchemy as db 

Base = declarative_base()

# --- DEFINIÇÃO DAS CLASSES (sem acentos) ---


class Universidade(Base):
    __tablename__ = "universidade"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True) 
    nome = db.Column(db.String(255))
    sigla = db.Column(db.String(20))
    cnpj = db.Column(db.String(14), unique=True) 
    email = db.Column(db.String(255), unique=True)  
    senha = db.Column(db.String(255))

    # Relationships
    cursos = relationship("Curso", back_populates="universidade")
    professores = relationship("Professor", back_populates="universidade")
    eventos = relationship("Evento", back_populates="universidade")


class Curso(Base):
    __tablename__ = "curso"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Mudança: idUniversidade -> id_universidade
    id_universidade = db.Column(db.Integer, ForeignKey("universidade.id"))
    nome = db.Column(db.String(255))
    sigla = db.Column(db.String(10))
    email = db.Column(db.String(255), unique=True)
    graduacao = db.Column(db.Boolean)

    # Relationships
    universidade = relationship("Universidade", back_populates="cursos")
    alunos = relationship("Aluno", back_populates="curso")
    curso_disciplina = relationship("CursoDisciplina", back_populates="curso")


class Usuario(Base):
    __tablename__ = "usuario"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    cpf = db.Column(db.String(11), unique=True)
    senha = db.Column(db.String(255))

    # Relationships
    aluno = relationship("Aluno", back_populates="usuario", uselist=False)
    professor = relationship("Professor", back_populates="usuario", uselist=False)
    notificacao = relationship("Notificacao", back_populates="usuario")
    convidado = relationship("Convidado", back_populates="usuario")
    eventos = relationship("Evento", back_populates="usuario")


class Aluno(Base):
    __tablename__ = "aluno"
    
    # Mudança: idUsuario -> id_usuario
    id_usuario = db.Column(db.Integer, ForeignKey("usuario.id"), primary_key=True)
    id_curso = db.Column(db.Integer, ForeignKey("curso.id"))
    matricula = db.Column(db.String(7)) # Removido acento de "mátricula"

    # Relationships
    usuario = relationship("Usuario", back_populates="aluno")
    curso = relationship("Curso", back_populates="alunos")
    presencas = relationship("Presenca", back_populates="aluno")


class Professor(Base):
    __tablename__ = "professor"
    
    id_usuario = db.Column(db.Integer, ForeignKey("usuario.id"), primary_key=True)
    id_universidade = db.Column(db.Integer, ForeignKey("universidade.id"))

    # Relationships
    usuario = relationship("Usuario", back_populates="professor")
    universidade = relationship("Universidade", back_populates="professores")
    disciplinas = relationship("Disciplina", back_populates="professor")


class Notificacao(Base):
    __tablename__ = "notificacao" # Notificação -> notificacao
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, ForeignKey("usuario.id"))
    data = db.Column(db.DateTime)
    mensagem = db.Column("mensagem", db.String(255))
    evento = db.Column("evento", db.String(255)) # Mudei nome da coluna pra evitar conflito com a tabela Evento, mas mantive string original se preferir

    # Relationships
    usuario = relationship("Usuario", back_populates="notificacao")


class Evento(Base):
    __tablename__ = "evento"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255))
    descricao = db.Column(db.String(500))
    id_universidade = db.Column(db.Integer, ForeignKey("universidade.id"))
    data_inicio = db.Column(db.DateTime)
    data_termino = db.Column(db.DateTime)
    recorrencia = db.Column(db.String(255))
    categoria = db.Column(db.String(255))
    email_proprietario = db.Column(db.String(255), ForeignKey("usuario.email")) # idproprietário -> id_proprietario

    # Relationships
    usuario = relationship("Usuario", back_populates="eventos")
    universidade = relationship("Universidade", back_populates="eventos")
    ocorrencia_evento = relationship("OcorrenciaEvento", back_populates="evento")
    disciplina = relationship("Disciplina", back_populates="evento", uselist=False)
    convidados = relationship("Convidado", back_populates="evento")


class Disciplina(Base):
    __tablename__ = "disciplina"
    
    id_evento = db.Column(db.Integer, ForeignKey("evento.id"), primary_key=True)
    id_professor = db.Column(db.Integer, ForeignKey("professor.id_usuario"))
    horario = db.Column(db.String(255))
    nome = db.Column(db.String(255))

    # Relationships
    evento = relationship("Evento", back_populates="disciplina")
    professor = relationship("Professor", back_populates="disciplinas")
    disciplina_dias = relationship("DisciplinaDias", back_populates="disciplina")
    curso_disciplina = relationship("CursoDisciplina", back_populates="disciplina")


class DisciplinaDias(Base):
    __tablename__ = "disciplina_dias"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_disciplina = db.Column(db.Integer, ForeignKey("disciplina.id_evento"), nullable=False)
    dia = db.Column(db.String(10), nullable=False)

    # Relationships
    disciplina = relationship("Disciplina", back_populates="disciplina_dias")


class CursoDisciplina(Base):
    __tablename__ = "curso_disciplina"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_curso = db.Column(db.Integer, ForeignKey("curso.id"))
    id_disciplina = db.Column(db.Integer, ForeignKey("disciplina.id_evento"))
    creditos = db.Column(db.Integer)

    # Relationships
    curso = relationship("Curso", back_populates="curso_disciplina")
    disciplina = relationship("Disciplina", back_populates="curso_disciplina")


class OcorrenciaEvento(Base):
    __tablename__ = "ocorrencia_evento" # OcorrênciaEvento -> ocorrencia_evento
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_evento = db.Column(db.Integer, ForeignKey("evento.id"))
    local = db.Column(db.String(255))
    data = db.Column(db.DateTime)

    # Relationships
    evento = relationship("Evento", back_populates="ocorrencia_evento")
    presenca = relationship("Presenca", back_populates="ocorrencia_evento")


class Convidado(Base):
    __tablename__ = "convidado"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_evento = db.Column(db.Integer, ForeignKey("evento.id"))
    id_usuario = db.Column(db.Integer, ForeignKey("usuario.id"))
    status_vinculo = db.Column(db.String(255))

    # Relationships
    evento = relationship("Evento", back_populates="convidados")
    usuario = relationship("Usuario", back_populates="convidado")


class Presenca(Base):
    __tablename__ = "presenca" # Presença -> presenca
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_ocorrencia_evento = db.Column(db.Integer, ForeignKey("ocorrencia_evento.id"))
    id_aluno = db.Column(db.Integer, ForeignKey("aluno.id_usuario"))
    presente = db.Column(db.Boolean)

    # Relationships
    ocorrencia_evento = relationship("OcorrenciaEvento", back_populates="presenca")
    aluno = relationship("Aluno", back_populates="presencas")
