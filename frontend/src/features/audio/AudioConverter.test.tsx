import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import AudioConverter from "./AudioConverter";

type Reply = { status: number; body: unknown };

function mockFetch(handler: (url: string, init?: RequestInit) => Reply) {
  const fn = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
    const { status, body } = handler(String(url), init);
    return { ok: status >= 200 && status < 300, status, json: async () => body };
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}

function chooseFile(name = "ejemplo.mp3") {
  const input = screen.getByLabelText("Archivo de audio");
  const file = new File(["datos"], name, { type: "audio/mpeg" });
  fireEvent.change(input, { target: { files: [file] } });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

test("el boton Convertir esta deshabilitado sin archivo", () => {
  render(<AudioConverter pollIntervalMs={10} />);
  expect(screen.getByRole("button", { name: "Convertir" })).toBeDisabled();
});

test("ofrece los cinco formatos de salida", () => {
  render(<AudioConverter pollIntervalMs={10} />);
  const options = screen
    .getAllByRole("option")
    .map((option) => (option as HTMLOptionElement).value);
  expect(options).toEqual(["mp3", "wav", "ogg", "flac", "m4a"]);
});

test("conversion exitosa: envia el archivo, consulta el job y muestra Descargar", async () => {
  let polls = 0;
  const fetchMock = mockFetch((url) => {
    if (url.endsWith("/api/v1/audio/convert")) {
      return { status: 202, body: { job_id: "abc", status: "queued" } };
    }
    polls += 1;
    return {
      status: 200,
      body: { job_id: "abc", status: polls < 2 ? "processing" : "done" },
    };
  });

  render(<AudioConverter pollIntervalMs={10} />);
  chooseFile();
  fireEvent.change(screen.getByLabelText("Formato de salida"), {
    target: { value: "wav" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Convertir" }));

  const link = await screen.findByRole("link", { name: "Descargar" });
  expect(link).toHaveAttribute("href", "/api/v1/jobs/abc/download");

  const [url, init] = fetchMock.mock.calls[0];
  expect(String(url)).toBe("/api/v1/audio/convert");
  expect(init?.method).toBe("POST");
  const body = init?.body as FormData;
  expect(body.get("target_format")).toBe("wav");
  expect((body.get("file") as File).name).toBe("ejemplo.mp3");
});

test("muestra el mensaje del servidor cuando rechaza el archivo", async () => {
  mockFetch(() => ({
    status: 413,
    body: {
      detail: { code: "file_too_large", message: "El archivo supera el limite de 50 MB." },
    },
  }));

  render(<AudioConverter pollIntervalMs={10} />);
  chooseFile("grande.mp3");
  fireEvent.click(screen.getByRole("button", { name: "Convertir" }));

  const alert = await screen.findByRole("alert");
  expect(alert).toHaveTextContent("El archivo supera el limite de 50 MB.");
  expect(screen.queryByRole("link", { name: "Descargar" })).not.toBeInTheDocument();
});

test("muestra un mensaje claro cuando el job falla con invalid_file", async () => {
  mockFetch((url) => {
    if (url.endsWith("/api/v1/audio/convert")) {
      return { status: 202, body: { job_id: "xyz", status: "queued" } };
    }
    return {
      status: 200,
      body: { job_id: "xyz", status: "failed", error: "invalid_file" },
    };
  });

  render(<AudioConverter pollIntervalMs={10} />);
  chooseFile("roto.mp3");
  fireEvent.click(screen.getByRole("button", { name: "Convertir" }));

  const alert = await screen.findByRole("alert");
  expect(alert).toHaveTextContent(/audio valido/i);
});

test("al elegir otro archivo desaparece el resultado anterior", async () => {
  mockFetch((url) => {
    if (url.endsWith("/api/v1/audio/convert")) {
      return { status: 202, body: { job_id: "abc", status: "queued" } };
    }
    return { status: 200, body: { job_id: "abc", status: "done" } };
  });

  render(<AudioConverter pollIntervalMs={10} />);
  chooseFile();
  fireEvent.click(screen.getByRole("button", { name: "Convertir" }));
  await screen.findByRole("link", { name: "Descargar" });

  chooseFile("otro.mp3");
  await waitFor(() =>
    expect(screen.queryByRole("link", { name: "Descargar" })).not.toBeInTheDocument(),
  );
  expect(screen.getByRole("button", { name: "Convertir" })).toBeEnabled();
});
