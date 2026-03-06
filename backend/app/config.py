from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys
    GROQ_API_KEY: str = ""
    TAVILY_API_KEY: str = ""
    
    # Model Configurations
    LLM_MODEL: str = "llama-3.1-8b-instant"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600
    
    # Retry Configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1
    
    # Logging
    LOG_LEVEL: str = "INFO"

settings = Settings()
