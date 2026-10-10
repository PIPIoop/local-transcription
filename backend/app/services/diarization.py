from pathlib import Path
class DiarizationUnavailable(RuntimeError): pass

def diarize(path: Path, speaker_count: int | None = None) -> list[tuple[float, float, str]]:
    try:
        import os
        from pyannote.audio import Pipeline
    except ImportError as exc:
        raise DiarizationUnavailable("Diarization не установлена. Установите requirements-diarization.txt.") from exc
    token = os.getenv("HF_TOKEN")
    if not token: raise DiarizationUnavailable("Для diarization задайте HF_TOKEN.")
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=token)
    result = pipeline(str(path), **({"num_speakers": speaker_count} if speaker_count else {}))
    return [(turn.start, turn.end, label) for turn, _, label in result.itertracks(yield_label=True)]

def speaker_at(start: float, end: float, turns: list[tuple[float, float, str]]) -> str:
    midpoint = (start + end) / 2
    for turn_start, turn_end, label in turns:
        if turn_start <= midpoint <= turn_end: return label
    return "SPEAKER_00"
