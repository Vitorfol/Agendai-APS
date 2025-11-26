from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# --- DEFINIÇÃO DAS CLASSES (sem acentos) ---


class Universidade(Base):
<<<<<<< HEAD
    __tablename__ = "universidade"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True) 
    nome = db.Column(db.String(255))
    sigla = db.Column(db.String(20))
    cnpj = db.Column(db.String(14), unique=True) 
    email = db.Column(db.String(255), unique=True)  
    senha = db.Column(db.String(255))
=======
    __tablename__ = "Universidade"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255))
    sigla = Column(String(20))
    cnpj = Column(String(14), unique=True)
    email = Column(String(255), unique=True)
    senha = Column(String(255), nullable=True)
>>>>>>> 089151fc0bf925cde724bf2a322c0146950a9c48

    # Relationships
    cursos = relationship("Curso", back_populates="universidade")
    professores = relationship("Professor", back_populates="universidade")
    eventos = relationship("Evento", back_populates="universidade")


class Curso(Base):
<<<<<<< HEAD
    __tablename__ = "curso"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Mudança: idUniversidade -> id_universidade
    id_universidade = db.Column(db.Integer, ForeignKey("universidade.id"))
    nome = db.Column(db.String(255))
    sigla = db.Column(db.String(10))
    email = db.Column(db.String(255), unique=True)
=======
    __tablename__ = "Curso"
    idUniversidade = Column(Integer, ForeignKey("Universidade.id"))
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255))
    sigla = Column(String(10))
    email = Column(String(255), unique=True)
>>>>>>> 089151fc0bf925cde724bf2a322c0146950a9c48

    # Relationships
    universidade = relationship("Universidade", back_populates="cursos")
    alunos = relationship("Aluno", back_populates="curso")
    curso_disciplina = relationship("CursoDisciplina", back_populates="curso")


class Usuario(Base):
<<<<<<< HEAD
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
=======
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
>>>>>>> 089151fc0bf925cde724bf2a322c0146950a9c48
    eventos = relationship("Evento", back_populates="usuario")


class Aluno(Base):
<<<<<<< HEAD
    __tablename__ = "aluno"
    
    # Mudança: idUsuario -> id_usuario
    id_usuario = db.Column(db.Integer, ForeignKey("usuario.id"), primary_key=True)
    id_curso = db.Column(db.Integer, ForeignKey("curso.id"))
    matricula = db.Column(db.String(7)) # Removido acento de "mátricula"

    # Relationships
=======
    __tablename__ = "Aluno"
    idUsuario = Column(Integer, ForeignKey("Usuario.id"), primary_key=True)
    idCurso = Column(Integer, ForeignKey("Curso.id"))
    matricula = Column(String(7))

>>>>>>> 089151fc0bf925cde724bf2a322c0146950a9c48
    usuario = relationship("Usuario", back_populates="aluno")
    curso = relationship("Curso", back_populates="alunos")
    presencas = relationship("Presenca", back_populates="aluno")


class Professor(Base):
<<<<<<< HEAD
    __tablename__ = "professor"
    
    id_usuario = db.Column(db.Integer, ForeignKey("usuario.id"), primary_key=True)
    id_universidade = db.Column(db.Integer, ForeignKey("universidade.id"))
    data_admissao = db.Column(db.Date) # dataAdmissão -> data_admissao
    titulacao = db.Column(db.String(255))

    # Relationships
=======
    __tablename__ = "Professor"
    idUsuario = Column(Integer, ForeignKey("Usuario.id"), primary_key=True)
    idUniversidade = Column(Integer, ForeignKey("Universidade.id"))
    dataAdmissao = Column(Date)
    titulacao = Column(String(255))

>>>>>>> 089151fc0bf925cde724bf2a322c0146950a9c48
    usuario = relationship("Usuario", back_populates="professor")
    universidade = relationship("Universidade", back_populates="professores")
    disciplinas = relationship("Disciplina", back_populates="professor")


class Notificacao(Base):
<<<<<<< HEAD
    __tablename__ = "notificacao" # Notificação -> notificacao
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, ForeignKey("usuario.id"))
    data = db.Column(db.DateTime)
    mensagem = db.Column("evento", db.String(255)) # Mudei nome da coluna pra evitar conflito com a tabela Evento, mas mantive string original se preferir

    # Relationships
    usuario = relationship("Usuario", back_populates="notificacao")


