import shutil
import subprocess
import time

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path / "storage"))
    return TestClient(app)


@pytest.fixture
def ffmpeg():
    path = shutil.which("ffmpeg")
    if path is None:
        pytest.skip("ffmpeg no esta instalado")
    return path


@pytest.fixture
def sample_mp3(tmp_path, ffmpeg):
    path = tmp_path / "ejemplo.mp3"
    subprocess.run(
        [ffmpeg, "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1", str(path)],
        check=True,
        capture_output=True,
    )
    return path


@pytest.fixture
def wait_for_job():
    def _wait(client, job_id, timeout=15.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            body = client.get(f"/api/v1/jobs/{job_id}").json()
            if body["status"] in ("done", "failed"):
                return body
            time.sleep(0.2)
        raise AssertionError(f"El job {job_id} no termino en {timeout}s")

    return _wait
