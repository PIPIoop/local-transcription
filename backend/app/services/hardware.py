import ctypes
import os
import platform
import subprocess
from app.services.cuda import cuda_device_available, cuda_runtime_issue

MODEL_PROFILES = [
    {"model": "tiny", "speed": "Очень быстро", "accuracy": "Базовая", "memory_gb": 1, "best_for": "Черновики и слабые ПК"},
    {"model": "base", "speed": "Быстро", "accuracy": "Хорошая", "memory_gb": 2, "best_for": "Короткие записи и экономия ресурсов"},
    {"model": "small", "speed": "Сбалансированно", "accuracy": "Высокая", "memory_gb": 4, "best_for": "Встречи на русском языке"},
    {"model": "medium", "speed": "Медленнее", "accuracy": "Очень высокая", "memory_gb": 7, "best_for": "Сложная речь и шумные записи"},
    {"model": "large-v3", "speed": "Медленно", "accuracy": "Максимальная", "memory_gb": 11, "best_for": "Максимальное качество на мощном GPU"},
]


def transcription_recommendation() -> dict:
    ram_gb = round(_total_ram_bytes() / (1024 ** 3), 1)
    cpu_threads = os.cpu_count() or 1
    cuda_detected = cuda_device_available()
    cuda_issue = cuda_runtime_issue() if cuda_detected else None
    cuda = cuda_detected and cuda_issue is None
    vram_gb = _vram_gb() if cuda_detected else 0.0

    if cuda and vram_gb >= 20 and ram_gb >= 32:
        model, device = "large-v3", "cuda"
        reason = "GPU располагает достаточным объёмом VRAM для максимального качества."
    elif cuda and vram_gb >= 8:
        model, device = "medium", "cuda"
        reason = "GPU подходит для модели medium: высокая точность с разумным временем обработки длинных записей."
    elif cuda and vram_gb >= 3:
        model, device = "small", "cuda"
        reason = "Модель small даст хороший баланс качества и скорости на доступном GPU."
    elif ram_gb >= 16 and cpu_threads >= 8:
        model, device = "small", "cpu"
        reason = (f"GPU найден, но CUDA runtime не готов: {cuda_issue}. Используем CPU." if cuda_detected and cuda_issue else "Для CPU модель small — оптимальный баланс качества и времени обработки.")
    elif ram_gb >= 8:
        model, device = "base", "cpu"
        reason = "Модель base снизит нагрузку на память и останется достаточно точной."
    else:
        model, device = "tiny", "cpu"
        reason = "Модель tiny рекомендована из-за ограниченного объёма оперативной памяти."

    return {
        "recommended_model": model,
        "recommended_device": device,
        "reason": reason,
        "hardware": {
            "os": platform.system(),
            "cpu_threads": cpu_threads,
            "ram_gb": ram_gb,
            "cuda": cuda,
            "cuda_detected": cuda_detected,
            "cuda_issue": cuda_issue,
            "vram_gb": vram_gb,
        },
        "models": MODEL_PROFILES,
    }


def _vram_gb() -> float:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        )
        values = [float(line.strip()) for line in result.stdout.splitlines() if line.strip()]
        return round(max(values) / 1024, 1) if values else 0.0
    except Exception:
        return 0.0


def _total_ram_bytes() -> int:
    if os.name == "nt":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.c_ulong),
                ("memory_load", ctypes.c_ulong),
                ("total_phys", ctypes.c_ulonglong),
                ("avail_phys", ctypes.c_ulonglong),
                ("total_page_file", ctypes.c_ulonglong),
                ("avail_page_file", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong),
                ("avail_virtual", ctypes.c_ulonglong),
                ("avail_extended_virtual", ctypes.c_ulonglong),
            ]
        status = MemoryStatus()
        status.length = ctypes.sizeof(MemoryStatus)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
        return int(status.total_phys)
    try:
        return int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
    except (AttributeError, ValueError):
        return 0


