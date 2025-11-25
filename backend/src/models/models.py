import sqlalchemy as db
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import ForeignKey


Base = declarative_base()

# --- DEFINIÇÃO DAS CLASSES ---

class Universidade(Base):
    __tablename__ = "Universidade"
    # primary_key já garante unicidade automaticamente
    id = db.Column(db.Integer, primary_key=True, autoincrement=True) 
    nome = db.Column(db.String(255))
    sigla = db.Column(db.String(20))
    
    # ADICIONADO unique=True
    cnpj = db.Column(db.String(14), unique=True) 
    email = db.Column(db.String(255), unique=True) 

    cursos = relationship("Curso", back_populates="universidade")
    professores = relationship("Professor", back_populates="universidade")
    evento = relationship("Evento", back_populates="universidade")


class Curso(Base):
    __tablename__ = "Curso"
    idUniversidade = db.Column(db.Integer, ForeignKey("Universidade.id"))
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255))
    sigla = db.Column(db.String(10))
    
    # ADICIONADO unique=True (Assumindo que email do curso não repete)
    email = db.Column(db.String(255), unique=True)

    universidade = relationship("Universidade", back_populates="cursos")
    alunos = relationship("Aluno", back_populates="curso")
    cursoDisciplina = relationship("CursoDisciplina", back_populates="curso")


class Usuário(Base):
    __tablename__ = "Usuário"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255))
    
    # ADICIONADO unique=True
    email = db.Column(db.String(255), unique=True)
    cpf = db.Column(db.String(11), unique=True)
    senha = db.Column(db.String(255))

    aluno = relationship("Aluno", back_populates="Usuário", uselist=False)
    professor = relationship("Professor", back_populates="Usuário", uselist=False)
    notificacao = relationship("Notificacao", back_populates="Usuário")
    convidado = relationship("Convidado", back_populates="Usuário")
    evento = relationship("Evento", back_populates="Usuário")


class Aluno(Base):
    __tablename__ = "Aluno"
    # Este ID é PK e FK ao mesmo tempo, então é ÚNICO por ser PK.
    idUsuário = db.Column("idUsuário", db.Integer, ForeignKey("Usuário.id"), primary_key=True)
    idCurso = db.Column(db.Integer, ForeignKey("Curso.id"))
    matricula = db.Column("mátricula", db.String(7)) # Dica: Geralmente matrícula também é única (unique=True)

    Usuário = relationship("Usuário", back_populates="aluno")
    curso = relationship("Curso", back_populates="alunos")
    presenca = relationship("Presenca", back_populates="aluno")


class Professor(Base):
    __tablename__ = "Professor"
    # ÚNICO por ser PK
    idUsuário = db.Column("idUsuário", db.Integer, ForeignKey("Usuário.id"), primary_key=True)
    idUniversidade = db.Column(db.Integer, ForeignKey("Universidade.id"))
    dataAdmissao = db.Column("dataAdmissão", db.Date)
    titulacao = db.Column("titulacao",db.String(255))

    Usuário = relationship("Usuário", back_populates="professor")
    universidade = relationship("Universidade", back_populates="professores")
    disciplina = relationship("Disciplina", back_populates="professor")


class Notificacao(Base):
    __tablename__ = "Notificação"
    idUsuário = db.Column("idUsuário", db.Integer, ForeignKey("Usuário.id"))
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    data = db.Column(db.DateTime)
    evento = db.Column(db.String(255))

    Usuário = relationship("Usuário", back_populates="notificacao")


class Evento(Base):
    __tablename__ = "Evento"
    idUniversidade = db.Column(db.Integer, ForeignKey("Universidade.id"))
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dataInicio = db.Column(db.DateTime)
    dataTermino = db.Column(db.DateTime)
    recorrente = db.Column(db.Boolean)
    categoria = db.Column(db.String(255))
    idProprietario = db.Column("idproprietário", db.Integer, ForeignKey("Usuário.id"))

    Usuário = relationship("Usuário", back_populates="evento")
    universidade = relationship("Universidade", back_populates="evento")
    ocorrenciaEvento = relationship("OcorrenciaEvento", back_populates="evento")
    disciplina = relationship("Disciplina", back_populates="evento", uselist=False)
    convidado = relationship("Convidado", back_populates="evento")


class Disciplina(Base):
    __tablename__ = "Disciplina"
    # ÚNICO por ser PK
    idEvento = db.Column(db.Integer, ForeignKey("Evento.id"), primary_key=True)
    idProfessor = db.Column(db.Integer, ForeignKey("Professor.idUsuário"))
    horario = db.Column(db.String(10))
    nome = db.Column(db.String(255))

    evento = relationship("Evento", back_populates="disciplina")
    professor = relationship("Professor", back_populates="disciplina")
    dDisciplinaDias = relationship("dDisciplina_dias", back_populates="disciplina")
    cursoDisciplina = relationship("CursoDisciplina", back_populates="disciplina")


class dDisciplina_dias(Base):
    __tablename__ = "dDisciplina"
    # PK Composta (A combinação dos dois campos deve ser única)
    idDisciplina = db.Column(db.Integer, ForeignKey("Disciplina.idEvento"), primary_key=True)
    dia = db.Column(db.String(10), primary_key=True) 

    disciplina = relationship("Disciplina", back_populates="dDisciplinaDias")


class CursoDisciplina(Base):
    __tablename__ = "CursoDisciplina"
    idCurso = db.Column(db.Integer, ForeignKey("Curso.id"))
    idDisciplina = db.Column(db.Integer, ForeignKey("Disciplina.idEvento"))
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    creditos = db.Column(db.Integer)

    curso = relationship("Curso", back_populates="cursoDisciplina")
    disciplina = relationship("Disciplina", back_populates="cursoDisciplina")


class OcorrenciaEvento(Base):
    __tablename__ = "OcorrênciaEvento"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idEvento = db.Column(db.Integer, ForeignKey("Evento.id"))
    local = db.Column(db.String(255))
    data = db.Column(db.DateTime)

    evento = relationship("Evento", back_populates="ocorrenciaEvento")
    presenca = relationship("Presenca", back_populates="ocorrenciaEvento")


class Convidado(Base):
    __tablename__ = "Convidado"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idEvento = db.Column(db.Integer, ForeignKey("Evento.id"))
    idUsuário = db.Column("idUsuário", db.Integer, ForeignKey("Usuário.id"))
    statusVinculo = db.Column(db.String(255))

    evento = relationship("Evento", back_populates="convidado")
    Usuário = relationship("Usuário", back_populates="convidado")


class Presenca(Base):
    __tablename__ = "Presença"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idOcorrenciaEvento = db.Column("idOcorrênciaEvento", db.Integer, ForeignKey("OcorrênciaEvento.id"))
    idAluno = db.Column(db.Integer, ForeignKey("Aluno.idUsuário"))
    presente = db.Column(db.Boolean)

    ocorrenciaEvento = relationship("OcorrenciaEvento", back_populates="presenca")
    aluno = relationship("Aluno", back_populates="presenca")