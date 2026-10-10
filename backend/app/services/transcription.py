import logging
import time
from pathlib import Path
from faster_whisper import WhisperModel
from app.models import Segment, Speaker, Transcription, TranscriptionSettings
from app.services.cuda import cuda_runtime_available, cuda_runtime_issue
from app.services.diarization import DiarizationUnavailable, diarize, speaker_at
from app.services.media import probe_duration
from app.services.storage import storage


logger = logging.getLogger(__name__)

def run_transcription(item: Transcription, path: Path, settings: TranscriptionSettings) -> None:
    started = time.monotonic()
    item.error = None
    item.segments = []
    item.speakers = []

    def update(stage: str, progress: int) -> None:
        item.stage = stage
        item.progress = max(item.progress, min(progress, 99))
        item.elapsed = time.monotonic() - started
        storage.save_transcription(item)

    try:
        item.status = "processing"
        item.progress = 0
        update("Подготовка файла", 8)
        item.file.duration = probe_duration(path)
        update("Загрузка модели Whisper", 18)
        if settings.device == "auto":
            device = "cuda" if cuda_runtime_available() else "cpu"
        else:
            device = settings.device
        if device == "cuda" and not cuda_runtime_available():
            raise RuntimeError(f"CUDA недоступна: {cuda_runtime_issue()}")
        compute_type = "float16" if device == "cuda" else "int8"
        model = WhisperModel(settings.whisper_model, device=device, compute_type=compute_type)
        update(f"Распознавание речи · {settings.whisper_model} / {device.upper()}", 30)
        raw_segments, info = model.transcribe(
            str(path),
            language=None if settings.language == "auto" else settings.language,
            vad_filter=True,
        )
        collected = []
        duration = max(item.file.duration, 1)
        last_saved = 0.0
        for segment in raw_segments:
            collected.append(segment)
            now = time.monotonic()
            if now - last_saved >= 0.75:
                ratio = min(max(segment.end / duration, 0), 1)
                progress = 30 + int(ratio * 47)
                update(
                    f"Распознавание речи · {_format_time(segment.end)} из {_format_time(duration)}",
                    progress,
                )
                last_saved = now
        item.language = info.language or settings.language
        turns = []
        if settings.diarization:
            update("Определение спикеров", 78)
            turns = diarize(path, settings.speaker_count)
        update("Формирование транскрипции", 90)
        labels: list[str] = []
        for segment in collected:
            label = speaker_at(segment.start, segment.end, turns) if turns else "SPEAKER_00"
            if label not in labels:
                labels.append(label)
            item.segments.append(
                Segment(
                    id=f"segment_{len(item.segments) + 1}",
                    start=segment.start,
                    end=segment.end,
                    speaker=f"speaker_{labels.index(label) + 1}",
                    text=segment.text.strip(),
                )
            )
        item.speakers = [
            Speaker(id=f"speaker_{index + 1}", name=f"Спикер {index + 1}")
            for index in range(max(1, len(labels)))
        ]
        item.status, item.stage, item.progress = "completed", "Готово", 100
    except DiarizationUnavailable as exc:
        item.status, item.error = "error", str(exc)
    except Exception as exc:
        logger.exception("Transcription %s failed", item.id)
        item.status = "error"
        details = str(exc).lower()
        if "cublas" in details or "cudnn" in details or "cuda недоступна" in details:
            item.error = "CUDA настроена не полностью. Выберите устройство Auto/CPU или установите CUDA 12 и cuDNN 9."
        elif "out of memory" in details or "memory" in details and "allocate" in details:
            item.error = "Недостаточно памяти. Выберите меньшую модель Whisper или CPU."
        else:
            item.error = "Транскрибация завершилась ошибкой. Подробности записаны в backend.err.log."
    finally:
        item.elapsed = time.monotonic() - started
        storage.save_transcription(item)
        if item.status in {"completed", "error"}:
            path.unlink(missing_ok=True)


def _format_time(seconds: float) -> str:
    value = max(0, int(seconds))
    return f"{value // 60:02d}:{value % 60:02d}"