class Evento(Base):
    __tablename__ = "evento"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_universidade = db.Column(db.Integer, ForeignKey("universidade.id"))
    data_inicio = db.Column(db.DateTime)
    data_termino = db.Column(db.DateTime)
    recorrente = db.Column(db.Boolean)
    categoria = db.Column(db.String(255))
    id_proprietario = db.Column(db.Integer, ForeignKey("usuario.id")) # idproprietário -> id_proprietario

    # Relationships
    usuario = relationship("Usuario", back_populates="eventos")
    universidade = relationship("Universidade", back_populates="eventos")
    ocorrencia_evento = relationship("OcorrenciaEvento", back_populates="evento")
=======
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
>>>>>>> 089151fc0bf925cde724bf2a322c0146950a9c48
    disciplina = relationship("Disciplina", back_populates="evento", uselist=False)
    convidados = relationship("Convidado", back_populates="evento")


class Disciplina(Base):
<<<<<<< HEAD
    __tablename__ = "disciplina"
    
    id_evento = db.Column(db.Integer, ForeignKey("evento.id"), primary_key=True)
    id_professor = db.Column(db.Integer, ForeignKey("professor.id_usuario"))
    horario = db.Column(db.String(10))
    nome = db.Column(db.String(255))
=======
    __tablename__ = "Disciplina"
    idEvento = Column(Integer, ForeignKey("Evento.id"), primary_key=True)
    idProfessor = Column(Integer, ForeignKey("Professor.idUsuario"))
    horario = Column(String(10))
    nome = Column(String(255))
>>>>>>> 089151fc0bf925cde724bf2a322c0146950a9c48

    # Relationships
    evento = relationship("Evento", back_populates="disciplina")
<<<<<<< HEAD
    professor = relationship("Professor", back_populates="disciplina")
    disciplina_dias = relationship("DisciplinaDias", back_populates="disciplina")
    curso_disciplina = relationship("CursoDisciplina", back_populates="disciplina")


class DisciplinaDias(Base):
    __tablename__ = "disciplina_dias"
    
    id_disciplina = db.Column(db.Integer, ForeignKey("disciplina.id_evento"), primary_key=True)
    dia = db.Column(db.String(10), primary_key=True) 
=======
    professor = relationship("Professor", back_populates="disciplinas")
    dDisciplinaDias = relationship("dDisciplina_dias", back_populates="disciplina")
    cursoDisciplina = relationship("CursoDisciplina", back_populates="disciplina")


class dDisciplina_dias(Base):
    __tablename__ = "dDisciplina"
    idDisciplina = Column(Integer, ForeignKey("Disciplina.idEvento"), primary_key=True)
    dia = Column(String(10), primary_key=True)
>>>>>>> 089151fc0bf925cde724bf2a322c0146950a9c48

    # Relationships
    disciplina = relationship("Disciplina", back_populates="disciplina_dias")


class CursoDisciplina(Base):
<<<<<<< HEAD
    __tablename__ = "curso_disciplina"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_curso = db.Column(db.Integer, ForeignKey("curso.id"))
    id_disciplina = db.Column(db.Integer, ForeignKey("disciplina.id_evento"))
    creditos = db.Column(db.Integer)
=======
    __tablename__ = "CursoDisciplina"
    id = Column(Integer, primary_key=True, autoincrement=True)
    idCurso = Column(Integer, ForeignKey("Curso.id"))
    idDisciplina = Column(Integer, ForeignKey("Disciplina.idEvento"))
    creditos = Column(Integer)
>>>>>>> 089151fc0bf925cde724bf2a322c0146950a9c48

    # Relationships
    curso = relationship("Curso", back_populates="curso_disciplina")
    disciplina = relationship("Disciplina", back_populates="curso_disciplina")


class OcorrenciaEvento(Base):
<<<<<<< HEAD
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
    evento = relationship("Evento", back_populates="convidado")
    usuario = relationship("Usuario", back_populates="convidado")


class Presenca(Base):
    __tablename__ = "presenca" # Presença -> presenca
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_ocorrencia_evento = db.Column(db.Integer, ForeignKey("ocorrencia_evento.id"))
    id_aluno = db.Column(db.Integer, ForeignKey("aluno.id_usuario"))
    presente = db.Column(db.Boolean)

    # Relationships
    ocorrencia_evento = relationship("OcorrenciaEvento", back_populates="presenca")
    aluno = relationship("Aluno", back_populates="presenca")
=======
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
>>>>>>> 089151fc0bf925cde724bf2a322c0146950a9c48
