# Constitucion del proyecto

## Alcance (v1)
- Audio: convertir entre mp3, wav, ogg, flac, m4a.
- Documentos: PDF a DOCX y DOCX a PDF.
- Imagenes: quitar fondo (salida PNG con transparencia).

## Principios
1. Privacidad: los archivos se borran automaticamente; no se registran contenidos.
2. Asincronia: toda conversion es un job (subir, consultar estado, descargar).
3. Limites explicitos: tamano maximo y formatos permitidos por modulo.
4. Errores claros: respuestas con codigo y mensaje legibles.

## Fuera de alcance (por ahora)
- Cuentas de usuario y pagos.
- OCR de PDFs escaneados.
- Procesamiento por lotes.

## Estados de un job
queued, processing, done, failed
