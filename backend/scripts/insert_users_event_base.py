#!/usr/bin/env python3
"""
Script para criar usuários de teste (alunos e professor) e disciplina APS (event base).
Executa chamadas HTTP para as rotas reais da API. Versão para init automático.
"""

import requests
import sys

BASE_URL = "http://localhost:8000/api"

def run_request(method, endpoint, data=None, token=None):
    """Executa uma requisição HTTP e retorna o resultado."""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        elif method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        else:
            return None
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            return None
    except Exception:
        return None

def main():
    # criando alunos (silencioso)
    # Se dados já existirem, script pode falhar silenciosamente - isso é esperado
    
    # Criar alunos
    alunos = [
        {"nome": "Vitor Fontenele", "email": "vitor@aluno.uece.br", "cpf": "11111111111", "senha": "senha123", "id_curso": 1, "matricula": "1111111"},
        {"nome": "Victor Timbó", "email": "victor@aluno.uece.br", "cpf": "22222222222", "senha": "senha123", "id_curso": 1, "matricula": "2222222"},
        {"nome": "Ian Bruno", "email": "ian@aluno.uece.br", "cpf": "33333333333", "senha": "senha123", "id_curso": 1, "matricula": "3333333"},
        {"nome": "Gabriel Marques", "email": "gabrielzito@aluno.uece.br", "cpf": "44444444444", "senha": "senha123", "id_curso": 1, "matricula": "4444444"},
        {"nome": "Ismael Sousa", "email": "ismael@aluno.uece.br", "cpf": "55555555555", "senha": "senha123", "id_curso": 1, "matricula": "5555555"},
        {"nome": "Pedro Otávio", "email": "pedro@aluno.uece.br", "cpf": "66666666666", "senha": "senha123", "id_curso": 1, "matricula": "6666666"},
    ]
    
    alunos_criados = []
    for aluno in alunos:
        resultado = run_request("POST", "/auth/register/aluno", aluno)
        if resultado:
            alunos_criados.append(aluno['email'])
        else:
            pass
    
    # criando professor (silencioso)
    
    # Criar professor
    professor = {
        "nome": "Matheus Paixão",
        "email": "matheus@uece.br",
        "cpf": "77777777777",
        "senha": "senha123",
        "id_universidade": 1
    }
    
    resultado_prof = run_request("POST", "/auth/register/professor", professor)
    if resultado_prof:
        pass
    else:
        # falha crítica
        sys.exit(1)
    
    # login do professor
    
    # Login do professor
    login_data = {
        "email": professor['email'],
        "password": professor['senha']
    }
    
    token_response = run_request("POST", "/auth/login", login_data)
    if not token_response or 'access_token' not in token_response:
        sys.exit(1)
    
    token = token_response['access_token']
    
    # criando disciplina APS
    
    # Criar disciplina
    disciplina_data = {
        "evento": {
            "nome": "APS",
            "descricao": "Disciplina de Análise e Projeto de Software",
            "id_universidade": 1,
            "data_inicio": "2025-07-01T09:20:00.000Z",
            "data_termino": "2025-12-16T11:10:00.000Z",
            "horario_inicio": "09:20:00",
            "horario_termino": "11:10:00",
            "local_padrao": "Sala 101",
            "recorrencia": "semanal",
            "categoria": "disciplina"
        },
        "disciplina": {
            "horario": "35-CD-manha",
            "nome": "APS"
        }
    }
    
    resultado_disciplina = run_request("POST", "/events/", disciplina_data, token)
    if resultado_disciplina and 'id' in resultado_disciplina:
        id_evento = resultado_disciplina['id']
        pass
    else:
        sys.exit(1)
    
    # adicionando alunos como participantes
    
    # Adicionar alunos como participantes
    for email_aluno in alunos_criados:
        resultado = run_request(
            "POST",
            f"/events/{id_evento}/participants?email_usuario={email_aluno}",
            None,
            token
        )
        # ignora retorno, operação silenciosa
        _ = resultado
    
    # script concluído (silencioso)

if __name__ == "__main__":
    main()
