import { EvaluateResult, EvalHealth } from "./types";
import { QUESTIONS } from "./constants";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const SSE_TIMEOUT_MS = 600_000; // 10 minutos para toda a avaliação (cada pergunta ~30-60s)

interface EvaluationCallbacks {
  onProgress: (data: { current: number; total: number; question: string }) => void;
  onResult: (result: EvaluateResult) => void;
  onDone: (data: { weighted_score?: number; health?: EvalHealth }) => void;
  onError: (error: string) => void;
}

/**
 * Transforma expert_answers (Record q1-q5) em questions[] para o backend.
 */
function buildQuestionsPayload(
  expertAnswers: Record<string, string>
): { question: string; official_answer: string }[] {
  return QUESTIONS.filter((q) => expertAnswers[q.key]?.trim())
    .map((q) => ({
      question: q.text,
      official_answer: expertAnswers[q.key].trim(),
    }));
}

/**
 * Conecta ao endpoint de avaliação via SSE.
 * Retorna AbortController para cancelamento.
 */
export function connectEvaluation(
  params: {
    context: string;
    expertAnswers: Record<string, string>;
    apiKey?: string;
  },
  callbacks: EvaluationCallbacks
): AbortController {
  const controller = new AbortController();

  const questions = buildQuestionsPayload(params.expertAnswers);

  if (questions.length === 0) {
    setTimeout(() => callbacks.onError("Nenhuma resposta do especialista preenchida."), 0);
    return controller;
  }

  if (!params.context || params.context.trim().length === 0) {
    setTimeout(() => callbacks.onError("Conteudo do site nao extraido."), 0);
    return controller;
  }

  const requestBody = {
    context: params.context,
    questions,
    ...(params.apiKey ? { api_key: params.apiKey } : {}),
  };

  console.log("[SSE] Iniciando avaliação:", {
    contextLen: params.context.length,
    questionsCount: questions.length,
    url: `${BASE_URL}/api/evaluate`,
  });

  // Timeout global para a conexão SSE
  const timeoutId = setTimeout(() => {
    console.error("[SSE] Timeout global atingido");
    controller.abort();
    callbacks.onError("Timeout: a avaliação excedeu o tempo limite. Tente novamente.");
  }, SSE_TIMEOUT_MS);

  (async () => {
    try {
      console.log("[SSE] Enviando fetch...");
      const response = await fetch(`${BASE_URL}/api/evaluate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify(requestBody),
        signal: controller.signal,
      });

      console.log("[SSE] Response status:", response.status);

      if (!response.ok) {
        clearTimeout(timeoutId);
        let errorMsg = `Erro ${response.status}`;
        try {
          const errorData = await response.json();
          errorMsg = errorData.detail || errorData.message || errorMsg;
        } catch {
          // keep default
        }
        console.error("[SSE] Erro HTTP:", errorMsg);
        callbacks.onError(errorMsg);
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        clearTimeout(timeoutId);
        callbacks.onError("Stream nao disponivel");
        return;
      }

      console.log("[SSE] Stream conectado, lendo eventos...");
      const decoder = new TextDecoder();
      let buffer = "";
      let parseErrors = 0;

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            console.log("[SSE] Stream finalizado");
            break;
          }

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
                console.log("[SSE] Evento:", parsed.type, parsed.current || "");

                switch (eventType || parsed.type) {
                  case "progress":
                    callbacks.onProgress({
                      current: parsed.current,
                      total: parsed.total,
                      question: parsed.question || "",
                    });
                    break;
                  case "result": {
                    const raw = parsed.data || parsed.result || parsed;
                    const normalized: EvaluateResult = {
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
                    clearTimeout(timeoutId);
                    callbacks.onDone({
                      weighted_score: parsed.weighted_score,
                      health: parsed.health,
                    });
                    break;
                  case "error":
                    clearTimeout(timeoutId);
                    callbacks.onError(parsed.message || "Erro desconhecido");
                    break;
                }
              } catch {
                parseErrors++;
                console.warn("[SSE] Parse error #" + parseErrors, eventData.substring(0, 100));
                if (parseErrors >= 5) {
                  clearTimeout(timeoutId);
                  callbacks.onError("Erros repetidos ao processar dados do servidor.");
                  return;
                }
              }
              eventType = "";
              eventData = "";
            }
          }
        }
      } finally {
        clearTimeout(timeoutId);
        reader.releaseLock();
      }
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof DOMException && error.name === "AbortError") {
        console.log("[SSE] Conexão abortada (esperado)");
        return;
      }
      const msg = error instanceof Error ? error.message : "Erro de conexao";
      console.error("[SSE] Erro fatal:", msg);
      callbacks.onError(msg);
    }
  })();

  return controller;
}
