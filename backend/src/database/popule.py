# ...existing code...
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker

# ajustar path do projeto para imports locais
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.models.models import (
    Universidade, Curso, Usuario, Professor, Aluno, Evento, Disciplina,
    DisciplinaDias, CursoDisciplina, OcorrenciaEvento, Notificacao,
    Convidado, Presenca
)
from connection import engine
from src.core.security import pegar_senha_hash

def popular_banco():
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("Iniciando popular_banco()")

        # Universidades
        u1 = Universidade(
            nome="Universidade Federal de Tecnologia",
            sigla="UFT",
            cnpj="12345678000199",
            email="contato@uft.edu.br",
            senha=pegar_senha_hash("universidade123")
        )
        u2 = Universidade(
            nome="Universidade Estadual do Ceará",
            sigla="UECE",
            cnpj="12345678000200",
            email="contato@uece.br",
            senha=pegar_senha_hash("uece123")
        )
        session.add_all([u1, u2])
        session.flush()  # gera ids

        # Usuários (professor, alunos, convidado)
        user_prof = Usuario(nome="Dr. Roberto Silva", email="roberto@uft.edu.br", cpf="11111111111", senha=pegar_senha_hash("senha123"))
        user_aluno1 = Usuario(nome="Ana Souza", email="ana.souza@aluno.uft.edu.br", cpf="22222222222", senha=pegar_senha_hash("senha123"))
        user_aluno2 = Usuario(nome="Carlos Lima", email="carlos.lima@aluno.uft.edu.br", cpf="33333333333", senha=pegar_senha_hash("senha123"))
        user_convidado = Usuario(nome="Palestrante Externo", email="palestrante@externo.com", cpf="44444444444", senha=pegar_senha_hash("senha123"))

        session.add_all([user_prof, user_aluno1, user_aluno2, user_convidado])
        session.flush()  # gera ids de usuario

        # Professor (primary key = id_usuario)
        prof = Professor(id_usuario=user_prof.id, id_universidade=u1.id)
        session.add(prof)

        # Cursos
        curso_bcc = Curso(nome="Ciência da Computação", sigla="BCC", email="bcc@uft.edu.br", id_universidade=u1.id, graduacao=True)
        curso_mat = Curso(nome="Matemática", sigla="MAT", email="mat@uft.edu.br", id_universidade=u1.id, graduacao=False)
        session.add_all([curso_bcc, curso_mat])
        session.flush()  # gera ids de cursos

        # Alunos (primary key = id_usuario)
        aluno1 = Aluno(id_usuario=user_aluno1.id, id_curso=curso_bcc.id, matricula="2023001")
        aluno2 = Aluno(id_usuario=user_aluno2.id, id_curso=curso_bcc.id, matricula="2023002")
        session.add_all([aluno1, aluno2])

        session.flush()

        # Eventos: usar email_proprietario = email do usuario proprietário
        evento_palestra = Evento(
            nome="Palestra sobre Inovações Tecnológicas",
            descricao="Uma palestra sobre inovações.",
            id_universidade=u1.id,
            data_inicio=datetime.now() + timedelta(days=1),
            data_termino=datetime.now() + timedelta(days=1, hours=2),
            recorrencia="Não",
            categoria="Palestra",
            email_proprietario=user_prof.email
        )
        evento_aula = Evento(
            nome="Aula: Banco de Dados I",
            descricao="Aula inaugural de Banco de Dados I.",
            id_universidade=u1.id,
            data_inicio=datetime.now() + timedelta(hours=2),
            data_termino=datetime.now() + timedelta(hours=3),
            recorrencia="Semanal",
            categoria="Aula",
            email_proprietario=user_prof.email
        )
        session.add_all([evento_palestra, evento_aula])
        session.flush()  # gera ids de eventos

        # Disciplina: primary key = id_evento (usar id do evento_aula)
        disciplina = Disciplina(
            id_evento=evento_aula.id,
            id_professor=prof.id_usuario,
            horario="19:00",
            nome="Banco de Dados I"
        )
        session.add(disciplina)
        session.flush()

        # Dias da disciplina (id_disciplina refere-se a disciplina.id_evento)
        dia1 = DisciplinaDias(id_disciplina=disciplina.id_evento, dia="Segunda")
        dia2 = DisciplinaDias(id_disciplina=disciplina.id_evento, dia="Quarta")
        session.add_all([dia1, dia2])

        # Vínculo curso-disciplina
        curso_disc = CursoDisciplina(id_curso=curso_bcc.id, id_disciplina=disciplina.id_evento, creditos=4)
        session.add(curso_disc)

        # Ocorrencia do evento (evento_aula)
        ocorrencia = OcorrenciaEvento(id_evento=evento_aula.id, local="Sala 301", data=datetime.now() + timedelta(hours=2))
        session.add(ocorrencia)
        session.flush()

    notificacao = Notificacao(
        id_usuario=user_aluno1.id,          # Mudança: idUsuario -> id_usuario
        data=datetime.now(),
        mensagem="Aula de BD I começou",
        evento="Banco de Dados I" # Mudança: atributo 'evento' virou 'mensagem' na classe
    )

    convidado = Convidado(
        id_evento=evento_palestra.id,       # Mudança: idEvento -> id_evento
        id_usuario=user_convidado.id        # Mudança: idUsuario -> id_usuario
    )
    session.add_all([notificacao, convidado])

    # 7. Presença
    presenca1 = Presenca(
        id_ocorrencia_evento=ocorrencia.id, # Mudança: idOcorrenciaEvento -> id_ocorrencia_evento
        id_aluno=aluno1.id_usuario,         # Mudança: idAluno -> id_aluno
        presente=True
    )
    presenca2 = Presenca(
        id_ocorrencia_evento=ocorrencia.id,
        id_aluno=aluno2.id_usuario,
        presente=False
    )
    session.add_all([presenca1, presenca2])

        # commit final
        session.commit()

        print("Banco populado com sucesso:")
        print(f"Universidades: {u1.id}, {u2.id}")
        print(f"Usuarios criados: prof={user_prof.id}, aluno1={user_aluno1.id}, aluno2={user_aluno2.id}, convidado={user_convidado.id}")
        print(f"Evento aula id: {evento_aula.id}, disciplina id_evento: {disciplina.id_evento}")

    except Exception as e:
        session.rollback()
        print("Erro ao popular banco:", e)
    finally:
        session.close()

if __name__ == "__main__":
    popular_banco()
# ...existing code...