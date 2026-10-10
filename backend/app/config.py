from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LTA_", env_file=".env", extra="ignore")
    base_dir: Path = Path(__file__).resolve().parents[1]
    max_upload_mb: int = 2048
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    @property
    def data_dir(self) -> Path: return self.base_dir / "data"
    @property
    def upload_dir(self) -> Path: return self.base_dir / "uploads"

config = AppConfig()
config.data_dir.mkdir(parents=True, exist_ok=True)
config.upload_dir.mkdir(parents=True, exist_ok=True)
