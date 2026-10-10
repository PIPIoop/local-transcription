import httpx
from app.models import AISettings
from app.prompts import QUESTION_FALLBACK, SCENARIOS, SYSTEM_PROMPT
class OllamaError(RuntimeError): pass
class OllamaService:
    def __init__(self, settings: AISettings):
        self.settings, self.base_url = settings, settings.ollama_url.rstrip("/")
    async def status(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags"); response.raise_for_status()
                models = [m["name"] for m in response.json().get("models", [])]
                return {"connected": True, "models": models, "modelAvailable": self.settings.model in models}
        except Exception: return {"connected": False, "models": [], "modelAvailable": False}
    async def analyze(self, transcript: str, scenario: str, question: str | None = None) -> tuple[str, str]:
        if scenario == "question":
            title, task = "Вопрос по транскрипции", (question or "").strip() + f"\nЕсли ответа нет в тексте, ответь точно: «{QUESTION_FALLBACK}»"
        else: title, task = SCENARIOS[scenario]
        budget = max(1500, self.settings.context_length - 3000)
        if max(1, len(transcript)//4) <= budget: return title, await self._generate(transcript, task)
        chunks = self._chunks(transcript, budget*4); partials = []
        for index, chunk in enumerate(chunks):
            partials.append(await self._generate(chunk, f"{task}\nЭто часть {index+1} из {len(chunks)}. Извлеки релевантные факты, сохраняя спикеров и timestamps."))
        combined = "\n\n--- ЧАСТЬ ---\n".join(partials)
        return title, await self._generate(combined, f"{task}\nОбъедини результаты без потери и дубликатов. Не добавляй новых фактов.", "ПРОМЕЖУТОЧНЫЕ РЕЗУЛЬТАТЫ")
    async def _generate(self, text: str, task: str, label: str = "ТРАНСКРИПЦИЯ") -> str:
        payload = {"model": self.settings.model, "prompt": f"{SYSTEM_PROMPT}\n\n{label}:\n{text}\n\nЗАДАЧА:\n{task}", "stream": False, "options": {"temperature": self.settings.temperature, "num_ctx": self.settings.context_length}}
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(600, connect=10)) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload); response.raise_for_status()
                return response.json()["response"].strip()
        except httpx.ConnectError as exc: raise OllamaError("Не удалось подключиться к Ollama. Убедитесь, что Ollama запущен.") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404: raise OllamaError(f"Модель {self.settings.model} не найдена в Ollama.") from exc
            raise OllamaError("Ollama вернул ошибку генерации.") from exc
        except Exception as exc: raise OllamaError("Не удалось завершить AI-анализ.") from exc
    @staticmethod
    def _chunks(text: str, max_chars: int) -> list[str]:
        chunks, current, size = [], [], 0
        for line in text.splitlines():
            if current and size + len(line) + 1 > max_chars: chunks.append("\n".join(current)); current, size = [], 0
            current.append(line); size += len(line)+1
        if current: chunks.append("\n".join(current))
        return chunks
