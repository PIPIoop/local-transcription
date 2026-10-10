import unittest
from unittest.mock import patch

from app.config import config
from app.models import FileInfo, Transcription
from app.services.jobs import TranscriptionJobManager
from app.services.storage import storage


class FakeProcess:
    def __init__(self, *args, **kwargs):
        self.alive = False
        self.terminated = False
    def start(self): self.alive = True
    def is_alive(self): return self.alive
    def terminate(self): self.terminated = True; self.alive = False
    def join(self, timeout=None): pass


class FakeContext:
    def __init__(self): self.process = None
    def Process(self, *args, **kwargs):
        self.process = FakeProcess()
        return self.process


class CancellationTests(unittest.TestCase):
    def test_running_job_can_be_cancelled(self):
        identifier = "unit_cancel_job"
        item = Transcription(id=identifier, status="processing", file=FileInfo(name="test.wav", size=1, format="wav"))
        storage.save_transcription(item)
        upload = config.upload_dir / f"{identifier}.wav"
        upload.write_bytes(b"test")
        manager = TranscriptionJobManager()
        context = FakeContext()
        manager._context = context
        try:
            manager.start(item, upload, storage.load_settings().transcription)
            result = manager.cancel(identifier)
            self.assertTrue(context.process.terminated)
            self.assertEqual(result.status, "cancelled")
            self.assertFalse(upload.exists())
        finally:
            (config.data_dir / f"transcription-{identifier}.json").unlink(missing_ok=True)
            upload.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
