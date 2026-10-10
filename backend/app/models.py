from typing import Literal
from pydantic import BaseModel, Field

class Segment(BaseModel):
    id: str
    start: float
    end: float
    speaker: str
    text: str

class Speaker(BaseModel):
    id: str
    name: str

class FileInfo(BaseModel):
    name: str
    size: int
    duration: float = 0
    format: str

class Transcription(BaseModel):
    id: str
    status: Literal["queued", "processing", "completed", "error", "cancelled"] = "queued"
    stage: str = "Подготовка файла"
    progress: int = 0
    elapsed: float = 0
    file: FileInfo
    language: str = "auto"
    speakers: list[Speaker] = Field(default_factory=list)
    segments: list[Segment] = Field(default_factory=list)
    error: str | None = None

class TranscriptionPatch(BaseModel):
    speakers: list[Speaker] | None = None
    segments: list[Segment] | None = None

class TranscriptionSettings(BaseModel):
    whisper_model: str = "small"
    language: str = "auto"
    device: Literal["auto", "cpu", "cuda"] = "auto"
    diarization: bool = False
    speaker_count: int | None = Field(default=None, ge=1, le=20)

class AISettings(BaseModel):
    ollama_url: str = "http://localhost:11434"
    model: str = "qwen3:8b"
    temperature: float = Field(default=0.2, ge=0, le=2)
    context_length: int = Field(default=32768, ge=2048, le=262144)

class Settings(BaseModel):
    transcription: TranscriptionSettings = Field(default_factory=TranscriptionSettings)
    ai: AISettings = Field(default_factory=AISettings)

class AnalyzeRequest(BaseModel):
    transcription_id: str
    scenario: Literal["summary", "tasks", "minutes", "meetings", "question"]
    question: str | None = Field(default=None, max_length=4000)

class AnalyzeResponse(BaseModel):
    scenario: str
    title: str
    content: str

