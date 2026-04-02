from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    openrouter_api_key: str = ""
    telegram_bot_token: str = ""
    imap_host: str = "127.0.0.1"
    imap_port: int = 1143
    smtp_port: int = 1025
    proton_email: str = ""
    proton_password: str = ""
    gmail_email: str = ""
    gmail_app_password: str = ""
    xai_api_key: str = ""
    canary_mode_enabled: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
