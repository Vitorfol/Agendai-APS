import requests

# ========================
# CONFIGURAÇÕES
# ========================

BASE_URL = "http://localhost:8000/api"

EMAIL = "contato@uece.br"
SENHA = "dedelbrabo"

EVENTO_PAYLOAD = {
    "evento": {
        "nome": "Feira de Ciências UECE",
        "descricao": "Evento institucional da universidade",
        "id_universidade": 4,
        "data_inicio": "2025-12-01T00:00:00Z",
        "data_termino": "2025-12-05T00:00:00Z",
        "horario_inicio": "13:00:00",
        "horario_termino": "17:00:00",
        "local_padrao": "Campus Itaperi",
        "recorrencia": "diario",
        "categoria": "ACADEMICO"
    },
    "disciplina": None
}

# ========================
# HELPERS
# ========================

def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


def print_response(response):
    print(f"➡️ Status: {response.status_code}")

    try:
        data = response.json()
        print("📦 Resposta:")
        print(data)
    except ValueError:
        print("📦 Resposta (texto):")
        print(response.text)

    print("-" * 60 + "\n")


# ========================
# ROTAS
# ========================

def login():
    print("🔐 Fazendo login...")

    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": EMAIL,
            "password": SENHA
        }
    )

    print_response(response)
    response.raise_for_status()

    return response.json()["access_token"]


def criar_evento(token):
    print("📌 Criando evento...")

    response = requests.post(
        f"{BASE_URL}/events/",
        headers=auth_headers(token),
        json=EVENTO_PAYLOAD
    )

    print_response(response)
    response.raise_for_status()

    return response.json()["id"]


def listar_ocorrencias_usuario(token):
    print("📋 Listando ocorrências do usuário...")

    response = requests.get(
        f"{BASE_URL}/events/",
        headers=auth_headers(token)
    )

    print_response(response)
    response.raise_for_status()

    return response.json()


def obter_evento_por_id(token, id_evento):
    print(f"🔎 Obtendo evento por ID ({id_evento})...")

    response = requests.get(
        f"{BASE_URL}/events/{id_evento}",
        headers=auth_headers(token)
    )

    print_response(response)
    response.raise_for_status()

    return response.json()


def listar_ocorrencias_evento(token, id_evento):
    print("📆 Listando ocorrências do evento...")

    response = requests.get(
        f"{BASE_URL}/events/{id_evento}/occurrences",
        headers=auth_headers(token)
    )

    print_response(response)
    response.raise_for_status()

    return response.json()


def obter_ocorrencia_por_data(token, id_evento, data):
    print(f"📅 Obtendo ocorrência do dia {data}...")

    response = requests.get(
        f"{BASE_URL}/events/{id_evento}/{data}",
        headers=auth_headers(token)
    )

    print_response(response)
    response.raise_for_status()

    return response.json()


def atualizar_ocorrencia(token, id_evento, data):
    print("✏️ Atualizando ocorrência...")

    response = requests.put(
        f"{BASE_URL}/events/{id_evento}/{data}",
        headers=auth_headers(token),
        json={
            "horario_inicio": "14:00:00",
            "horario_termino": "18:00:00",
            "local": "Auditório Central"
        }
    )

    print_response(response)
    response.raise_for_status()


def cancelar_ocorrencia(token, id_evento, data):
    print("❌ Cancelando ocorrência...")

    response = requests.delete(
        f"{BASE_URL}/events/{id_evento}/{data}",
        headers=auth_headers(token)
    )

    print_response(response)
    response.raise_for_status()


def deletar_evento(token, id_evento):
    print("🗑️ Deletando evento...")

    response = requests.delete(
        f"{BASE_URL}/events/{id_evento}",
        headers=auth_headers(token)
    )

    print_response(response)
    response.raise_for_status()


# ========================
# MAIN
# ========================

def main():
    token = login()

    # 👉 Comente / descomente o que quiser testar

    # id_evento = criar_evento(token)

    #listar_ocorrencias_usuario(token)

    #obter_evento_por_id(token, 53)

    #ocorrencias = listar_ocorrencias_evento(token, 53)
    #data = ocorrencias[0]["data"]

    #obter_ocorrencia_por_data(token, 53, data)
    #atualizar_ocorrencia(token, 53, "2025-12-02T00:00:00Z")
    #cancelar_ocorrencia(token, 53, "2025-12-03T00:00:00Z")

    deletar_evento(token, 53)

    print("🎉 TESTES FINALIZADOS")


if __name__ == "__main__":
    main()
