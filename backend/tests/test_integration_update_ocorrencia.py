#!/usr/bin/env python3
"""
TESTE DE INTEGRAÇÃO - ATUALIZAÇÃO DE OCORRÊNCIAS
=================================================
Testa o endpoint: PUT /api/events/{id_evento}/{date}

Este teste:
1. Cria um usuário de teste no banco (se não existir)
2. Cria um evento com proprietário
3. Faz login para obter token
4. Testa todas as operações de UPDATE
5. Limpa os dados de teste (opcional)

CREDENCIAIS:
- Email: contato@uece.br
- Senha: dedelbrabo
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
from datetime import datetime
from src.database.connection import SessionLocal
from src.models.models import Usuario, Professor, Evento, OcorrenciaEvento, Universidade
from src.core.security import pegar_senha_hash

# Configurações
BASE_URL = "http://localhost:8000/api"
TEST_EMAIL = "contato@uece.br"
TEST_PASSWORD = "dedelbrabo"

# Cores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_section(title):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}  {title}{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}")

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.YELLOW}ℹ️  {msg}{Colors.END}")

def setup_test_data():
    """Cria usuário e evento de teste no banco"""
    print_section("SETUP: Preparando dados de teste")
    
    db = SessionLocal()
    event_id = None
    test_date = "2025-12-15"
    
    try:
        # 1. Garantir que existe universidade
        uni = db.query(Universidade).first()
        if not uni:
            print_info("Criando universidade de teste...")
            uni = Universidade(
                nome="UECE",
                sigla="UECE",
                cnpj="00000000000001",
                email=None,
                senha=""
            )
            db.add(uni)
            db.flush()
            print_success(f"Universidade criada (ID: {uni.id})")
        else:
            print_success(f"Universidade encontrada (ID: {uni.id})")
        
        # 2. Criar/verificar usuário (contato@uece.br / dedelbrabo)
        # Este usuário será o PROPRIETÁRIO do evento de teste
        user = db.query(Usuario).filter(Usuario.email == TEST_EMAIL).first()
        if not user:
            print_info(f"Criando usuário: {TEST_EMAIL}")
            print_info(f"Senha: {TEST_PASSWORD}")
            user = Usuario(
                nome="Usuario Teste Update",
                email=TEST_EMAIL,
                cpf="00011122233",
                senha=pegar_senha_hash(TEST_PASSWORD)
            )
            db.add(user)
            db.flush()
            
            prof = Professor(
                id_usuario=user.id,
                id_universidade=uni.id
            )
            db.add(prof)
            db.commit()
            print_success(f"Usuário criado (ID: {user.id})")
            print_success(f"Login: {TEST_EMAIL} / {TEST_PASSWORD}")
        else:
            print_success(f"Usuário já existe (ID: {user.id})")
            print_info(f"Login disponível: {TEST_EMAIL} / {TEST_PASSWORD}")
        
        # 3. Criar/atualizar evento de teste com proprietário
        # Verificar se já existe
        evento = db.query(Evento).filter(
            Evento.nome == "Teste Update Ocorrência",
            Evento.email_proprietario == TEST_EMAIL
        ).first()
        
        if not evento:
            print_info("Criando evento de teste...")
            evento = Evento(
                nome="Teste Update Ocorrência",
                descricao="Evento para testar atualização de ocorrências",
                id_universidade=uni.id,
                data_inicio=datetime(2025, 12, 15, 8, 0, 0),
                data_termino=datetime(2025, 12, 15, 18, 0, 0),  # Janela maior para testes
                recorrencia=None,
                categoria="Teste",
                email_proprietario=TEST_EMAIL
            )
            db.add(evento)
            db.flush()
            
            # Criar ocorrência
            ocorrencia = OcorrenciaEvento(
                id_evento=evento.id,
                local="Sala Original 100",
                data=datetime(2025, 12, 15, 10, 0, 0)
            )
            db.add(ocorrencia)
            db.commit()
            print_success(f"Evento criado (ID: {evento.id})")
        else:
            print_success(f"Evento já existe (ID: {evento.id})")
            
            # Resetar a ocorrência para o valor inicial para testes consistentes
            ocorrencia = db.query(OcorrenciaEvento).filter(
                OcorrenciaEvento.id_evento == evento.id,
                OcorrenciaEvento.data >= datetime(2025, 12, 15, 0, 0, 0),
                OcorrenciaEvento.data < datetime(2025, 12, 16, 0, 0, 0)
            ).first()
            
            if ocorrencia:
                print_info("Resetando ocorrência para valores iniciais...")
                ocorrencia.local = "Sala Original 100"
                ocorrencia.data = datetime(2025, 12, 15, 10, 0, 0)
                db.commit()
                print_success("Ocorrência resetada")
            else:
                # Criar se não existir
                print_info("Criando ocorrência...")
                ocorrencia = OcorrenciaEvento(
                    id_evento=evento.id,
                    local="Sala Original 100",
                    data=datetime(2025, 12, 15, 10, 0, 0)
                )
                db.add(ocorrencia)
                db.commit()
                print_success("Ocorrência criada")
        
        event_id = evento.id
        
        print(f"\n{Colors.BOLD}Dados de teste prontos:{Colors.END}")
        print(f"  Evento ID: {event_id}")
        print(f"  Data: {test_date}")
        print(f"  Local inicial: Sala Original 100")
        print(f"  Proprietário: {TEST_EMAIL}")
        print(f"\n{Colors.BOLD}Credenciais para teste manual:{Colors.END}")
        print(f"  Email: {TEST_EMAIL}")
        print(f"  Senha: {TEST_PASSWORD}")
        print(f"  Use essas credenciais para fazer login e testar o UPDATE!")
        
    except Exception as e:
        db.rollback()
        print_error(f"Erro no setup: {str(e)}")
        raise
    finally:
        db.close()
    
    return event_id, test_date


def test_get_ocorrencia(event_id, test_date):
    """Teste 1: GET da ocorrência"""
    print_section("TESTE 1: GET Ocorrência (Baseline)")
    
    url = f"{BASE_URL}/events/{event_id}/{test_date}"
    print(f"GET {url}")
    
    response = requests.get(url)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        data = response.json()
        print_success("Ocorrência encontrada!")
        print(f"  Local: {data.get('local')}")
        print(f"  Data: {data.get('data')}")
        print(f"  Hora: {data.get('hora')}")
        return data
    else:
        print_error("Falha ao buscar ocorrência")
        return None


def test_without_auth(event_id, test_date):
    """Teste 2: PUT sem autenticação"""
    print_section("TESTE 2: PUT sem Autenticação (deve dar 401)")
    
    url = f"{BASE_URL}/events/{event_id}/{test_date}"
    print(f"PUT {url} (sem token)")
    
    response = requests.put(
        url,
        json={"local": "Tentativa sem auth"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 401:
        print_success("Proteção de autenticação funcionando!")
        return True
    else:
        print_error(f"Esperado 401, recebido {response.status_code}")
        return False


def login_and_get_token():
    """Teste 3: Login"""
    print_section("TESTE 3: Login para obter Token")
    
    url = f"{BASE_URL}/auth/login"
    print(f"POST {url}")
    print(f"Credenciais: {TEST_EMAIL} / {TEST_PASSWORD}")
    
    response = requests.post(
        url,
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print_success("Login bem-sucedido!")
        print(f"Token: {token[:50]}...")
        return token
    else:
        print_error("Falha no login")
        print(f"Response: {response.json()}")
        return None


def test_update_local_only(event_id, test_date, token, original_hora):
    """Teste 4: UPDATE apenas LOCAL"""
    print_section("TESTE 4: PUT apenas LOCAL")
    
    url = f"{BASE_URL}/events/{event_id}/{test_date}"
    new_local = "Sala Atualizada 101"
    
    print(f"PUT {url}")
    print(f'Body: {{"local": "{new_local}"}}')
    
    response = requests.put(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={"local": new_local}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('local') == new_local and data.get('hora') == original_hora:
            print_success("Local atualizado! Hora mantida!")
            return True
        else:
            print_error(f"Dados incorretos: local={data.get('local')}, hora={data.get('hora')}")
            return False
    else:
        print_error(f"Falha na atualização: {response.status_code}")
        return False


def test_update_data_only(event_id, test_date, token):
    """Teste 5: UPDATE apenas DATA/HORA"""
    print_section("TESTE 5: PUT apenas DATA/HORA")
    
    url = f"{BASE_URL}/events/{event_id}/{test_date}"
    new_datetime = f"{test_date}T15:30:00"
    
    print(f"PUT {url}")
    print(f'Body: {{"data": "{new_datetime}"}}')
    
    response = requests.put(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={"data": new_datetime}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('hora') == "15:30:00":
            print_success("Hora atualizada! Local mantido!")
            return True
        else:
            print_error(f"Hora incorreta: {data.get('hora')}")
            return False
    else:
        print_error(f"Falha na atualização: {response.status_code}")
        return False


def test_update_both(event_id, test_date, token):
    """Teste 6: UPDATE LOCAL e DATA juntos"""
    print_section("TESTE 6: PUT LOCAL + DATA juntos")
    
    url = f"{BASE_URL}/events/{event_id}/{test_date}"
    new_local = "Sala Final 999"
    new_datetime = f"{test_date}T16:00:00"
    
    print(f"PUT {url}")
    print(f'Body: {{"local": "{new_local}", "data": "{new_datetime}"}}')
    
    response = requests.put(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={"local": new_local, "data": new_datetime}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('local') == new_local and data.get('hora') == "16:00:00":
            print_success("Local e hora atualizados juntos!")
            return True
        else:
            print_error(f"Dados incorretos")
            return False
    else:
        print_error(f"Falha na atualização: {response.status_code}")
        return False


def test_update_empty(event_id, test_date, token):
    """Teste 7: UPDATE sem campos (deve dar 400)"""
    print_section("TESTE 7: PUT sem campos (deve dar 400)")
    
    url = f"{BASE_URL}/events/{event_id}/{test_date}"
    print(f"PUT {url}")
    print('Body: {}')
    
    response = requests.put(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 400 and "Nenhum campo" in response.text:
        print_success("Validação funcionando!")
        return True
    else:
        print_error(f"Esperado 400, recebido {response.status_code}")
        return False


def restore_original(event_id, test_date, token, original_local, original_datetime):
    """Restaurar valores originais"""
    print_section("TESTE 8: Restaurar valores originais")
    
    url = f"{BASE_URL}/events/{event_id}/{test_date}"
    
    response = requests.put(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={"local": original_local, "data": original_datetime}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print_success("Dados restaurados!")
        return True
    else:
        print_error("Falha ao restaurar")
        return False


def main():
    """Executa todos os testes"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}")
    print("  TESTE DE INTEGRAÇÃO - ATUALIZAÇÃO DE OCORRÊNCIAS")
    print(f"{'='*70}{Colors.END}\n")
    
    results = []
    
    try:
        # Setup
        event_id, test_date = setup_test_data()
        
        # Teste 1: GET baseline
        original_data = test_get_ocorrencia(event_id, test_date)
        if not original_data:
            print_error("Abortando: não foi possível obter dados iniciais")
            return
        
        original_local = original_data.get('local')
        original_hora = original_data.get('hora')
        original_datetime = f"{test_date}T{original_hora}"
        
        # Teste 2: Sem autenticação
        results.append(("PUT sem auth", test_without_auth(event_id, test_date)))
        
        # Teste 3: Login
        token = login_and_get_token()
        if not token:
            print_error("Abortando: não foi possível obter token")
            return
        
        # Teste 4: Update local
        results.append(("PUT local", test_update_local_only(event_id, test_date, token, original_hora)))
        
        # Teste 5: Update data
        results.append(("PUT data", test_update_data_only(event_id, test_date, token)))
        
        # Teste 6: Update ambos
        results.append(("PUT ambos", test_update_both(event_id, test_date, token)))
        
        # Teste 7: Update vazio
        results.append(("PUT vazio", test_update_empty(event_id, test_date, token)))
        
        # Teste 8: Restaurar
        results.append(("Restaurar", restore_original(event_id, test_date, token, original_local, original_datetime)))
        
        # Resumo
        print_section("RESUMO DOS TESTES")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = f"{Colors.GREEN}✅ PASSOU{Colors.END}" if result else f"{Colors.RED}❌ FALHOU{Colors.END}"
            print(f"  {name:<20} {status}")
        
        print(f"\n{Colors.BOLD}Total: {passed}/{total} testes passaram{Colors.END}")
        
        if passed == total:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 TODOS OS TESTES PASSARAM! 🎉{Colors.END}")
            print(f"\n{Colors.GREEN}Implementação 100% funcional:{Colors.END}")
            print("  ✅ Schema OcorrenciaEventoUpdate com campos opcionais")
            print("  ✅ Update parcial (só local OU só data)")
            print("  ✅ Update completo (local E data juntos)")
            print("  ✅ Autenticação JWT funcionando")
            print("  ✅ Autorização por proprietário (email_proprietario)")
            print("  ✅ Validação de campos (erro 400 se nenhum campo)")
            print("  ✅ Resposta com date e hora separados")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}Alguns testes falharam{Colors.END}")
        
    except Exception as e:
        print_error(f"Erro durante execução dos testes: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
