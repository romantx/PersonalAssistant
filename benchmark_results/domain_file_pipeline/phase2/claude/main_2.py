import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    app_name: str = "File Pipeline API"
    version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Redis Settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_url: Optional[str] = None
    
    # File Upload Settings
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    upload_dir: str = "./uploads"
    allowed_extensions: list = [".txt", ".pdf", ".docx", ".xlsx", ".csv", ".json"]
    
    # Celery Settings
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.redis_url:
            self.redis_url = f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
        
        # Ensure upload directory exists
        os.makedirs(self.upload_dir, exist_ok=True)

settings = Settings()