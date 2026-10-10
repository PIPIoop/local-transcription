import json
import subprocess
from pathlib import Path

class MediaError(RuntimeError): pass

def probe_duration(path: Path) -> float:
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)], capture_output=True, text=True, timeout=30, check=True)
        return float(json.loads(result.stdout)["format"]["duration"])
    except FileNotFoundError as exc:
        raise MediaError("FFmpeg не найден. Установите FFmpeg и добавьте его в PATH.") from exc
    except Exception as exc:
        raise MediaError("Не удалось прочитать медиафайл. Проверьте формат и целостность файла.") from exc
