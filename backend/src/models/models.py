from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# --- DEFINIÇÃO DAS CLASSES (snake_case e sem acentos) ---

class Universidade(Base):
    __tablename__ = "universidade"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255))
    sigla = Column(String(20))
    cnpj = Column(String(14), unique=True)
    email = Column(String(255), unique=True)
    senha = Column(String(255))

    # Relationships
    cursos = relationship("Curso", back_populates="universidade")
    professores = relationship("Professor", back_populates="universidade")
    eventos = relationship("Evento", back_populates="universidade")


class Curso(Base):
    __tablename__ = "curso"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_universidade = Column(Integer, ForeignKey("universidade.id"))
    nome = Column(String(255))
    sigla = Column(String(10))
    email = Column(String(255), unique=True)

    # Relationships
    universidade = relationship("Universidade", back_populates="cursos")
    alunos = relationship("Aluno", back_populates="curso")
    curso_disciplina = relationship("CursoDisciplina", back_populates="curso")


class Usuario(Base):
    __tablename__ = "usuario"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255))
    email = Column(String(255), unique=True)
    cpf = Column(String(11), unique=True)
    senha = Column(String(255))

    # Relationships
    aluno = relationship("Aluno", back_populates="usuario", uselist=False)
    professor = relationship("Professor", back_populates="usuario", uselist=False)
    notificacoes = relationship("Notificacao", back_populates="usuario")
    convidados = relationship("Convidado", back_populates="usuario")
    eventos = relationship("Evento", back_populates="usuario")


class Aluno(Base):
    __tablename__ = "aluno"
    
    id_usuario = Column(Integer, ForeignKey("usuario.id"), primary_key=True)
    id_curso = Column(Integer, ForeignKey("curso.id"))
    matricula = Column(String(7), unique=True)

    # Relationships
    usuario = relationship("Usuario", back_populates="aluno")
    curso = relationship("Curso", back_populates="alunos")
    presencas = relationship("Presenca", back_populates="aluno")


class Professor(Base):
    __tablename__ = "professor"
    
    id_usuario = Column(Integer, ForeignKey("usuario.id"), primary_key=True)
    id_universidade = Column(Integer, ForeignKey("universidade.id"))
    data_admissao = Column(Date)
    titulacao = Column(String(255))

    # Relationships
    usuario = relationship("Usuario", back_populates="professor")
    universidade = relationship("Universidade", back_populates="professores")
    disciplinas = relationship("Disciplina", back_populates="professor")


class Notificacao(Base):
    __tablename__ = "notificacao"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id"))
    data = Column(DateTime)
    mensagem = Column(String(255))

    # Relationships
    usuario = relationship("Usuario", back_populates="notificacoes")


class Evento(Base):
    __tablename__ = "evento"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_universidade = Column(Integer, ForeignKey("universidade.id"))
    data_inicio = Column(DateTime)
    data_termino = Column(DateTime)
    recorrencia = Column(String(255))  # ex: "Semanal", "Diário", "Diário (Dias úteis)"
    categoria = Column(String(255))
    id_proprietario = Column(Integer, ForeignKey("usuario.id"))

    # Relationships
    usuario = relationship("Usuario", back_populates="eventos")
    universidade = relationship("Universidade", back_populates="eventos")
    ocorrencias = relationship("OcorrenciaEvento", back_populates="evento")
    disciplina = relationship("Disciplina", back_populates="evento", uselist=False)
    convidados = relationship("Convidado", back_populates="evento")


class Disciplina(Base):
    __tablename__ = "disciplina"
    
    id_evento = Column(Integer, ForeignKey("evento.id"), primary_key=True)
    id_professor = Column(Integer, ForeignKey("professor.id_usuario"))
    horario = Column(String(10))
    nome = Column(String(255))

    # Relationships
    evento = relationship("Evento", back_populates="disciplina")
    professor = relationship("Professor", back_populates="disciplinas")
    disciplina_dias = relationship("DisciplinaDias", back_populates="disciplina")
    curso_disciplina = relationship("CursoDisciplina", back_populates="disciplina")


class DisciplinaDias(Base):
    __tablename__ = "disciplina_dias"
    
    id_disciplina = Column(Integer, ForeignKey("disciplina.id_evento"), primary_key=True)
    dia = Column(String(10), primary_key=True)

    disciplina = relationship("Disciplina", back_populates="disciplina_dias")


class CursoDisciplina(Base):
    __tablename__ = "curso_disciplina"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_curso = Column(Integer, ForeignKey("curso.id"))
    id_disciplina = Column(Integer, ForeignKey("disciplina.id_evento"))
    creditos = Column(Integer)

    curso = relationship("Curso", back_populates="curso_disciplina")
    disciplina = relationship("Disciplina", back_populates="curso_disciplina")


class OcorrenciaEvento(Base):
    __tablename__ = "ocorrencia_evento"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_evento = Column(Integer, ForeignKey("evento.id"))
    local = Column(String(255))
    data = Column(DateTime)

    evento = relationship("Evento", back_populates="ocorrencias")
    presencas = relationship("Presenca", back_populates="ocorrencia_evento")


class Convidado(Base):
    __tablename__ = "convidado"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_evento = Column(Integer, ForeignKey("evento.id"))
    id_usuario = Column(Integer, ForeignKey("usuario.id"))
    status_vinculo = Column(String(255))

    evento = relationship("Evento", back_populates="convidados")
    usuario = relationship("Usuario", back_populates="convidados")


class Presenca(Base):
    __tablename__ = "presenca"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_ocorrencia_evento = Column(Integer, ForeignKey("ocorrencia_evento.id"))
    id_aluno = Column(Integer, ForeignKey("aluno.id_usuario"))
    presente = Column(Boolean)

    ocorrencia_evento = relationship("OcorrenciaEvento", back_populates="presencas")
    aluno = relationship("Aluno", back_populates="presencas")
