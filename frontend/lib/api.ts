import { ExtractResponse } from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const DEFAULT_TIMEOUT_MS = 30_000;

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit & { timeoutMs?: number } = {}
): Promise<T> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, ...fetchOptions } = options;
  const url = `${BASE_URL}${endpoint}`;

  // Timeout via AbortController
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  // Mescla signal externo com o de timeout
  const signal = fetchOptions.signal
    ? composeAbortSignals(fetchOptions.signal, controller.signal)
    : controller.signal;

  try {
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...fetchOptions.headers,
      },
      ...fetchOptions,
      signal,
    });

    if (!response.ok) {
      let errorMessage = `Erro ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        // keep default error message
      }
      throw new ApiError(errorMessage, response.status);
    }

    return response.json();
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError(
        "A requisicao excedeu o tempo limite. Tente novamente.",
        408
      );
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

function composeAbortSignals(...signals: AbortSignal[]): AbortSignal {
  const controller = new AbortController();
  for (const signal of signals) {
    if (signal.aborted) {
      controller.abort(signal.reason);
      return controller.signal;
    }
    signal.addEventListener("abort", () => controller.abort(signal.reason), {
      once: true,
    });
  }
  return controller.signal;
}

export async function extractContent(url: string): Promise<ExtractResponse> {
  return fetchApi<ExtractResponse>("/api/extract", {
    method: "POST",
    body: JSON.stringify({ url }),
    timeoutMs: 45_000, // Extração pode demorar mais
  });
}
