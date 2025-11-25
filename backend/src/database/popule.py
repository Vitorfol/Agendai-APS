import sqlalchemy as db
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)
from src.models.models import *
from connection import engine




def popular_banco():
    # Cria as tabelas
    Session = sessionmaker(bind=engine)
    session = Session()

    print("--- Iniciando inserção de dados ---")

    # 1. Criar Universidade
    univ = Universidade(
        nome="Universidade Federal de Tecnologia",
        sigla="UFT",
        cnpj="12345678000199",
        email="contato@uft.edu.br"
    )
    session.add(univ)
    session.flush() # Garante que univ.id foi gerado

    # 2. Criar Usuários (Base para Alunos, Professores e Admin)
    user_prof = Usuário(nome="Dr. Roberto Silva", email="roberto@uft.edu.br", cpf="11111111111")
    user_aluno1 = Usuário(nome="Ana Souza", email="ana.souza@aluno.uft.edu.br", cpf="22222222222")
    user_aluno2 = Usuário(nome="Carlos Lima", email="carlos.lima@aluno.uft.edu.br", cpf="33333333333")
    user_convidado = Usuário(nome="Palestrante Externo", email="guest@email.com", cpf="44444444444")
    
    session.add_all([user_prof, user_aluno1, user_aluno2, user_convidado])
    session.flush()

    # 3. Vincular Professor e Alunos aos Usuários
    # Professor (Herança/Vínculo 1:1 com Usuário)
    prof = Professor(
        idUsuário=user_prof.id,
        idUniversidade=univ.id,
        dataAdmissao=datetime.now().date()
    )
    session.add(prof)

    # Curso
    curso = Curso(
        nome="Ciência da Computação",
        sigla="BCC",
        email="bcc@uft.edu.br",
        idUniversidade=univ.id
    )
    session.add(curso)
    session.flush()

    # Alunos (Herança/Vínculo 1:1 com Usuário)
    aluno1 = Aluno(idUsuário=user_aluno1.id, idCurso=curso.id, matricula="2023001")
    aluno2 = Aluno(idUsuário=user_aluno2.id, idCurso=curso.id, matricula="2023002")
    session.add_all([aluno1, aluno2])

    # 4. Criar Eventos e Disciplinas
    # Nota: Disciplina herda ID de Evento (é um tipo especial de Evento neste modelo)
    
    # Evento genérico
    evento_palestra = Evento(
        idUniversidade=univ.id,
        dataInicio=datetime.now(),
        dataTermino=datetime.now() + timedelta(hours=2),
        recorrente=False,
        categoria="Palestra",
        idProprietario=user_prof.id
    )
    session.add(evento_palestra)
    session.flush()

    # Evento do tipo Disciplina (Ex: Aula de Banco de Dados)
    evento_aula = Evento(
        idUniversidade=univ.id,
        dataInicio=datetime.now(),
        dataTermino=datetime.now() + timedelta(60),
        recorrente=True,
        categoria="Aula",
        idProprietario=user_prof.id
    )
    session.add(evento_aula)
    session.flush() # Preciso do ID para criar a disciplina

    # Disciplina (Vinculada ao ID do evento_aula)
    disciplina = Disciplina(
        idEvento=evento_aula.id,
        idProfessor=prof.idUsuário,
        horario="19:00",
        nome="Banco de Dados I"
    )
    session.add(disciplina)
    session.flush()

    # 5. Tabelas dependentes de Disciplina e Curso
    d_dias = dDisciplina_dias(idDisciplina=disciplina.idEvento, dia="Segunda")
    d_dias2 = dDisciplina_dias(idDisciplina=disciplina.idEvento, dia="Quarta")
    
    curso_disc = CursoDisciplina(
        idCurso=curso.id,
        idDisciplina=disciplina.idEvento,
        creditos=4
    )
    session.add_all([d_dias, d_dias2, curso_disc])

    # 6. Ocorrência, Notificação, Convidado
    ocorrencia = OcorrenciaEvento(
        idEvento=evento_aula.id,
        local="Sala 301",
        data=datetime.now()
    )
    session.add(ocorrencia)
    session.flush()

    notificacao = Notificacao(
        idUsuário=user_aluno1.id,
        data=datetime.now(),
        evento="Aula de BD I começou"
    )

    convidado = Convidado(
        idEvento=evento_palestra.id,
        idUsuário=user_convidado.id,
        statusVinculo="Confirmado"
    )
    session.add_all([notificacao, convidado])

    # 7. Presença
    presenca1 = Presenca(
        idOcorrenciaEvento=ocorrencia.id,
        idAluno=aluno1.idUsuário,
        presente=True
    )
    presenca2 = Presenca(
        idOcorrenciaEvento=ocorrencia.id,
        idAluno=aluno2.idUsuário,
        presente=False
    )
    session.add_all([presenca1, presenca2])

    # Salvar tudo
    session.commit()
    print("--- Dados inseridos com sucesso! ---")
    print(f"Universidade ID: {univ.id}")
    print(f"Professor Criado ID: {prof.idUsuário}")
    print(f"Disciplina Criada: {disciplina.nome} (Vinculada ao Evento ID: {disciplina.idEvento})")

if __name__ == "__main__":
    popular_banco()