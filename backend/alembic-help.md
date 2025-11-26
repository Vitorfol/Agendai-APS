# Como usar o alembic
Nesse Texto eu explico os principais comandos necessários para usar o alembic

O alembic é um versionador de banco de dados, utilizado para controlar melhor a modelagem do seu banco e evitar perda de dados.
## Atualizar a modelagem do banco

Após iniciar o *docker compose*, é possivel que você encontre o seu banco de dados vazio. se esse for o caso, basta executar a seguinte linha de comando:

_docker compose exec backend alembic upgrade head_

Isso vai fazer com que o banco de dados fique na versão mais atual disponivel.

## Modificar a modelagem do banco

Caso você queira modificar o banco de dados (adicionar uma tabela, modificar uma coluna), para evitar a perda de dados execute: 

_docker compose exec backend alembic revision --autogenerate -m "seu commit"_

## Desatualizar a modelagem do banco

Caso seja necessário voltar atrás no seu banco de dados, apenas execute

_docker compose exec backend alembic downgrade -1_

## Iniciar o alembic

Este comando só deve ser utilizado em casos extremos, ele cria um novo alembic com uma nova configuração, perdendo todo o histórico de versões anterior

_docker compose exec backend alembic init alembic_