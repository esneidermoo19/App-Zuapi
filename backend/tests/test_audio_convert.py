from app.core.config import settings


def post_audio(client, name, content, target_format):
    return client.post(
        "/api/v1/audio/convert",
        files={"file": (name, content, "audio/mpeg")},
        data={"target_format": target_format},
    )


def test_conversion_exitosa_mp3_a_wav(client, sample_mp3, wait_for_job):
    response = post_audio(client, "ejemplo.mp3", sample_mp3.read_bytes(), "wav")
    assert response.status_code == 202
    job = response.json()
    assert job["status"] == "queued"

    final = wait_for_job(client, job["job_id"])
    assert final["status"] == "done"

    download = client.get(f"/api/v1/jobs/{job['job_id']}/download")
    assert download.status_code == 200
    assert ".wav" in download.headers["content-disposition"]
    assert download.content[:4] == b"RIFF"


def test_formato_de_salida_no_soportado(client):
    response = post_audio(client, "ejemplo.mp3", b"datos", "xyz")
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "unsupported_format"


def test_archivo_corrupto(client, ffmpeg, wait_for_job):
    response = post_audio(client, "roto.mp3", b"esto no es audio", "wav")
    assert response.status_code == 202

    final = wait_for_job(client, response.json()["job_id"])
    assert final["status"] == "failed"
    assert final["error"] == "invalid_file"


def test_archivo_demasiado_grande(client, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_mb", 1)
    contenido = b"0" * (2 * 1024 * 1024)
    response = post_audio(client, "grande.mp3", contenido, "wav")
    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "file_too_large"


def test_job_inexistente(client):
    response = client.get("/api/v1/jobs/no-existe")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "job_not_found"
