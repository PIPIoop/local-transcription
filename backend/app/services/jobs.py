import multiprocessing
from pathlib import Path
from threading import Lock

from app.models import Transcription, TranscriptionSettings
from app.services.storage import storage
from app.services.transcription import run_transcription


class TranscriptionJobManager:
    def __init__(self) -> None:
        self._context = multiprocessing.get_context("spawn")
        self._jobs: dict[str, multiprocessing.Process] = {}
        self._lock = Lock()

    def start(self, item: Transcription, path: Path, settings: TranscriptionSettings) -> None:
        with self._lock:
            existing = self._jobs.get(item.id)
            if existing and existing.is_alive():
                return
            process = self._context.Process(
                target=run_transcription,
                args=(item, path, settings),
                name=f"whisper-{item.id[:8]}",
                daemon=True,
            )
            process.start()
            self._jobs[item.id] = process

    def cancel(self, transcription_id: str) -> Transcription | None:
        with self._lock:
            process = self._jobs.pop(transcription_id, None)
        if process and process.is_alive():
            process.terminate()
            process.join(timeout=5)
            if process.is_alive() and hasattr(process, "kill"):
                process.kill()
                process.join(timeout=2)
        item = storage.load_transcription(transcription_id)
        if not item:
            return None
        if item.status in {"queued", "processing"}:
            item.status = "cancelled"
            item.stage = "Отменено пользователем"
            item.error = None
            storage.save_transcription(item)
        for upload in item_uploads(transcription_id):
            upload.unlink(missing_ok=True)
        return item

    def shutdown(self) -> None:
        with self._lock:
            processes = list(self._jobs.values())
            self._jobs.clear()
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=3)


def item_uploads(transcription_id: str) -> list[Path]:
    from app.config import config
    return list(config.upload_dir.glob(f"{transcription_id}.*"))


job_manager = TranscriptionJobManager()
