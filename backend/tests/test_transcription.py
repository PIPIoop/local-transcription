import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.models import FileInfo, Transcription, TranscriptionSettings
from app.services.hardware import transcription_recommendation
from app.services.transcription import run_transcription


class FakeWhisper:
    def __init__(self, *args, **kwargs):
        pass

    def transcribe(self, *args, **kwargs):
        segments = [
            SimpleNamespace(start=0.0, end=25.0, text="Первая реплика"),
            SimpleNamespace(start=25.0, end=75.0, text="Вторая реплика"),
        ]
        return iter(segments), SimpleNamespace(language="ru")


class TranscriptionTests(unittest.TestCase):
    def test_recommendation_has_supported_model(self):
        result = transcription_recommendation()
        self.assertIn(result["recommended_model"], {"tiny", "base", "small", "medium", "large-v3"})
        self.assertIn(result["recommended_device"], {"cpu", "cuda"})
        self.assertGreater(result["hardware"]["cpu_threads"], 0)

    def test_streaming_progress_is_persisted(self):
        item = Transcription(id="test", file=FileInfo(name="test.wav", size=10, format="wav"))
        snapshots = []
        with patch("app.services.transcription.WhisperModel", FakeWhisper), \
             patch("app.services.transcription.probe_duration", return_value=100.0), \
             patch("app.services.transcription.storage.save_transcription", side_effect=lambda value: snapshots.append((value.progress, value.stage))):
            run_transcription(item, Path("missing-test-file.wav"), TranscriptionSettings(whisper_model="tiny", device="cpu"))
        self.assertEqual(item.status, "completed")
        self.assertEqual(item.progress, 100)
        self.assertEqual(len(item.segments), 2)
        self.assertTrue(any(progress > 30 and "из" in stage for progress, stage in snapshots))


if __name__ == "__main__":
    unittest.main()
