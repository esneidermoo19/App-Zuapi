"""Gestor de jobs en memoria, compartido por todos los modulos de conversion."""

from __future__ import annotations

import shutil
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.config import settings

QUEUED = "queued"
PROCESSING = "processing"
DONE = "done"
FAILED = "failed"


class JobResponse(BaseModel):
    """Payload de un job segun el contrato specs/openapi.yaml."""

    job_id: str
    status: str
    error: str | None = None
    download_url: str | None = None


@dataclass
class JobRecord:
    """Estado interno de un job."""

    job_id: str
    status: str = QUEUED
    error: str | None = None
    result_path: Path | None = None
    filename: str | None = None
    workdir: Path | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


_jobs: dict[str, JobRecord] = {}
_lock = threading.Lock()


def create_job() -> JobRecord:
    """Crea un job en estado queued y devuelve su estado interno."""
    purge_expired()
    record = JobRecord(job_id=uuid.uuid4().hex)
    with _lock:
        _jobs[record.job_id] = record
    return record


def get_job(job_id: str) -> JobRecord | None:
    with _lock:
        return _jobs.get(job_id)


def delete_job(job_id: str) -> None:
    with _lock:
        record = _jobs.pop(job_id, None)
    if record is not None and record.workdir is not None:
        shutil.rmtree(record.workdir, ignore_errors=True)


def _update(job_id: str, **changes: object) -> None:
    with _lock:
        record = _jobs.get(job_id)
        if record is None:
            return
        for key, value in changes.items():
            setattr(record, key, value)
        record.updated_at = datetime.now(timezone.utc)


def mark_processing(job_id: str) -> None:
    _update(job_id, status=PROCESSING)


def mark_done(job_id: str, result_path: Path, filename: str) -> None:
    _update(job_id, status=DONE, result_path=result_path, filename=filename, error=None)


def mark_failed(job_id: str, error: str) -> None:
    _update(job_id, status=FAILED, error=error, result_path=None)


def to_response(record: JobRecord) -> JobResponse:
    download_url = None
    if record.status == DONE:
        download_url = f"/api/v1/jobs/{record.job_id}/download"
    return JobResponse(
        job_id=record.job_id,
        status=record.status,
        error=record.error,
        download_url=download_url,
    )


def purge_expired(ttl_minutes: int | None = None) -> None:
    """Elimina los jobs (y sus archivos) que superaron el TTL configurado."""
    ttl = settings.file_ttl_minutes if ttl_minutes is None else ttl_minutes
    limit = datetime.now(timezone.utc) - timedelta(minutes=ttl)
    expired: list[JobRecord] = []
    with _lock:
        for job_id, record in list(_jobs.items()):
            if record.updated_at < limit:
                expired.append(record)
                del _jobs[job_id]
    for record in expired:
        if record.workdir is not None:
            shutil.rmtree(record.workdir, ignore_errors=True)


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobResponse)
def get_job_status(job_id: str) -> JobResponse:
    record = get_job(job_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "job_not_found", "message": "El job no existe."},
        )
    return to_response(record)


@router.get("/{job_id}/download")
def download_job(job_id: str) -> FileResponse:
    record = get_job(job_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "job_not_found", "message": "El job no existe."},
        )
    if record.status != DONE or record.result_path is None or not record.result_path.is_file():
        raise HTTPException(
            status_code=409,
            detail={
                "code": "job_not_ready",
                "message": "El job aun no ha terminado correctamente.",
            },
        )
    return FileResponse(
        record.result_path,
        filename=record.filename or record.result_path.name,
        media_type="application/octet-stream",
    )
