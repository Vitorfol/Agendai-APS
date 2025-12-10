from datetime import datetime
from src.database.connection import SessionLocal
from src.models.models import Evento, OcorrenciaEvento, Disciplina, DisciplinaDias, Universidade


def ensure_university(session):
    uni = session.query(Universidade).first()
    if not uni:
        uni = Universidade(nome="Teste Univ", sigla="TU", cnpj="00000000000000", email=None, senha="")
        session.add(uni)
        session.flush()
    return uni


def main():
    session = SessionLocal()
    try:
        uni = ensure_university(session)

        # 1) Evento não-aula
        evento1 = Evento(
            nome="Reunião de Projeto - Teste",
            descricao="Evento para teste: reunião",
            id_universidade=uni.id,
            data_inicio=datetime(2025, 11, 30, 9, 0, 0),
            data_termino=datetime(2025, 11, 30, 10, 0, 0),
            recorrencia=None,
            categoria="Reunião",
            email_proprietario=None
        )
        session.add(evento1)
        session.flush()

        ocorr1 = OcorrenciaEvento(
            id_evento=evento1.id,
            local="Sala Teste 1",
            data=datetime(2025, 11, 30, 9, 0, 0)
        )
        session.add(ocorr1)

        # 2) Evento do tipo Disciplina com dias SEG/QUA/SEX
        evento2 = Evento(
            nome="Disciplina Teste",
            descricao="Disciplina para testes",
            id_universidade=uni.id,
            data_inicio=datetime(2025, 12, 1, 0, 0, 0),
            data_termino=datetime(2025, 12, 31, 0, 0, 0),
            recorrencia="Semanal",
            categoria="Disciplina",
            email_proprietario=None
        )
        session.add(evento2)
        session.flush()

        disciplina = Disciplina(
            id_evento=evento2.id,
            id_professor=None,
            horario="AB",
            nome="Disciplina Teste Nome"
        )
        session.add(disciplina)
        session.flush()

        # Add days: Segunda, Quarta, Sexta
        dias = ["Segunda", "Quarta", "Sexta"]
        for d in dias:
            dd = DisciplinaDias(id_disciplina=disciplina.id_evento, dia=d)
            session.add(dd)

        # Create one occurrence for the discipline (e.g., 2025-12-01 08:00:00)
        ocorr2 = OcorrenciaEvento(
            id_evento=evento2.id,
            local="Sala Disciplina",
            data=datetime(2025, 12, 1, 8, 0, 0)
        )
        session.add(ocorr2)

        session.commit()

        print("Inserted:")
        print(f"  non-class event id: {evento1.id} -> occurrence date 2025-11-30")
        print(f"  discipline event id: {evento2.id} -> occurrence date 2025-12-01")
        print("")
        print("Test with these curl commands:")
        print(f"curl -i \"http://localhost:8000/api/events/{evento1.id}/2025-11-30\"")
        print(f"curl -i \"http://localhost:8000/api/events/{evento2.id}/2025-12-01\"")

    except Exception as e:
        session.rollback()
        print("Error inserting test data:", e)
    finally:
        session.close()


if __name__ == '__main__':
    main()
