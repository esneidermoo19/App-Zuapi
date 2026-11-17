"""Logica de conversion de audio: validacion de la subida y uso de FFmpeg."""

from __future__ import annotations

import shutil
import subprocess
import threading
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.core.jobs import JobRecord, mark_done, mark_failed, mark_processing

ALLOWED_FORMATS = ("mp3", "wav", "ogg", "flac", "m4a")

CODEC_ARGS: dict[str, list[str]] = {
    "mp3": ["-c:a", "libmp3lame"],
    "wav": ["-c:a", "pcm_s16le"],
    "ogg": ["-c:a", "libvorbis"],
    "flac": ["-c:a", "flac"],
    "m4a": ["-c:a", "aac"],
}

CHUNK_SIZE = 1024 * 1024


def normalize_format(target_format: str) -> str:
    return (target_format or "").strip().lower().lstrip(".")


def validate_target_format(target_format: str) -> str:
    """Valida el formato de salida pedido y devuelve el valor normalizado."""
    value = normalize_format(target_format)
    if value not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "unsupported_format",
                "message": (
                    f"Formato de salida no soportado: '{target_format}'. "
                    f"Permitidos: {', '.join(ALLOWED_FORMATS)}."
                ),
            },
        )
    return value


def validate_source_extension(filename: str | None) -> str:
    """Valida la extension del archivo subido y devuelve la extension normalizada."""
    suffix = Path(filename or "").suffix.lower().lstrip(".")
    if suffix not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "unsupported_format",
                "message": (
                    f"Formato de entrada no soportado: '{filename}'. "
                    f"Permitidos: {', '.join(ALLOWED_FORMATS)}."
                ),
            },
        )
    return suffix


def max_upload_bytes() -> int:
    """Limite de tamano leido de la configuracion en cada peticion."""
    return settings.max_upload_mb * 1024 * 1024


def build_output_name(filename: str | None, target_format: str) -> str:
    stem = Path(filename or "audio").stem
    safe = "".join(char if char.isalnum() or char in "-_" else "_" for char in stem).strip("._")
    return f"{safe or 'audio'}.{target_format}"


def job_workdir(job_id: str) -> Path:
    return Path(settings.storage_dir) / job_id


def save_upload(file: UploadFile, job: JobRecord) -> Path:
    """Guarda la subida en el storage aplicando el limite de tamano configurado."""
    workdir = job_workdir(job.job_id)
    workdir.mkdir(parents=True, exist_ok=True)
    job.workdir = workdir
    destination = workdir / f"input.{validate_source_extension(file.filename)}"
    limit = max_upload_bytes()
    written = 0
    with destination.open("wb") as handle:
        while chunk := file.file.read(CHUNK_SIZE):
            written += len(chunk)
            if written > limit:
                handle.close()
                shutil.rmtree(workdir, ignore_errors=True)
                raise HTTPException(
                    status_code=413,
                    detail={
                        "code": "file_too_large",
                        "message": (
                            f"El archivo supera el limite de {settings.max_upload_mb} MB."
                        ),
                    },
                )
            handle.write(chunk)
    return destination


def build_command(ffmpeg: str, source: Path, destination: Path, target_format: str) -> list[str]:
    """Construye el comando de FFmpeg como lista de argumentos (nunca con shell)."""
    return [
        ffmpeg,
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        *CODEC_ARGS[target_format],
        str(destination),
    ]


def start_conversion(job: JobRecord, source: Path, target_format: str, output_name: str) -> None:
    """Lanza la conversion en segundo plano sin bloquear la respuesta HTTP."""
    threading.Thread(
        target=run_conversion,
        args=(job, source, target_format, output_name),
        daemon=True,
    ).start()


def run_conversion(job: JobRecord, source: Path, target_format: str, output_name: str) -> None:
    """Convierte el archivo en segundo plano y actualiza el estado del job."""
    mark_processing(job.job_id)
    destination = job_workdir(job.job_id) / f"output.{target_format}"
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        mark_failed(job.job_id, "ffmpeg_unavailable")
        return
    try:
        completed = subprocess.run(
            build_command(ffmpeg, source, destination, target_format),
            capture_output=True,
            check=False,
        )
    except OSError:
        mark_failed(job.job_id, "conversion_error")
        return
    if completed.returncode != 0 or not destination.is_file() or destination.stat().st_size == 0:
        mark_failed(job.job_id, "invalid_file")
        return
    mark_done(job.job_id, destination, output_name)
