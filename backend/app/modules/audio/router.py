from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile

from app.core import jobs
from app.core.jobs import JobResponse
from app.modules.audio import service

router = APIRouter(prefix="/audio", tags=["audio"])


@router.post("/convert", status_code=202, response_model=JobResponse)
def convert_audio(
    file: Annotated[UploadFile, File()],
    target_format: Annotated[str, Form()],
) -> JobResponse:
    """Crea un job de conversion de audio y responde 202 con el job en cola."""
    target = service.validate_target_format(target_format)
    service.validate_source_extension(file.filename)

    job = jobs.create_job()
    try:
        source = service.save_upload(file, job)
    except Exception:
        jobs.delete_job(job.job_id)
        raise

    output_name = service.build_output_name(file.filename, target)
    snapshot = jobs.to_response(job)
    service.start_conversion(job, source, target, output_name)
    return snapshot
