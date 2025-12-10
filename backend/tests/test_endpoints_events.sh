#!/bin/bash

# Script de teste completo dos endpoints de eventos usando curl
# Testa especialmente os endpoints que foram reordenados

set -e  # Para em caso de erro

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
API_URL="http://localhost:8000/api"
EMAIL="contato@uece.br"
PASSWORD="dedelbrabo"

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}🧪 TESTE COMPLETO - ENDPOINTS DE EVENTOS (via CURL)${NC}"
echo -e "${BLUE}============================================================${NC}\n"

# Função para fazer requests e mostrar resultado
make_request() {
    local method=$1
    local endpoint=$2
    local description=$3
    local data=$4
    local token=$5
    
    echo -e "${YELLOW}➤ ${description}${NC}"
    echo -e "  ${method} ${endpoint}"
    
    if [ -n "$token" ]; then
        if [ -n "$data" ]; then
            response=$(curl -s -X ${method} "${API_URL}${endpoint}" \
                -H "Authorization: Bearer ${token}" \
                -H "Content-Type: application/json" \
                -d "${data}" \
                -w "\nHTTP_CODE:%{http_code}")
        else
            response=$(curl -s -X ${method} "${API_URL}${endpoint}" \
                -H "Authorization: Bearer ${token}" \
                -w "\nHTTP_CODE:%{http_code}")
        fi
    else
        if [ -n "$data" ]; then
            response=$(curl -s -X ${method} "${API_URL}${endpoint}" \
                -H "Content-Type: application/json" \
                -d "${data}" \
                -w "\nHTTP_CODE:%{http_code}")
        else
            response=$(curl -s -X ${method} "${API_URL}${endpoint}" \
                -w "\nHTTP_CODE:%{http_code}")
        fi
    fi
    
    http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE/d')
    
    if [[ $http_code -ge 200 && $http_code -lt 300 ]]; then
        echo -e "  ${GREEN}✅ Status: ${http_code}${NC}"
        echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
    else
        echo -e "  ${RED}❌ Status: ${http_code}${NC}"
        echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
    fi
    echo ""
}

# 1. LOGIN
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}📝 PASSO 1: Autenticação${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

login_response=$(curl -s -X POST "${API_URL}/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}")

TOKEN=$(echo $login_response | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', 'null'))")

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✅ Login realizado com sucesso!${NC}"
    echo -e "   Token: ${TOKEN:0:20}...${NC}\n"
else
    echo -e "${RED}❌ Falha no login!${NC}"
    echo $login_response | jq '.'
    exit 1
fi

# 2. CRIAR EVENTO PARA TESTES
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}📝 PASSO 2: Criar Evento de Teste${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

evento_data='{
  "evento": {
    "nome": "Teste Curl - Aula de APS",
    "descricao": "Evento criado via curl para testes",
    "id_universidade": 2,
    "data_inicio": "2025-12-16T09:00:00",
    "data_termino": "2025-12-16T11:00:00",
    "recorrencia": "semanal",
    "categoria": "Aula",
    "email_proprietario": "contato@uece.br"
  },
  "disciplina": null,
  "dias": null
}'

evento_response=$(curl -s -X POST "${API_URL}/events/" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "${evento_data}")

EVENTO_ID=$(echo $evento_response | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 'null'))")

if [ "$EVENTO_ID" != "null" ] && [ -n "$EVENTO_ID" ]; then
    echo -e "${GREEN}✅ Evento criado com sucesso! ID: ${EVENTO_ID}${NC}\n"
else
    echo -e "${RED}❌ Falha ao criar evento!${NC}"
    echo $evento_response | jq '.'
    exit 1
fi

# 3. TESTAR ENDPOINTS QUE FORAM REORDENADOS
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}📝 PASSO 3: Testar Endpoints com {date}${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

# GET /{id_evento}/{date} - Obter ocorrência em data específica
make_request "GET" "/events/${EVENTO_ID}/2025-12-16" \
    "Obter ocorrência do evento na data 2025-12-16" \
    "" \
    "$TOKEN"

make_request "GET" "/events/${EVENTO_ID}/2025-12-23" \
    "Obter ocorrência do evento na data 2025-12-23 (próxima semana)" \
    "" \
    "$TOKEN"

# PUT /{id_evento}/{date} - Atualizar ocorrência
update_data='{
  "local": "Laboratório de Informática - Sala 101",
  "data": "2025-12-16T10:00:00"
}'

make_request "PUT" "/events/${EVENTO_ID}/2025-12-16" \
    "Atualizar local e horário da ocorrência de 2025-12-16" \
    "$update_data" \
    "$TOKEN"

# Verificar se a atualização funcionou
make_request "GET" "/events/${EVENTO_ID}/2025-12-16" \
    "Verificar atualização da ocorrência" \
    "" \
    "$TOKEN"

# 4. TESTAR ENDPOINTS DE PARTICIPANTS (que estavam conflitando)
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}📝 PASSO 4: Testar Endpoints de Participants${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

# POST /{id_evento}/participants - Adicionar participante individual
make_request "POST" "/events/${EVENTO_ID}/participants?email_usuario=pedro.teste@uece.br" \
    "Adicionar participante individual (Pedro)" \
    "" \
    "$TOKEN"

# POST /{id_evento}/participants - Adicionar via curso
make_request "POST" "/events/${EVENTO_ID}/participants?email_usuario=computacao@uece.br" \
    "Adicionar todos os alunos do curso de Computação" \
    "" \
    "$TOKEN"

# POST /{id_evento}/participants - Adicionar todos do domínio
make_request "POST" "/events/${EVENTO_ID}/participants?email_usuario=todos@uece.br" \
    "Adicionar todos os usuários com @uece.br" \
    "" \
    "$TOKEN"

# GET /{id_evento}/participants - Listar participantes
make_request "GET" "/events/${EVENTO_ID}/participants" \
    "Listar todos os participantes do evento" \
    "" \
    ""

# DELETE /{id_evento}/participants - Remover participante
make_request "DELETE" "/events/${EVENTO_ID}/participants?email_usuario=pedro.teste@uece.br" \
    "Remover participante (Pedro)" \
    "" \
    "$TOKEN"

# GET /{id_evento}/participants - Listar participantes após remoção
make_request "GET" "/events/${EVENTO_ID}/participants" \
    "Listar participantes após remoção" \
    "" \
    ""

# 5. LIMPAR DADOS DE TESTE
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}📝 PASSO 5: Limpeza (Deletar evento de teste)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

make_request "DELETE" "/events/${EVENTO_ID}" \
    "Deletar evento de teste" \
    "" \
    "$TOKEN"

echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ TODOS OS TESTES CONCLUÍDOS!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
