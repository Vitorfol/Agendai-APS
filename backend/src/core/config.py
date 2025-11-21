from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Agendai"
    ALGORITHM: str = "HS256"
    SECRET_KEY: str 
    ACCESS_TOKEN_EXPIRE_MINUTES: int 
    REFRESH_TOKEN_EXPIRE_DAYS: int 
    
    class Config:
        env_file = ".env"
        
settings = Settings()
