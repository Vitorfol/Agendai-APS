#!/bin/bash

# Script para testar o endpoint de atualização de ocorrências de eventos
# Uso: ./scripts/test_update_ocorrencia.sh

set -e  # Para o script se houver erro

echo "=========================================="
echo "TESTE DE ATUALIZAÇÃO DE OCORRÊNCIA"
echo "=========================================="
echo ""

# Variáveis de configuração
API_URL="http://localhost:8000/api"
EMAIL="contato@uece.br"
PASSWORD="dedelbrabo"
ID_EVENTO=11
DATA_OCORRENCIA="2025-12-15"

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. LOGIN
echo -e "${BLUE}[1/7]${NC} Fazendo login..."
LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"${EMAIL}\", \"password\": \"${PASSWORD}\"}")

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
  echo "❌ Erro ao fazer login!"
  echo "Resposta: $LOGIN_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✓${NC} Login bem-sucedido!"
echo "Token: ${ACCESS_TOKEN:0:50}..."
echo ""

# 2. VER ESTADO INICIAL
echo -e "${BLUE}[2/7]${NC} Consultando estado inicial da ocorrência..."
INITIAL_STATE=$(curl -s "${API_URL}/events/${ID_EVENTO}/${DATA_OCORRENCIA}")
echo "Estado inicial:"
echo $INITIAL_STATE | python3 -m json.tool 2>/dev/null || echo $INITIAL_STATE
echo ""

# 3. ATUALIZAR APENAS O LOCAL
echo -e "${BLUE}[3/7]${NC} Atualizando APENAS o local..."
UPDATE_LOCAL=$(curl -s -X PUT "${API_URL}/events/${ID_EVENTO}/${DATA_OCORRENCIA}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"local": "Sala Teste Shell"}')
echo "Resultado:"
echo $UPDATE_LOCAL | python3 -m json.tool 2>/dev/null || echo $UPDATE_LOCAL
echo ""

# 4. ATUALIZAR APENAS A DATA/HORA
echo -e "${BLUE}[4/7]${NC} Atualizando APENAS a data/hora..."
UPDATE_DATA=$(curl -s -X PUT "${API_URL}/events/${ID_EVENTO}/${DATA_OCORRENCIA}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"data": "2025-12-15T15:30:00"}')
echo "Resultado:"
echo $UPDATE_DATA | python3 -m json.tool 2>/dev/null || echo $UPDATE_DATA
echo ""

# 5. ATUALIZAR AMBOS (LOCAL E DATA)
echo -e "${BLUE}[5/7]${NC} Atualizando AMBOS (local e data)..."
UPDATE_BOTH=$(curl -s -X PUT "${API_URL}/events/${ID_EVENTO}/${DATA_OCORRENCIA}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"local": "Auditório Principal", "data": "2025-12-15T17:00:00"}')
echo "Resultado:"
echo $UPDATE_BOTH | python3 -m json.tool 2>/dev/null || echo $UPDATE_BOTH
echo ""

# 6. VER ESTADO FINAL
echo -e "${BLUE}[6/7]${NC} Consultando estado final da ocorrência..."
FINAL_STATE=$(curl -s "${API_URL}/events/${ID_EVENTO}/${DATA_OCORRENCIA}")
echo "Estado final:"
echo $FINAL_STATE | python3 -m json.tool 2>/dev/null || echo $FINAL_STATE
echo ""

# 7. CANCELAR A OCORRÊNCIA (DELETE)
echo -e "${BLUE}[7/7]${NC} Cancelando a ocorrência..."
DELETE_RESPONSE=$(curl -s -X DELETE "${API_URL}/events/${ID_EVENTO}/${DATA_OCORRENCIA}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")
echo "Resultado:"
echo $DELETE_RESPONSE | python3 -m json.tool 2>/dev/null || echo $DELETE_RESPONSE
echo ""

# Verificar se foi deletada
echo "Verificando se a ocorrência foi deletada (deve retornar 404)..."
VERIFY_DELETE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "${API_URL}/events/${ID_EVENTO}/${DATA_OCORRENCIA}")
echo $VERIFY_DELETE
echo ""

echo "=========================================="
echo -e "${GREEN}✓ TODOS OS TESTES CONCLUÍDOS!${NC}"
echo "=========================================="
echo ""
echo -e "${YELLOW}COMO FAZER AS REQUESTS MANUALMENTE:${NC}"
echo ""
echo "1️⃣  Atualizar APENAS o local:"
echo "   curl -X PUT \"${API_URL}/events/${ID_EVENTO}/${DATA_OCORRENCIA}\" \\"
echo "     -H \"Authorization: Bearer \$TOKEN\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"local\": \"Nova Sala\"}'"
echo ""
echo "2️⃣  Atualizar APENAS a data/hora:"
echo "   curl -X PUT \"${API_URL}/events/${ID_EVENTO}/${DATA_OCORRENCIA}\" \\"
echo "     -H \"Authorization: Bearer \$TOKEN\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"data\": \"2025-12-15T14:00:00\"}'"
echo ""
echo "3️⃣  Atualizar AMBOS:"
echo "   curl -X PUT \"${API_URL}/events/${ID_EVENTO}/${DATA_OCORRENCIA}\" \\"
echo "     -H \"Authorization: Bearer \$TOKEN\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"local\": \"Auditório\", \"data\": \"2025-12-15T16:00:00\"}'"
echo ""
echo "4️⃣  Cancelar a ocorrência:"
echo "   curl -X DELETE \"${API_URL}/events/${ID_EVENTO}/${DATA_OCORRENCIA}\" \\"
echo "     -H \"Authorization: Bearer \$TOKEN\""
echo ""
echo -e "${YELLOW}Dica:${NC} Você pode editar as variáveis no topo do script para testar com diferentes valores:"
echo "  - EMAIL, PASSWORD: Credenciais de login"
echo "  - ID_EVENTO: ID do evento a atualizar"
echo "  - DATA_OCORRENCIA: Data da ocorrência (formato: YYYY-MM-DD)"
