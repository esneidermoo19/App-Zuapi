from pathlib import Path

from app.main import app

SPEC = Path(__file__).resolve().parents[2] / "specs" / "openapi.yaml"


def test_health_path_is_in_spec():
    text = SPEC.read_text(encoding="utf-8")
    assert "/health:" in text
    assert "/api/v1/health" in app.openapi()["paths"]
