# Como usar o Alembic

Este guia explica os principais comandos necessários para usar o Alembic no dia a dia do desenvolvimento.

O Alembic é um versionador de banco de dados (ferramenta de migração) para SQLAlchemy, utilizado para controlar a evolução do esquema do seu banco de dados de forma segura e reproduzível.

## 1. Comandos Básicos

### Atualizar o banco para a última versão (Upgrade)

Após iniciar o *docker compose*, ou baixar atualizações de código de colegas, seu banco pode estar desatualizado. Para aplicar todas as mudanças pendentes:

`docker compose exec backend alembic upgrade head`

### Criar uma nova migração (Revision)

Sempre que você alterar seus arquivos de `models.py` (adicionar tabelas, mudar colunas), você precisa gerar um arquivo de revisão. O flag `--autogenerate` compara seu código com o banco atual:

`docker compose exec backend alembic revision --autogenerate -m "descreva sua mudança aqui"`

*Dica: Sempre abra o arquivo gerado em `alembic/versions` para conferir se ele detectou as mudanças corretamente antes de aplicar.*

### Desfazer mudanças (Downgrade)

Caso precise desfazer a última migração aplicada (útil se algo quebrou):

`docker compose exec backend alembic downgrade -1`

Para voltar para uma versão específica (onde `<revision_id>` é o hash da versão):
`docker compose exec backend alembic downgrade <revision_id>`

Para voltar ao estado vazio (base):
`docker compose exec backend alembic downgrade base`

## 2. Comandos de Consulta e Controle

### Verificar o histórico (History)

Para ver a lista de todas as revisões criadas no projeto (mostra os IDs e mensagens):

`docker compose exec backend alembic history`

Para ver com mais detalhes (data, hora):
`docker compose exec backend alembic history --verbose`

### Verificar versão atual (Current)

Para saber em qual revisão exata o seu banco de dados está parado no momento:

`docker compose exec backend alembic current`

### Forçar uma versão (Stamp)

O comando `stamp` é usado quando você quer atualizar a tabela de controle do Alembic (`alembic_version`) **sem rodar** os scripts de migração. Isso é útil se você restaurou um backup ou corrigiu o banco manualmente e só precisa "avisar" o Alembic que está tudo certo.

Marcar o banco como atualizado (head):
`docker compose exec backend alembic stamp head`

Marcar o banco como estando em uma revisão específica:
`docker compose exec backend alembic stamp <revision_id>`

## 3. Situações Extremas

### Reiniciar as migrações do Zero (Reset em Dev)

Se o ambiente de desenvolvimento virou uma bagunça e você quer limpar o histórico de migrações:

1. Apague todos os arquivos `.py` dentro da pasta `alembic/versions` (mas não apague a pasta em si).

2. Apague a tabela `alembic_version` no seu banco de dados (comando SQL: `DROP TABLE alembic_version;`).

3. Gere uma nova migração inicial:
   `docker compose exec backend alembic revision --autogenerate -m "migracao_inicial"`

4. Aplique a nova migração:
   `docker compose exec backend alembic upgrade head`

### Iniciar o Alembic (Init)

Este comando cria a estrutura de pastas e configuração inicial (`alembic.ini`, `env.py`). Só deve ser usado na **criação do projeto**. Se executado novamente, pode sobrescrever configurações.

`docker compose exec backend alembic init alembic`