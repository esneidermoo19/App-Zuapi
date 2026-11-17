import { useEffect, useRef, useState } from "react";

const FORMATS = ["mp3", "wav", "ogg", "flac", "m4a"] as const;

type JobStatus = "queued" | "processing" | "done" | "failed";

interface JobResponse {
  job_id: string;
  status: JobStatus;
  error?: string | null;
}

interface ErrorResponse {
  detail?: {
    message?: string;
  };
}

interface AudioConverterProps {
  pollIntervalMs?: number;
}

function serverMessage(body: unknown): string | undefined {
  if (typeof body !== "object" || body === null || !("detail" in body)) {
    return undefined;
  }

  const detail = (body as ErrorResponse).detail;
  return typeof detail?.message === "string" ? detail.message : undefined;
}

function jobFailureMessage(code: string | null | undefined): string {
  if (code === "invalid_file") {
    return "El archivo no es un audio valido.";
  }
  return code ? `La conversion fallo (${code}).` : "La conversion no se pudo completar.";
}

export default function AudioConverter({ pollIntervalMs = 1000 }: AudioConverterProps) {
  const [file, setFile] = useState<File | null>(null);
  const [targetFormat, setTargetFormat] = useState<(typeof FORMATS)[number]>("mp3");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const requestIdRef = useRef(0);

  const clearPollingTimer = () => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  useEffect(
    () => () => {
      requestIdRef.current += 1;
      clearPollingTimer();
    },
    [],
  );

  const pollJob = async (id: string, requestId: number): Promise<void> => {
    try {
      const response = await fetch(`/api/v1/jobs/${id}`);
      const body: unknown = await response.json();
      if (requestId !== requestIdRef.current) return;

      if (!response.ok) {
        setError(serverMessage(body) ?? "No se pudo consultar el estado de la conversion.");
        setBusy(false);
        return;
      }

      const job = body as JobResponse;
      setStatus(job.status);

      if (job.status === "done") {
        setBusy(false);
        return;
      }
      if (job.status === "failed") {
        setError(jobFailureMessage(job.error));
        setBusy(false);
        return;
      }
      if (job.status === "queued" || job.status === "processing") {
        timerRef.current = setTimeout(() => {
          timerRef.current = null;
          void pollJob(id, requestId);
        }, pollIntervalMs);
      }
    } catch {
      if (requestId === requestIdRef.current) {
        setError("No se pudo consultar el estado de la conversion.");
        setBusy(false);
      }
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    requestIdRef.current += 1;
    clearPollingTimer();
    setFile(event.target.files?.[0] ?? null);
    setBusy(false);
    setStatus(null);
    setJobId(null);
    setError(null);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!file || busy) return;

    const requestId = ++requestIdRef.current;
    clearPollingTimer();
    setBusy(true);
    setStatus("queued");
    setJobId(null);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("target_format", targetFormat);

    try {
      const response = await fetch("/api/v1/audio/convert", {
        method: "POST",
        body: formData,
      });
      const body: unknown = await response.json();
      if (requestId !== requestIdRef.current) return;

      if (!response.ok) {
        setError(serverMessage(body) ?? "No se pudo iniciar la conversion.");
        setBusy(false);
        setStatus(null);
        return;
      }

      const job = body as JobResponse;
      setJobId(job.job_id);
      setStatus(job.status);
      await pollJob(job.job_id, requestId);
    } catch {
      if (requestId === requestIdRef.current) {
        setError("No se pudo iniciar la conversion.");
        setBusy(false);
        setStatus(null);
      }
    }
  };

  return (
    <section aria-label="Conversor de audio">
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="audio-file">Archivo de audio</label>
          <input
            id="audio-file"
            type="file"
            accept="audio/*"
            onChange={handleFileChange}
          />
        </div>
        <div>
          <label htmlFor="audio-target-format">Formato de salida</label>
          <select
            id="audio-target-format"
            value={targetFormat}
            onChange={(event) =>
              setTargetFormat(event.target.value as (typeof FORMATS)[number])
            }
          >
            {FORMATS.map((format) => (
              <option key={format} value={format}>
                {format}
              </option>
            ))}
          </select>
        </div>
        <button type="submit" disabled={!file || busy}>
          Convertir
        </button>
      </form>

      {busy && status && <p>Estado: {status}</p>}
      {error && <p role="alert">{error}</p>}
      {status === "done" && jobId && (
        <a href={`/api/v1/jobs/${jobId}/download`}>Descargar</a>
      )}
    </section>
  );
}
