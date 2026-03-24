import { EvaluateResult, EvalHealth } from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface EvaluationBody {
  url: string;
  content: string;
  expert_answers: Record<string, string>;
}

interface EvaluationCallbacks {
  onProgress: (data: { current: number; total: number }) => void;
  onResult: (result: EvaluateResult) => void;
  onDone: (data: { weighted_score?: number; health?: EvalHealth }) => void;
  onError: (error: string) => void;
}

/**
 * Conecta ao endpoint de avaliação via SSE.
 * Retorna um AbortController para cancelar a conexão.
 */
export function connectEvaluation(
  body: EvaluationBody,
  callbacks: EvaluationCallbacks
): AbortController {
  const controller = new AbortController();
  let parseErrors = 0;

  // Fire-and-forget async — erros vão para onError callback
  (async () => {
    try {
      const response = await fetch(`${BASE_URL}/api/evaluate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      if (!response.ok) {
        let errorMsg = `Erro ${response.status}`;
        try {
          const errorData = await response.json();
          errorMsg = errorData.detail || errorData.message || errorMsg;
        } catch {
          // keep default
        }
        callbacks.onError(errorMsg);
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        callbacks.onError("Stream nao disponivel");
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          let eventType = "";
          let eventData = "";

          for (const line of lines) {
            if (line.startsWith("event:")) {
              eventType = line.slice(6).trim();
            } else if (line.startsWith("data:")) {
              eventData = line.slice(5).trim();
            } else if (line === "" && eventData) {
              try {
                const parsed = JSON.parse(eventData);

                switch (eventType || parsed.type) {
                  case "progress":
                    callbacks.onProgress({
                      current: parsed.current,
                      total: parsed.total,
                    });
                    break;
                  case "result": {
                    const raw = parsed.data || parsed.result || parsed;
                    // Normaliza campos backend → frontend
                    const normalized = {
                      ...raw,
                      ai_answer: raw.ai_answer || raw.resposta_ia || "",
                      expert_answer: raw.expert_answer || raw.official_answer || "",
                      semantic_match: raw.semantic_match ?? raw.match_semantico ?? null,
                      claims_rate: raw.claims_rate ?? raw.taxa_claims ?? null,
                    };
                    callbacks.onResult(normalized);
                    break;
                  }
                  case "done":
                    callbacks.onDone({
                      weighted_score: parsed.weighted_score,
                      health: parsed.health,
                    });
                    break;
                  case "error":
                    callbacks.onError(parsed.message || "Erro desconhecido");
                    break;
                }
              } catch {
                parseErrors++;
                if (parseErrors >= 3) {
                  callbacks.onError(
                    `Multiplos erros ao processar dados do servidor (${parseErrors} falhas)`
                  );
                }
              }
              eventType = "";
              eventData = "";
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      // Não reporta erro se foi cancelamento intencional
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      callbacks.onError(
        error instanceof Error ? error.message : "Erro de conexao"
      );
    }
  })();

  return controller;
}
