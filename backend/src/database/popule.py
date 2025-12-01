import sqlalchemy as db
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import sys
import os

# Configuração de caminhos para importação (mantida do seu original)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

# Importa os modelos atualizados e a engine
from src.models.models import *
from connection import engine
from src.core.security import pegar_senha_hash

def popular_banco():
    # Cria a sessão
    Session = sessionmaker(bind=engine)
    session = Session()

    print("--- Iniciando inserção de dados ---")

    # 1. Criar Universidade
    univ = Universidade(
        nome="Universidade Federal de Tecnologia",
        sigla="UFT",
        cnpj="12345678000199",
        email="contato@uft.edu.br",
        senha=pegar_senha_hash("universidade123")
    )
    session.add(univ)
    session.flush() # Garante que univ.id foi gerado

    univ2 = Universidade(
        nome="Universidade Estadual do Ceará",
        sigla="UECE",
        cnpj="12345678000200",
        email="contato@uece,br",
        senha=pegar_senha_hash("uece123")
    )
    session.add(univ2)
    session.flush()

    # 2. Criar Usuarios (Base para Alunos, Professores e Admin)
    # Adicionando senha padrão (hash) para os usuários de teste
    user_prof = Usuario(nome="Dr. Roberto Silva", email="roberto@uft.edu.br", cpf="11111111111", senha=pegar_senha_hash("senha123"))
    user_aluno1 = Usuario(nome="Ana Souza", email="ana.souza@aluno.uft.edu.br", cpf="22222222222", senha=pegar_senha_hash("senha123"))
    user_aluno2 = Usuario(nome="Carlos Lima", email="carlos.lima@aluno.uft.edu.br", cpf="33333333333", senha=pegar_senha_hash("senha123"))
    user_convidado = Usuario(nome="Palestrante Externo", email="guest@email.com", cpf="44444444444", senha=pegar_senha_hash("senha123"))
    
    session.add_all([user_prof, user_aluno1, user_aluno2, user_convidado])
    session.flush()

    # 3. Vincular Professor e Alunos aos Usuarios
    # Professor
    prof = Professor(
        id_usuario=user_prof.id,        # Mudança: idUsuario -> id_usuario
        id_universidade=univ.id         # Mudança: idUniversidade -> id_universidade
    )
    session.add(prof)

    # Curso
# Curso
    curso = Curso(
        nome="Ciência da Computação",
        sigla="BCC",
        email="bcc@uft.edu.br",
        id_universidade=univ.id,
        graduacao=True      # Mudança: idUniversidade -> id_universidade
    )
    session.add(curso)
    session.flush()

    curso2 = Curso(
        nome="Matematica",
        sigla="MAT",
        email="mat@uft.edu.br",
        id_universidade=univ.id,
        graduacao=False      # Mudança: idUniversidade -> id_universidade
    )
    session.add(curso2)
    session.flush()

    curso3 = Curso(
        nome="Fisica",
        sigla="FIS",
        email="fis@uece.br",
        id_universidade=univ2.id,
        graduacao=True      # Mudança: idUniversidade -> id_universidade
    )
    session.add(curso3)
    session.flush()

    # Alunos
    aluno1 = Aluno(id_usuario=user_aluno1.id, id_curso=curso.id, matricula="2023001") # Snake case aplicado
    aluno2 = Aluno(id_usuario=user_aluno2.id, id_curso=curso.id, matricula="2023002")
    session.add_all([aluno1, aluno2])

    # 4. Criar Eventos e Disciplinas
    
    # Evento genérico
    evento_palestra = Evento(
        id_universidade=univ.id,
        data_inicio=datetime.now(),             # Mudança: dataInicio -> data_inicio
        data_termino=datetime.now() + timedelta(hours=2), # Mudança: dataTermino -> data_termino
        recorrencia="False",
        categoria="Palestra",
    email_proprietario=user_prof.email     # Mudança: idProprietario -> email_proprietario (agora referencia usuario.email)
    )
    session.add(evento_palestra)
    session.flush()

    # Evento do tipo Disciplina
    evento_aula = Evento(
        id_universidade=univ.id,
        data_inicio=datetime.now(),
        data_termino=datetime.now() + timedelta(60),
        recorrencia="True",
        categoria="Aula",
    email_proprietario=user_prof.email
    )
    session.add(evento_aula)
    session.flush() 

    # Disciplina 
    disciplina = Disciplina(
        id_evento=evento_aula.id,           # Mudança: idEvento -> id_evento
        id_professor=prof.id_usuario,       # Mudança: idProfessor -> id_professor e idUsuario -> id_usuario
        horario="19:00",
        nome="Banco de Dados I"
    )
    session.add(disciplina)
    session.flush()

    # 5. Tabelas dependentes de Disciplina e Curso
    # Mudança: Classe dDisciplina_dias virou DisciplinaDias
    d_dias = DisciplinaDias(id_disciplina=disciplina.id_evento, dia="Segunda") # Mudança: idDisciplina -> id_disciplina
    d_dias2 = DisciplinaDias(id_disciplina=disciplina.id_evento, dia="Quarta")
    
    curso_disc = CursoDisciplina(
        id_curso=curso.id,                  # Mudança: idCurso -> id_curso
        id_disciplina=disciplina.id_evento, # Mudança: idDisciplina -> id_disciplina
        creditos=4
    )
    session.add_all([d_dias, d_dias2, curso_disc])

    # 6. Ocorrência, Notificação, Convidado
    ocorrencia = OcorrenciaEvento(
        id_evento=evento_aula.id,           # Mudança: idEvento -> id_evento
        local="Sala 301",
        data=datetime.now()
    )
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
        id_usuario=user_convidado.id,       # Mudança: idUsuario -> id_usuario
        status_vinculo="Confirmado"         # Mudança: statusVinculo -> status_vinculo
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

    # Salvar tudo
    session.commit()
    print("--- Dados inseridos com sucesso! ---")
    print(f"Universidade ID: {univ.id}")
    print(f"Professor Criado ID: {prof.id_usuario}")
    print(f"Disciplina Criada: {disciplina.nome} (Vinculada ao Evento ID: {disciplina.id_evento})")

if __name__ == "__main__":
    popular_banco()