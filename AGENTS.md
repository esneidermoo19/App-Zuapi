# AGENTS.md

Reglas para agentes de IA (OpenCode) que trabajan en este repo.

## Metodo: Spec-Driven Development
- Nunca implementes algo sin spec previa en `specs/`.
- Si la spec es ambigua, pregunta o propon el cambio en la spec primero.
- El contrato HTTP vive en `specs/openapi.yaml`. El codigo se ajusta al contrato, no al reves.
- Cada escenario Gherkin de `specs/<modulo>/*.feature` debe tener al menos un test.
- No modifiques los tests ni el contrato para que pasen; si hay un error en ellos, avisa.

## Stack
- Backend: Python 3.12, FastAPI, pytest, ruff.
- Frontend: React 18, Vite, TypeScript, Vitest.
- Binarios externos: ffmpeg (audio), LibreOffice headless (Word a PDF).
- Librerias: pdf2docx (PDF a Word), rembg (quitar fondo).

## Estructura del backend
- `backend/app/main.py`: crea la app y registra routers en /api/v1.
- `backend/app/core/`: config y utilidades compartidas (jobs).
- `backend/app/modules/<modulo>/`: `router.py` (HTTP), `service.py` (logica), `schemas.py` (modelos).
- La logica de conversion va en `service.py`, nunca en el router.

## Reglas de codigo
- Todo archivo subido se valida (extension, tipo y tamano maximo) antes de procesarse.
- El limite de tamano se lee de `settings.max_upload_mb` en cada peticion.
- Los errores HTTP usan `detail={"code": "...", "message": "..."}`.
- Los archivos temporales se guardan en `settings.storage_dir` y se borran tras `file_ttl_minutes`.
- Nunca construyas comandos de shell con nombres de archivo del usuario; usa `subprocess.run([...])` con lista de argumentos.
- Sin secretos en el repo. Configuracion por variables de entorno.
- Antes de instalar una libreria nueva, verifica que existe y es la correcta.

## Antes de terminar cualquier tarea
cd backend && ruff check . && python -m pytest
cd frontend && npm run lint && npm test && npm run build
