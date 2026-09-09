from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_host: str = "127.0.0.1"
    central_port: int = 8015
    mcp_port: int = 9015
    asset_mcp_port: int = 9016
    threat_mcp_port: int = 9017
    central_database_path: Path = Path("data/registry.db")
    firewall_database_path: Path = Path("mcp_servers/firewall_logs.db")
    app_api_key: str
    mcp_shared_key: str
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.1:8b"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
