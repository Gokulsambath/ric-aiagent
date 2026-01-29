from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List, Optional
import json
from pathlib import Path
from app.schema.api_config_dto import APIKeyConfig

class DatabaseSettings(BaseSettings):
    database_type: str = Field(default="postgresql", alias="DATABASE_TYPE")
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    
    postgres_driver: str = Field(default="postgresql+psycopg2", alias="POSTGRES_DRIVER")
    postgres_user: str = Field(default="ricagoapi_user", alias="POSTGRES_USER")
    postgres_password: str = Field(default="changeme123", alias="POSTGRES_PASSWORD")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="ricagoapi", alias="POSTGRES_DB")

    def get_db_url(self) -> str:
        if self.database_url:
            return self.database_url
        
        # Default to PostgreSQL
        return f"{self.postgres_driver}://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

class MailSettings(BaseSettings):
    mail_username: str = Field(alias="MAIL_USERNAME")
    mail_password: str = Field(alias="MAIL_PASSWORD")
    mail_from: str = Field(alias="MAIL_FROM")
    mail_port: int = Field(default=465, alias="MAIL_PORT")
    mail_server: str = Field(default="smtp.gmail.com", alias="MAIL_SERVER")
    mail_starttls: bool = Field(default=False, alias="MAIL_STARTTLS")
    mail_ssl_tls: bool = Field(default=True, alias="MAIL_SSL_TLS")
    use_credentials: bool = Field(default=True, alias="USE_CREDENTIALS")
    validate_certs: bool = Field(default=True, alias="VALIDATE_CERTS")
    mail_to: str = Field(default="rica@ricago.com", alias="MAIL_TO")
    support_email: str = Field(default="support@ricago.com", alias="SUPPORT_EMAIL")
    mail_provider: str = Field(default="gmail", alias="MAIL_PROVIDER")

    model_config = SettingsConfigDict(extra="ignore", env_file=".env", env_file_encoding="utf-8")

class OllamaSettings(BaseSettings):
    default_model: str = Field(default="gpt-oss:120b-cloud", alias="DEFAULT_MODEL")
    ollama_api_url: str = Field(default="https://ollama.com", alias="OLLAMA_API_URL")
    
    model_config = SettingsConfigDict(extra="ignore", env_file=".env", env_file_encoding="utf-8")

class OpenAISettings(BaseSettings):
    api_key: str = Field(default="e81e1546fd0b42eda763f75ea88f1b57.vbfSc4Z9xLPmc2EDA-lRH7uI", alias="OPENAI_API_KEY")
    api_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_API_URL") 
    model: str = Field(default="gpt-oss:120b-cloud", alias="OPENAI_MODEL")
    
    model_config = SettingsConfigDict(extra="ignore", env_file=".env", env_file_encoding="utf-8")

class BotpressSettings(BaseSettings):
    botpress_url: str = Field(default="http://botpress:3000/botpress", alias="BOTPRESS_URL")
    webhook_id: str = Field(default="test", alias="BOTPRESS_WEBHOOK_ID")
    bot_id: str = Field(default="test", alias="BOTPRESS_BOT_ID")
    
    model_config = SettingsConfigDict(extra="ignore", env_file=".env", env_file_encoding="utf-8")

class ServerSettings(BaseSettings):
    cors_urls: List[str] = Field(
        default=[
            "https://ricagoapi.com",
            "https://www.ricagoapi.com",
            "http://127.0.0.1:5500",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
            "http://127.0.0.1:60105",
            "http://localhost:5500",
            "http://localhost:3000",
            "http://localhost:8000",
            "https://ricagoapi.onrender.com",
            "https://api.ricagoapi.com",
            "http://localhost:4000",
            "http://127.0.0.1:4000",
            "https://dev.ricago.in",
            "https://dev.ricago.in:3001"
            "https://test.ricago.in",
            "https://test.ricago.in:3001"
            "https://ai.ricago.com",
            "https://ai.ricago.com:3001"
        ], 
        alias="CORS_URLS"
    )
    secret_key: str = Field(default="RICAGO", alias="SECRET_KEY")
    api_name: str = Field(default="RicagoAPI Server", alias="API_NAME")
    version: str = Field(default="1.0.1", alias="VERSION")
    
    model_config = SettingsConfigDict(extra="ignore", env_file=".env", env_file_encoding="utf-8")

def load_api_keys_from_file() -> List[APIKeyConfig]:
    try:
        json_path = Path("app/configs/api_key_config.json")
        if json_path.exists():
            with open(json_path, 'r') as f:
                data = json.load(f)
                return [APIKeyConfig(**k) for k in data.get("api_keys", [])]
    except Exception as e:
        print(f"Warning: Failed to load API keys from file: {e}")
    return []

class SecuritySettings(BaseSettings):
    api_keys: List[APIKeyConfig] = Field(default_factory=load_api_keys_from_file)

class RedisSettings(BaseSettings):
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")

    model_config = SettingsConfigDict(extra="ignore", env_file=".env", env_file_encoding="utf-8")

class AppSettings(BaseSettings):
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    mail: MailSettings = Field(default_factory=MailSettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    botpress: BotpressSettings = Field(default_factory=BotpressSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Singleton instance
settings = AppSettings()
