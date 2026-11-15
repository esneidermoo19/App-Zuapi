Feature: Convertir audio entre formatos
  Como usuario quiero convertir un archivo de audio a otro formato
  para poder usarlo en otro dispositivo o aplicacion.

  Background:
    Given el servicio esta activo
    And el tamano maximo de archivo es 50 MB

  Scenario: Conversion exitosa de mp3 a wav
    When subo un archivo "ejemplo.mp3" valido y pido el formato "wav"
    Then recibo un job con estado "queued"
    And al consultar el job termina en estado "done"
    And puedo descargar un archivo con extension ".wav"

  Scenario: Formato de salida no soportado
    When subo un archivo "ejemplo.mp3" valido y pido el formato "xyz"
    Then recibo un error 422 con el codigo "unsupported_format"

  Scenario: Archivo corrupto
    When subo un archivo "roto.mp3" que no es audio valido
    Then el job termina en estado "failed"
    And el error indica "invalid_file"

  Scenario: Archivo demasiado grande
    When subo un archivo de 80 MB
    Then recibo un error 413 con el codigo "file_too_large"
