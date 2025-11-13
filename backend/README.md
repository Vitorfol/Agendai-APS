# Agendai - Backend

This is the repository for the Agendai Backend, an Academic Calendar System.

## 🧱 Architecture and Technologies

The Backend is developed using a Three-Layer Architecture based on the RESTful communication style, ensuring modularity and scalability.

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Language/Framework** | **Python** & **FastAPI** | High-performance framework for API construction. |
| **Asynchronous Server** | **Uvicorn** | ASGI server to run FastAPI applications. |
| **Database** | **MySQL** | Database Management System. |
| **ORM/Driver** | **SQLAlchemy** & **PyMySQL** | ORM for object-relational mapping and connection driver. |

## 🛡️ Authentication and Core Logic (Middlewares/Dependencies)

Authentication and Authorization logic (like JWT validation and role checking) are primarily implemented using **FastAPI Dependencies** (which serve the function of traditional middlewares).

- **`core/security.py`**: Contains the logic to **validate JWTs, hash passwords**, and define dependency functions to **authenticate and authorize** users based on their role (Aluno, Professor, Admin) before accessing protected routes.

## 📁 Code Structure (src)

The Python code adheres to the separation of concerns principle (Service Layer Pattern):

| Directory | Content and Responsibility | Example Files |
| :--- | :--- | :--- |
| `api/` | **Presentation Layer (Controllers).** Receives HTTP requests, handles dependency injection, and returns responses. It delegates complex tasks to the `services/` layer. | `endpoints_auth.py`, `endpoints_notifications.py` |
| `core/` | **Configuration and Security.** Essential application logic and settings. | `config.py` (Environment Variables), `security.py` |
| `database/` | **Access and Connection.** Configuration for MySQL connection and **database migrations (Alembic)**. | `connection.py` |
| `models/` | **DB Mapping.** SQLAlchemy classes that represent MySQL tables. | `model_user.py`, `model_event.py` |
| `schemas/` | **Validation/Contract.** Pydantic classes defining the input and output (JSON) format for API data. | `schema_user.py`, `schema_event.py` |
| `services/` | **Business Logic.** Where core business rules are implemented (e.g., frequency calculation, recurring event generation, **sending notifications**). Called by the `api/` endpoints. | `service_auth.py`, `service_events.py`, `service_notifications.py` |
| `main.py` | FastAPI application entry point. | |

## ✅ Next Critical Steps (Implied Tasks)

Before starting on specific endpoints, the team must address these foundational tasks:

1.  **Database Migrations (B-24):** Set up Alembic (or similar) to manage database schema creation and updates.
2.  **Recurring Event Logic (B-23):** Implement the core logic in `service_events.py` to generate multiple occurrences from a single recurring event definition.
3.  **Email Service Setup (B-25):** Configure the external SMTP service for notifications and password recovery.
4.  **Logging and Error Handling (B-26):** Implement global logging and custom exception handlers.

## ⚙️ Containerization

The project uses Docker to ensure a consistent development environment.

- **`Dockerfile`**: Defines the Python environment and Backend dependencies.
- **`docker-compose.yml`**: Orchestrates the Backend container and the MySQL database service.
- **`.env.example`**: Should be copied to `.env` and populated with MySQL credentials and security keys.



💡 Exemplo Prático do Fluxo de Dados: Cadastro de UsuárioPara entender a interação entre as camadas, veja o fluxo completo ao receber uma requisição de cadastro de novo usuário (POST /auth/register):1. Camada de Apresentação (api/endpoints_auth.py)A função do endpoint é declarar o que precisa para a requisição funcionar (o Schema para validação) e delegar a execução para a camada de Serviço.from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..schemas import schema_user
from ..services import service_auth
from ..database.connection import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=schema_user.UserResponse)
def register_user_endpoint(
    # [1] FASTAPI/PYDANTIC: Faz a validação automática do JSON contra o Schema
    user_data: schema_user.UserCreate, 
    # [2] DEPENDENCY: Injeta a sessão do banco de dados (que será usada no Service)
    db: Session = Depends(get_db) 
):
    # [3] DELEGAÇÃO: Chama a implementação da lógica de negócio na camada de Services.
    new_user = service_auth.create_user(db, user_data)
    
    # [7] RESPOSTA: Retorna o objeto UserResponse, que será serializado em JSON para o cliente.
    return new_user
2. Camada de Serviço (services/service_auth.py)Esta camada recebe os dados já validados e implementa as regras de negócio antes de interagir com o banco de dados.from sqlalchemy.orm import Session
from ..models import model_user
from ..schemas import schema_user
from ..core import security # Para hashear a senha

def create_user(db: Session, user: schema_user.UserCreate):
    # [4] LÓGICA DE NEGÓCIO: Verifica se o usuário já existe (Regra de Unicidade)
    db_user = db.query(model_user.User).filter(model_user.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # [5] LÓGICA DE SEGURANÇA: Hashing da Senha (Chama o Core)
    hashed_password = security.get_password_hash(user.password)

    # [6] ACESSO A DADOS: Cria o objeto Model e salva no DB (interação com o Model)
    db_user = model_user.User(
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user) # Atualiza o objeto para obter o ID gerado pelo BD
    
    # [7] RETORNO: Retorna o objeto criado (pronto para ser usado na resposta da API)
    return db_user
Resumo da Inversão de Controle:O API não sabe como a senha é criptografada ou como o dado é salvo; ele apenas chama a implementação no Service.O Service não sabe nada sobre HTTP (status codes); ele apenas executa a lógica e interage com o Model e o Core.