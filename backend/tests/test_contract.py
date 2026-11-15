from pathlib import Path

import pytest

from app.main import app

SPEC = Path(__file__).resolve().parents[2] / "specs" / "openapi.yaml"

SPEC_PATHS = [
    "/health",
    "/audio/convert",
    "/jobs/{job_id}",
    "/jobs/{job_id}/download",
]


@pytest.mark.parametrize("path", SPEC_PATHS)
def test_spec_path_is_implemented(path):
    text = SPEC.read_text(encoding="utf-8")
    assert f"  {path}:" in text
    assert f"/api/v1{path}" in app.openapi()["paths"]
