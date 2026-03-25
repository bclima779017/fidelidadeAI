import {
  ExtractResponse,
  SitemapResponse,
  MultiExtractResponse,
  RAGIndexResponse,
} from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const DEFAULT_TIMEOUT_MS = 30_000;

// Diagnóstico: loga a URL base no primeiro carregamento
console.info(`[API] BASE_URL = "${BASE_URL}" (env=${process.env.NEXT_PUBLIC_API_URL || "não definido"})`);

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

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const signal = fetchOptions.signal
    ? composeAbortSignals(fetchOptions.signal, controller.signal)
    : controller.signal;

  try {
    console.info(`[API] → ${fetchOptions.method || "GET"} ${url}`);
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...fetchOptions.headers,
      },
      ...fetchOptions,
      signal,
    });

    console.info(`[API] ← ${response.status} ${url}`);

    if (!response.ok) {
      let errorMessage = `Erro ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        // keep default
      }
      console.error(`[API] ERRO: ${errorMessage} | URL: ${url}`);
      throw new ApiError(errorMessage, response.status);
    }

    return response.json();
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      console.warn(`[API] TIMEOUT após ${timeoutMs}ms: ${url}`);
      throw new ApiError(
        "A requisicao excedeu o tempo limite. Tente novamente.",
        408
      );
    }
    console.error(`[API] FALHA: ${error instanceof Error ? error.message : error} | URL: ${url}`);
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

// ── Extract ──

export async function extractContent(url: string): Promise<ExtractResponse> {
  return fetchApi<ExtractResponse>("/api/extract", {
    method: "POST",
    body: JSON.stringify({ url }),
    timeoutMs: 45_000,
  });
}

// ── Sitemap ──

export async function discoverSitemap(
  url: string,
  maxPages: number = 50
): Promise<SitemapResponse> {
  return fetchApi<SitemapResponse>("/api/sitemap/discover", {
    method: "POST",
    body: JSON.stringify({ url, max_pages: maxPages }),
    timeoutMs: 60_000,
  });
}

// ── Multi Extract ──

export async function extractMultiPages(
  urls: string[]
): Promise<MultiExtractResponse> {
  return fetchApi<MultiExtractResponse>("/api/extract/multi", {
    method: "POST",
    body: JSON.stringify({ urls }),
    timeoutMs: 120_000,
  });
}

/**
 * Extrai múltiplas páginas via SSE com progresso por página.
 */
export function connectMultiExtract(
  urls: string[],
  callbacks: {
    onExtracting: (data: { current: number; total: number; url: string }) => void;
    onExtracted: (data: { current: number; total: number; url: string; title: string; char_count: number }) => void;
    onFailed: (data: { current: number; total: number; url: string; error: string }) => void;
    onDone: (data: { total_extracted: number; total_requested: number; pages: ExtractResponse[] }) => void;
    onError: (error: string) => void;
  }
): AbortController {
  const controller = new AbortController();
  const MULTI_EXTRACT_TIMEOUT_MS = 300_000; // 5 minutos

  (async () => {
    const timeoutId = setTimeout(() => controller.abort(), MULTI_EXTRACT_TIMEOUT_MS);
    try {
      const response = await fetch(`${BASE_URL}/api/extract/multi/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        body: JSON.stringify({ urls }),
        signal: controller.signal,
      });

      if (!response.ok) {
        let msg = `Erro ${response.status}`;
        try { const d = await response.json(); msg = d.detail || msg; } catch {}
        callbacks.onError(msg);
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) { callbacks.onError("Stream nao disponivel"); return; }

      const decoder = new TextDecoder();
      let buffer = "";

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          let eventData = "";
          for (const line of lines) {
            if (line.startsWith("data:")) {
              eventData = line.slice(5).trim();
            } else if (line === "" && eventData) {
              try {
                const parsed = JSON.parse(eventData);
                switch (parsed.type) {
                  case "extracting": callbacks.onExtracting(parsed); break;
                  case "extracted": callbacks.onExtracted(parsed); break;
                  case "failed": callbacks.onFailed(parsed); break;
                  case "done": callbacks.onDone(parsed); break;
                }
              } catch { /* ignore malformed SSE JSON */ }
              eventData = "";
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      callbacks.onError(error instanceof Error ? error.message : "Erro de conexao");
    } finally {
      clearTimeout(timeoutId);
    }
  })();

  return controller;
}

// ── RAG ──

export async function indexRAG(
  pages: ExtractResponse[]
): Promise<RAGIndexResponse> {
  return fetchApi<RAGIndexResponse>("/api/rag/index", {
    method: "POST",
    body: JSON.stringify({ pages }),
    timeoutMs: 180_000,
  });
}

export async function getRAGStats(): Promise<{ total_chunks: number; total_pages: number; is_ready: boolean }> {
  return fetchApi("/api/rag/stats", { method: "GET" });
}
