from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, declarative_base


Base = declarative_base()

# --- DEFINIÇÃO DAS CLASSES (sem acentos) ---


class Universidade(Base):
    __tablename__ = "Universidade"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255))
    sigla = Column(String(20))
    cnpj = Column(String(14), unique=True)
    email = Column(String(255), unique=True)
    senha = Column(String(255), nullable=True)

    cursos = relationship("Curso", back_populates="universidade")
    professores = relationship("Professor", back_populates="universidade")
    eventos = relationship("Evento", back_populates="universidade")


class Curso(Base):
    __tablename__ = "Curso"
    idUniversidade = Column(Integer, ForeignKey("Universidade.id"))
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255))
    sigla = Column(String(10))
    email = Column(String(255), unique=True)

    universidade = relationship("Universidade", back_populates="cursos")
    alunos = relationship("Aluno", back_populates="curso")
    cursoDisciplina = relationship("CursoDisciplina", back_populates="curso")


class Usuario(Base):
    __tablename__ = "Usuario"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255))
    email = Column(String(255), unique=True)
    cpf = Column(String(11), unique=True)
    senha = Column(String(255))

    aluno = relationship("Aluno", back_populates="usuario", uselist=False)
    professor = relationship("Professor", back_populates="usuario", uselist=False)
    notificacoes = relationship("Notificacao", back_populates="usuario")
    convidados = relationship("Convidado", back_populates="usuario")
    eventos = relationship("Evento", back_populates="usuario")


class Aluno(Base):
    __tablename__ = "Aluno"
    idUsuario = Column(Integer, ForeignKey("Usuario.id"), primary_key=True)
    idCurso = Column(Integer, ForeignKey("Curso.id"))
    matricula = Column(String(7))

    usuario = relationship("Usuario", back_populates="aluno")
    curso = relationship("Curso", back_populates="alunos")
    presencas = relationship("Presenca", back_populates="aluno")


class Professor(Base):
    __tablename__ = "Professor"
    idUsuario = Column(Integer, ForeignKey("Usuario.id"), primary_key=True)
    idUniversidade = Column(Integer, ForeignKey("Universidade.id"))
    dataAdmissao = Column(Date)
    titulacao = Column(String(255))

    usuario = relationship("Usuario", back_populates="professor")
    universidade = relationship("Universidade", back_populates="professores")
    disciplinas = relationship("Disciplina", back_populates="professor")


class Notificacao(Base):
    __tablename__ = "Notificacao"
    id = Column(Integer, primary_key=True, autoincrement=True)
    idUsuario = Column(Integer, ForeignKey("Usuario.id"))
    data = Column(DateTime)
    evento = Column(String(255))

    usuario = relationship("Usuario", back_populates="notificacoes")


class Evento(Base):
    __tablename__ = "Evento"
    id = Column(Integer, primary_key=True, autoincrement=True)
    idUniversidade = Column(Integer, ForeignKey("Universidade.id"))
    dataInicio = Column(DateTime)
    dataTermino = Column(DateTime)
    recorrente = Column(Boolean)
    categoria = Column(String(255))
    idProprietario = Column(Integer, ForeignKey("Usuario.id"))

    usuario = relationship("Usuario", back_populates="eventos")
    universidade = relationship("Universidade", back_populates="eventos")
    ocorrencias = relationship("OcorrenciaEvento", back_populates="evento")
    disciplina = relationship("Disciplina", back_populates="evento", uselist=False)
    convidados = relationship("Convidado", back_populates="evento")


class Disciplina(Base):
    __tablename__ = "Disciplina"
    idEvento = Column(Integer, ForeignKey("Evento.id"), primary_key=True)
    idProfessor = Column(Integer, ForeignKey("Professor.idUsuario"))
    horario = Column(String(10))
    nome = Column(String(255))

    evento = relationship("Evento", back_populates="disciplina")
    professor = relationship("Professor", back_populates="disciplinas")
    dDisciplinaDias = relationship("dDisciplina_dias", back_populates="disciplina")
    cursoDisciplina = relationship("CursoDisciplina", back_populates="disciplina")


class dDisciplina_dias(Base):
    __tablename__ = "dDisciplina"
    idDisciplina = Column(Integer, ForeignKey("Disciplina.idEvento"), primary_key=True)
    dia = Column(String(10), primary_key=True)

    disciplina = relationship("Disciplina", back_populates="dDisciplinaDias")


class CursoDisciplina(Base):
    __tablename__ = "CursoDisciplina"
    id = Column(Integer, primary_key=True, autoincrement=True)
    idCurso = Column(Integer, ForeignKey("Curso.id"))
    idDisciplina = Column(Integer, ForeignKey("Disciplina.idEvento"))
    creditos = Column(Integer)

    curso = relationship("Curso", back_populates="cursoDisciplina")
    disciplina = relationship("Disciplina", back_populates="cursoDisciplina")


class OcorrenciaEvento(Base):
    __tablename__ = "OcorrenciaEvento"
    id = Column(Integer, primary_key=True, autoincrement=True)
    idEvento = Column(Integer, ForeignKey("Evento.id"))
    local = Column(String(255))
    data = Column(DateTime)

    evento = relationship("Evento", back_populates="ocorrencias")
    presenca = relationship("Presenca", back_populates="ocorrencia")


class Convidado(Base):
    __tablename__ = "Convidado"
    id = Column(Integer, primary_key=True, autoincrement=True)
    idEvento = Column(Integer, ForeignKey("Evento.id"))
    idUsuario = Column(Integer, ForeignKey("Usuario.id"))
    statusVinculo = Column(String(255))

    evento = relationship("Evento", back_populates="convidados")
    usuario = relationship("Usuario", back_populates="convidados")


class Presenca(Base):
    __tablename__ = "Presenca"
    id = Column(Integer, primary_key=True, autoincrement=True)
    idOcorrenciaEvento = Column(Integer, ForeignKey("OcorrenciaEvento.id"))
    idAluno = Column(Integer, ForeignKey("Aluno.idUsuario"))
    presente = Column(Boolean)

    ocorrencia = relationship("OcorrenciaEvento", back_populates="presenca")
    aluno = relationship("Aluno", back_populates="presencas")
