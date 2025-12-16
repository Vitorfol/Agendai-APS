from pydantic_settings import BaseSettings, SettingsConfigDict

import datetime

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Agendai"
    
    # JWT Configuration
    ALGORITHM: str = "HS256"
    SECRET_KEY: str # Deve ser carregada do ambiente/arquivo
    ACCESS_TOKEN_EXPIRE_MINUTES: int # Deve ser carregada
    REFRESH_TOKEN_EXPIRE_DAYS: int # Deve ser carregada

    DATABASE_USER: str 
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_NAME: str

    # SMTP Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    model_config = SettingsConfigDict(
        env_file=".env"
        # O padrão 'extra='forbid'' está OK se todos os campos estão declarados.
    )
        
settings = Settings()