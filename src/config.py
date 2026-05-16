from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    base_dir: Path = Path(__file__).parent
    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    max_upload_size_bytes: int = 5 * 1024 * 1024
    # items_per_page: int = 10

    database_url: str

    reset_token_expire_minutes: int = 60

    mail_server: str
    mail_port: int
    mail_username: str
    mail_password: SecretStr
    mail_from: str
    mail_use_tls: bool
    frontend_url: str


settings = Settings()  # type: ignore[call-arg]
print(settings.database_url)