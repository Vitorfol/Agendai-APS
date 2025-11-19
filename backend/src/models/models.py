import sqlalchemy as db
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from sqlalchemy.orm  import declarative_base
Base = declarative_base()

class Universidade(Base):
    __tablename__ = "Universidade"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    nome = db.Column(db.String(255))
    sigla = db.Column(db.String(20))
    cnpj = db.Column(db.String(14))
    email = db.Column(db.String(255))

    cursos = relationship("Curso", back_populates = "Universidade")
    professores = relationship("Professor", back_populates = "Universidade")
    evento = relationship("Evento", back_populates = "Universidade")


class Curso(Base):
    __tablename__ = "Curso"
    idUniversidade = db.Column(db.Integer, ForeignKey("Universidade.id"))
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    nome = db.Column(db.String(255))
    sigla = db.Column(db.String(10))
    email = db.Column(db.String(255))

    universidade = relationship("Universidade", back_populates = "Curso")
    alunos = relationship("Aluno", back_populates = "Curso")
    CursoDisciplina = relationship("CursoDisciplina", back_populates = "Curso")


class Usuário(Base):
    __tablename__ = "Usuário"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    nome = db.Column(db.String(255))
    email = db.Column(db.String(255))
    cpf = db.Column(db.String(11))

    aluno = relationship("Aluno", back_populates = "Usuário")
    professor = relationship("Professor", back_populates = "Usuário")    
    notificação = relationship("Notificação", back_populates = "Usuário")
    convidado = relationship("Convidado", back_populates = "Usuário")
    evento = relationship("Evento", back_populates= "Usuário")

class Aluno(Base):
    __tablename__ = "Aluno"
    idUsuário = db.Column(db.Integer, ForeignKey("Usuário.id"), primary_key = True)
    idCurso = db.Column(db.Integer, ForeignKey("Curso.id"))
    mátricula = db.Column(db.String(7))

    usuário = relationship("Usuário", back_populates = "Aluno")
    curso = relationship("Curso", back_populates = "Aluno")
    presenca = relationship("Presença", back_populates= "Aluno")

    
class Professor(Base):
    __tablename__ = "Professor"
    idUsuário = db.Column(db.Integer, ForeignKey("Usuário.id"), primary_key = True)
    idUniversidade = db.Column(db.Integer, ForeignKey("Universidade.id"))
    dataAdmissão = db.Column(db.Date)

    usuário = relationship("Usuário", back_populates = "Professor")
    universidade = relationship("Universidade", back_populates = "Professor")
    disciplina = relationship("Professor", back_populates = "Disciplina")  

class Notificação(Base):
    __tablename__ = "Notificação"
    idUsuário = db.Column(db.Integer, ForeignKey("Usuário.id"))
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    data = db.Column(db.DateTime)
    evento = db.Column(db.String(255))

    usuário = relationship("Usuário", back_populates = "Notificação")


class Evento(Base):
    __tablename__ = "Evento"
    idUniversidade = db.Column(db.Integer, ForeignKey("Universidade.id"))
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    dataInicio = db.Column(db.DateTime)
    dataTermino = db.Column(db.DateTime)
    recorrente = db.Column(db.Boolean)
    categoria = db.Column(db.String(255))
    idproprietário = db.Column(db.Integer, ForeignKey("Usuário.id"))


    usuario = relationship("Usuário", back_populates= "Evento")
    universidade = relationship("Universidade", back_populates = "Evento")
    ocorrenciaEvento = relationship("OcorrênciaEvento", back_populates= "Evento")
    disciplina = relationship("Disciplina", back_populates = "Evento")
    convidado = relationship("Convidado", back_populates= "Evento")


class Disciplina(Base):
    __tablename__ = "Disciplina"
    idEvento = db.Column(db.Integer, ForeignKey("Evento.id"), primary_key = True)
    idProfessor = db.Column(db.Integer, ForeignKey("Professor.idUsuário"))
    horario = db.Column(db.String(10))
    nome = db.Column(db.String(255)) 

    evento = relationship("Evento", back_populates = "Disciplina")
    professor = relationship("Professor", back_populates = "Disciplina")    
    disciplina = relationship("Disciplina", back_populates = "dDisciplina")  
    cursoDisciplina = relationship("CursoDisciplina", back_populates = "Disciplina") 

class dDisciplina_dias(Base):
    __tablename__ = "dDisciplina"
    idDisciplina = db.Column(db.Integer, ForeignKey("Disciplina.idEvento"), primary_key = True)
    dia = db.Column(db.String(10))

    disciplina = relationship("dDisciplina", back_populates = "Disciplina")  


class CursoDisciplina(Base):
    __tablename__ = "CursoDisciplina"
    idCurso = db.Column(db.Integer, ForeignKey("Curso.id"))
    idDisciplina = db.Column(db.Integer, ForeignKey("Disciplina.idEvento"))
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    creditos = db.Column(db.Integer)

    curso = relationship("Curso", back_populates = "CursoDisciplina")
    disciplina = relationship("Disciplina", back_populates = "CursoDisciplina") 


class OcorrenciaEvento(Base):
    __tablename__ = "OcorrênciaEvento"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    idEvento = db.Column(db.Integer, ForeignKey("Evento.id"))
    local = db.Column(db.String(255))
    data = db.Column(db.DateTime)

    evento = relationship("Evento", back_populates= "OcorrenciaEvento")
    presenca = relationship("Presença", back_populates= "OcorrenciaEvento")

class Convidado(Base):
    __tablename__ = "Convidado"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    idEvento = db.Column(db.Integer, ForeignKey("Evento.id"))
    idUsuário = db.Column(db.Integer, ForeignKey("Usuário.id"))
    statusVinculo = db.Column(db.String(255))

    evento = relationship("Evento", back_populates= "Convidado")
    usuário = relationship("Usuário", back_populates = "Convidado")


class Presença(Base):
    __tablename__ = "Presença"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    idOcorrênciaEvento = db.Column(db.Integer, ForeignKey("OcorrênciaEvento.id"))
    idAluno = db.Column(db.Integer, ForeignKey("Aluno.idUsuário"))
    presente = db.Column(db.Boolean)

    ocorrenciaEvento = relationship("OcorrenciaEvento", back_populates= "Presença")
    aluno = relationship("Aluno", back_populates= "Presença")




    
    