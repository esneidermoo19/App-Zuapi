Feature: Pantalla de conversion de audio
  Como usuario quiero subir un audio, elegir el formato y descargar el resultado
  sin salir de la pagina.

  Background:
    Given la pantalla muestra el campo "Archivo de audio", el selector "Formato de salida" y el boton "Convertir"
    And los formatos disponibles son mp3, wav, ogg, flac y m4a

  Scenario: Boton deshabilitado sin archivo
    Given no he elegido ningun archivo
    Then el boton "Convertir" esta deshabilitado

  Scenario: Conversion exitosa
    When elijo un archivo, el formato "wav" y pulso "Convertir"
    Then la app envia el archivo y el formato a POST /api/v1/audio/convert
    And consulta GET /api/v1/jobs/{job_id} cada cierto tiempo mientras el estado sea "queued" o "processing"
    And cuando el estado es "done" muestra el enlace "Descargar" hacia /api/v1/jobs/{job_id}/download

  Scenario: El servidor rechaza el archivo
    When el servidor responde 413 con el codigo "file_too_large"
    Then se muestra una alerta con el mensaje del servidor
    And no se muestra el enlace "Descargar"

  Scenario: La conversion falla
    When el job termina en estado "failed" con el error "invalid_file"
    Then se muestra una alerta que dice "El archivo no es un audio valido"

  Scenario: Convertir otro archivo
    Given una conversion terminada
    When elijo otro archivo
    Then el resultado anterior desaparece y puedo convertir de nuevo
