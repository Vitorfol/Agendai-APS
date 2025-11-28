# Testes de Integração — backend

Este arquivo descreve como rodar os testes de integração que verificam autenticação (/auth/login) e o endpoint `/users/me`.

Local dos testes
- `backend/tests/test_integration_auth.py`

Requisitos
- Os testes usam `pytest` e `requests`. Estes pacotes foram adicionados a `requirements.txt` e serão instalados durante o build da imagem Docker.

Rodando os testes (dentro do container `backend`)

- Executar todos os testes do arquivo (saída concisa):

```bash
docker compose exec backend sh -c "pytest -q tests/test_integration_auth.py"
```

- Executar um teste específico (ex.: login + /users/me):

```bash
docker compose exec backend sh -c "pytest -q tests/test_integration_auth.py::test_login_success_and_users_me -q"
```

- Executar com logs detalhados (verbose):

```bash
docker compose exec backend sh -c "pytest -vv tests/test_integration_auth.py"
```

Explicação das flags
- `-q` (quiet): imprime menos saída — útil para runs rápidos/CI.
- `-vv` (very verbose): mostra saída detalhada dos testes e logs, útil para depuração.

Se o `pytest` não estiver disponível na imagem/container
- Se a imagem utilizada pelo serviço ainda não foi reconstruída com as dependências de teste, você verá `pytest: not found`.
- Solução rápida (instala temporária dentro do container):

```bash
docker compose exec backend sh -c "pip install --no-cache-dir pytest requests && cd /app && pytest -q tests/test_integration_auth.py"
```

Mas atenção: esta instalação é temporária e será perdida se você remover o container. A forma correta é reconstruir a imagem (ver abaixo).

Reconstruir imagem (instala pytest permanentemente)

Se você alterou `requirements.txt` (por exemplo, adicionou `pytest`/`requests`), reconstrua a imagem do backend:

```bash
docker compose build backend
docker compose up -d
```

Ou em um passo:

```bash
docker compose up --build -d
```

Notas sobre volumes / banco
- `docker compose down` por padrão não remove volumes; só `docker compose down -v` remove volumes.
- Se você usa volumes nomeados ou bind mounts para o banco, seus dados serão preservados ao dar `down` e `up` normalmente.

Debug / inspeção
- Ver logs do backend:

```bash
docker compose logs backend --tail 200
```

- Listar arquivos dentro do container (útil para confirmar paths):

```bash
docker compose exec backend sh -c "ls -la /app || true; ls -la /app/tests || true"
```

Integração contínua (sugestão)
- Adicione um job no CI (GitHub Actions / GitLab CI) que executa `pytest -q tests/test_integration_auth.py` contra uma instância do serviço (p.ex. usando `services` ou `docker-compose` no runner).

Perguntas frequentes rápidas
- Q: qual comando usar para logs detalhados? A: `pytest -vv`.
- Q: onde estão os testes? A: `backend/tests/test_integration_auth.py`.
- Q: por que os testes falharam antes? A: normalmente porque a imagem não tinha `pytest` instalado ou o path do teste estava incorreto. Os comandos acima resolvem ambos os casos.

---

Se quiser, eu crio também um pequeno script `scripts/run-tests.sh` que executa o build (quando necessário), sobe os containers e roda os testes automaticamente.
