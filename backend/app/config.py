from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


class Settings(BaseSettings):

    """Application settings."""
    
    database_url: str 
    redis_url: str 
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None
    environment: str = "development"
    cors_origins: str = "http://localhost:5173,https://fastmission-fastfrontend.utvssk.easypanel.host/,https://fast-mission.vercel.app/"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    secret_key: str = "CHANGE-ME-IN-PRODUCTION-use-openssl-rand-hex-32"

    IA_API_KEY: str | None = None  # URL do serviço de IA (ajustar conforme necessário)
    COSMOS_API_KEY: str | None = None  # Chave de API para Cosmos DB (ajustar conforme necessário)

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
        )
    


    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def is_testing(self) -> bool:
        return self.environment.lower() == "testing"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    @property
    def celery_broker(self) -> str:
        return self.celery_broker_url or self.redis_url
    
    @property
    def celery_backend(self) -> str:
        return self.celery_result_backend or self.redis_url
    

    def model_post_init(self, __context) -> None:
        valid_envs = ["development", "production", "testing"]
        if self.environment not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}")

        if not self.database_url:
            raise ValueError(
                "Database URL is required. Set DATABASE_URL in your .env file or environment variables." \
                "Configure in .env: DATABASE_URL=postgresql://user:password..."
            )
        

        if self.is_production and self.secret_key == "CHANGE-ME-IN-PRODUCTION-use-openssl-rand-hex-32":
            raise ValueError(
                "Secret key is required in production. Set SECRET_KEY in your .env file or environment variables."
                "Openssl rand -hex 32"
            )

        if not self.IA_API_KEY:
            print("⚠️ Warning: IA_API_KEY is not set. AI features will be disabled.")   

settings = Settings()


