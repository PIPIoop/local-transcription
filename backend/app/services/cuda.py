import os
from pathlib import Path


def cuda_device_available() -> bool:
    try:
        import ctranslate2
        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


def _dll_exists(name: str) -> bool:
    search_paths = [Path(value) for value in os.environ.get("PATH", "").split(os.pathsep) if value]
    try:
        import ctranslate2
        search_paths.append(Path(ctranslate2.__file__).resolve().parent)
    except Exception:
        pass
    return any((directory / name).is_file() for directory in search_paths)


def cuda_runtime_issue() -> str | None:
    if not cuda_device_available():
        return "Совместимая NVIDIA GPU не обнаружена."
    if os.name != "nt":
        return None
    missing = [name for name in ("cublas64_12.dll", "cudnn64_9.dll") if not _dll_exists(name)]
    if missing:
        return "Не найдены CUDA-библиотеки: " + ", ".join(missing)
    return None


def cuda_runtime_available() -> bool:
    return cuda_runtime_issue() is None
