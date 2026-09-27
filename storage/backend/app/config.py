from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
STORAGE_DIR = ROOT_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
PROCESSED_DIR = STORAGE_DIR / "processed"
EVENT_DIR = STORAGE_DIR / "events"

for folder in (UPLOAD_DIR, PROCESSED_DIR, EVENT_DIR):
    folder.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    app_name: str = "BorderVision AI"
    environment: str = "development"
    yolo_model: str = "yolo11n.pt"
    confidence_threshold: float = 0.35
    iou_threshold: float = 0.50
    max_upload_mb: int = 500
    database_url: str = "sqlite:///./bordervision.db"
    backend_cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [x.strip() for x in self.backend_cors_origins.split(",") if x.strip()]


settings = Settings()
