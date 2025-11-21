# 🐳 Guia Rápido de Docker Compose para Desenvolvedores

Este guia é para todos os desenvolvedores que trabalham no projeto `agendai`. Ele explica como subir o ambiente de desenvolvimento usando Docker Compose e como lidar com as mudanças de código e dependências.

## 📦 1. Arquitetura do Ambiente

Nosso ambiente é definido pelos arquivos `Dockerfile` e `docker-compose.yml`, contendo dois serviços principais:

* **`backend` (Porta 8000):** Nossa aplicação Python (FastAPI).
    * **Hot-Reload (`--reload`):** Está ativo. O código (`./backend`) é mapeado diretamente para o container (**Bind Mount**), permitindo que você salve um arquivo local e veja a mudança instantaneamente.
* **`db` (Porta 3307):** Servidor MySQL 8.4.
    * **Persistência de Dados:** Os dados são salvos em um **Volume Nomeado** (`db_data`), o que significa que o banco de dados e as tabelas persistem mesmo após o `docker compose down`.

## 🚀 2. Comandos Essenciais (O Bê-á-bá)

| Comando | O que faz | Cenário de Uso |
| :--- | :--- | :--- |
| **`docker compose up --build -d`** | **Constroi** as imagens, **cria** os containers e inicia em segundo plano (`-d`). | **Sempre na 1ª vez** ou após mudar o `Dockerfile` / `requirements.txt`. |
| **`docker compose up -d`** | Inicia os containers a partir das imagens já existentes. | Se você deu `down` anteriormente e quer subir tudo rapidamente. |
| **`docker compose down`** | Para e **remove** os containers e a rede, mas **PRESERVA** o volume de dados (`db_data`). | Ao finalizar o trabalho para liberar recursos da sua máquina. |
| **`docker compose ps`** | Verifica o status dos serviços (`Up` ou `Exited`). | Para confirmar que o `db` e o `backend` estão rodando. |

## 🔄 3. Fluxo de Trabalho de Desenvolvimento

O fluxo de trabalho varia dependendo do que foi alterado.

### A. Mudanças Apenas no Código (`utils.py`, `main.py`)

**Regra:** Graças ao **Bind Mount** e ao **`--reload`**, o Docker lida com isso automaticamente.

| Ação | Comando Necessário | Explicação |
| :--- | :--- | :--- |
| **Você (Localmente)** | Nenhum. | O Uvicorn vê o arquivo salvo e reinicia o processo Python automaticamente. |
| **Colegas (Após `git pull`)** | `docker compose restart backend` | Garante que o processo do Uvicorn pare e comece de novo, carregando o novo código puxado do Git. |

### B. Mudanças na Estrutura ou Dependências

**Regra:** Mudanças que afetam o ambiente base exigem a reconstrução da imagem.

| Arquivo Alterado | Comando Necessário | Razão |
| :--- | :--- | :--- |
| **`Dockerfile`** | `docker compose up --build -d` | A imagem precisa ser reconstruída para aplicar as novas instruções. |
| **`requirements.txt`** | `docker compose up --build -d` | O `pip install` é executado durante o *build*. É preciso refazê-lo para instalar novas dependências. |
| **Portas/Variáveis de Ambiente** | `docker compose up -d` | O container precisa ser recriado para carregar as novas configurações de *runtime*. |

## 🧪 4. Como Rodar Comandos e Scripts Avulsos

Use o comando `exec` para rodar comandos pontuais (como scripts de população de dados, migrações ou testes) **dentro** do container `backend` onde o ambiente Python está configurado.

**Sintaxe:** `docker compose exec [NOME_DO_SERVIÇO] [COMANDO]`

| Tarefa | Comando de Exemplo |
| :--- | :--- |
| **Rodar um Script** | `docker compose exec backend python popule.py` |
| **Abrir o Terminal** | `docker compose exec backend /bin/bash` |
| **Rodar Testes** | `docker compose exec backend pytest` |

---

## 🛠️ Dicas de Configuração (DBeaver)

* **Host:** `localhost`
* **Porta:** `3307` (Mapeada de `3306` para sua máquina)
* **Usuário:** `root`
* **Senha:** `admin123`
* **Database:** `agendai`

**Lembrete:** Seus dados persistem no volume `agendai_db_data`. Você só precisa dar `up` e re-conectar no DBeaver, sem a necessidade de criar uma nova conexão.

---

## 🏁 5. Iniciando a Aplicação Principal (Onde está o `main.py`?)

Não se preocupe em rodar o `main.py`! O Docker Compose lida com isso automaticamente:

1.  **Onde está o comando?** O comando que roda o `main.py` (via Uvicorn) está na propriedade **`command`** do serviço `backend`.
2.  **O que o `up` faz?** Quando você executa **`docker compose up -d`** (ou com `--build`), ele faz duas coisas simultâneas:
    * **Serviço `db`:** Inicia o servidor MySQL (porta 3307).
    * **Serviço `backend`:** Executa o `command: uvicorn src.main:app ...` automaticamente.
3.  **Resultado Final:** Se ambos estiverem no status `Up` (verifique com `docker compose ps`), a sua aplicação principal está rodando e acessível via `http://localhost:8000`.

---

## 🛠️ Dicas de Configuração (DBeaver)

* **Host:** `localhost`
* **Porta:** `3307` (Mapeada de `3306` para sua máquina)
* **Usuário:** `root`
* **Senha:** `admin123`
* **Database:** `agendai`

**Lembrete:** Seus dados persistem no volume `agendai_db_data`. Você só precisa dar `up` e re-conectar no DBeaver, sem a necessidade de criar uma nova conexão.



## Fluxo trabalho

Parar: docker compose down
Voltar: docker compose up -d