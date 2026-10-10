from pathlib import Path
from threading import Lock
from app.config import config
from app.models import Settings, Transcription

class Storage:
    def __init__(self) -> None:
        self._lock = Lock()
        self.settings_path = config.data_dir / "settings.json"
    def _path(self, transcription_id: str) -> Path:
        return config.data_dir / f"transcription-{transcription_id}.json"
    def save_transcription(self, item: Transcription) -> None:
        with self._lock:
            self._path(item.id).write_text(item.model_dump_json(indent=2), encoding="utf-8")
    def load_transcription(self, transcription_id: str) -> Transcription | None:
        path = self._path(transcription_id)
        return Transcription.model_validate_json(path.read_text(encoding="utf-8")) if path.exists() else None
    def load_settings(self) -> Settings:
        if not self.settings_path.exists(): return Settings()
        try: return Settings.model_validate_json(self.settings_path.read_text(encoding="utf-8"))
        except Exception: return Settings()
    def save_settings(self, settings: Settings) -> None:
        with self._lock:
            self.settings_path.write_text(settings.model_dump_json(indent=2), encoding="utf-8")
storage = Storage()
