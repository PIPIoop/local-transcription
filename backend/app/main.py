import uuid
from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from app.config import config
from app.models import AnalyzeRequest, AnalyzeResponse, FileInfo, Settings, Transcription, TranscriptionPatch
from app.services.hardware import transcription_recommendation
from app.services.jobs import job_manager
from app.services.ollama import OllamaError, OllamaService
from app.services.storage import storage
from app.services.transcription import run_transcription
app = FastAPI(title="Local Transcript AI", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in config.cors_origins.split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
ALLOWED = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".mp4", ".webm", ".mov", ".mkv"}
@app.on_event("startup")
def recover_interrupted_transcriptions():
    for data_path in config.data_dir.glob("transcription-*.json"):
        try:
            item = Transcription.model_validate_json(data_path.read_text(encoding="utf-8"))
            if item.status not in {"queued", "processing"}:
                continue
            uploads = list(config.upload_dir.glob(f"{item.id}.*"))
            if not uploads:
                item.status = "error"
                item.error = "Обработка была прервана, а временный файл не найден. Загрузите файл снова."
                storage.save_transcription(item)
                continue
            job_manager.start(item, uploads[0], storage.load_settings().transcription)
        except Exception:
            continue

@app.get("/api/transcription/recommendation")
def get_transcription_recommendation():
    return transcription_recommendation()
@app.get("/api/health")
def health(): return {"status": "ok"}
@app.post("/api/transcribe", response_model=Transcription, status_code=202)
async def transcribe(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED: raise HTTPException(415, "Неподдерживаемый формат файла.")
    identifier = uuid.uuid4().hex; target = config.upload_dir / f"{identifier}{suffix}"; size = 0
    with target.open("wb") as output:
        while chunk := await file.read(1024*1024):
            size += len(chunk)
            if size > config.max_upload_mb*1024*1024:
                output.close(); target.unlink(missing_ok=True); raise HTTPException(413, f"Файл больше допустимых {config.max_upload_mb} МБ.")
            output.write(chunk)
    item = Transcription(id=identifier, file=FileInfo(name=file.filename or target.name, size=size, format=suffix.removeprefix(".")))
    storage.save_transcription(item); job_manager.start(item, target, storage.load_settings().transcription)
    return item
@app.post("/api/transcription/{transcription_id}/cancel", response_model=Transcription)
def cancel_transcription(transcription_id: str):
    item = job_manager.cancel(transcription_id)
    if not item:
        raise HTTPException(404, "Транскрипция не найдена.")
    return item

@app.on_event("shutdown")
def stop_transcription_processes():
    job_manager.shutdown()
@app.get("/api/transcription/active/current", response_model=Transcription)
def get_active_transcription():
    candidates = sorted(
        config.data_dir.glob("transcription-*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for data_path in candidates:
        try:
            item = Transcription.model_validate_json(data_path.read_text(encoding="utf-8"))
            if item.status in {"queued", "processing"}:
                return item
        except Exception:
            continue
    raise HTTPException(404, "Активная транскрипция не найдена.")
@app.get("/api/transcription/{transcription_id}", response_model=Transcription)
def get_transcription(transcription_id: str):
    item = storage.load_transcription(transcription_id)
    if not item: raise HTTPException(404, "Транскрипция не найдена.")
    return item
@app.patch("/api/transcription/{transcription_id}", response_model=Transcription)
def patch_transcription(transcription_id: str, patch: TranscriptionPatch):
    item = storage.load_transcription(transcription_id)
    if not item: raise HTTPException(404, "Транскрипция не найдена.")
    if patch.speakers is not None: item.speakers = patch.speakers
    if patch.segments is not None: item.segments = patch.segments
    storage.save_transcription(item); return item
@app.post("/api/ai/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    item = storage.load_transcription(request.transcription_id)
    if not item or item.status != "completed": raise HTTPException(404, "Готовая транскрипция не найдена.")
    names = {speaker.id: speaker.name for speaker in item.speakers}
    transcript = "\n".join(f"[{format_time(s.start)}] {names.get(s.speaker, s.speaker)}: {s.text}" for s in item.segments)
    try:
        title, content = await OllamaService(storage.load_settings().ai).analyze(transcript, request.scenario, request.question)
        return AnalyzeResponse(scenario=request.scenario, title=title, content=content)
    except OllamaError as exc: raise HTTPException(503, str(exc)) from exc
@app.get("/api/ollama/status")
async def ollama_status(): return await OllamaService(storage.load_settings().ai).status()
@app.get("/api/ollama/models")
async def ollama_models(): return await OllamaService(storage.load_settings().ai).status()
@app.get("/api/settings", response_model=Settings)
def get_settings(): return storage.load_settings()
@app.put("/api/settings", response_model=Settings)
def put_settings(settings: Settings): storage.save_settings(settings); return settings
def format_time(seconds: float) -> str:
    value = max(0, int(seconds)); return f"{value//3600:02d}:{value%3600//60:02d}:{value%60:02d}"



