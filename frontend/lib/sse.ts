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

export async function connectEvaluation(
  body: EvaluationBody,
  callbacks: EvaluationCallbacks
): Promise<void> {
  try {
    const response = await fetch(`${BASE_URL}/api/evaluate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify(body),
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

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Parse SSE events from buffer
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
          // End of event — process it
          try {
            const parsed = JSON.parse(eventData);

            switch (eventType || parsed.type) {
              case "progress":
                callbacks.onProgress({
                  current: parsed.current,
                  total: parsed.total,
                });
                break;
              case "result":
                callbacks.onResult(parsed.result || parsed);
                break;
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
          } catch (e) {
            console.warn("Failed to parse SSE data:", eventData, e);
          }
          eventType = "";
          eventData = "";
        }
      }
    }
  } catch (error) {
    callbacks.onError(
      error instanceof Error ? error.message : "Erro de conexao"
    );
  }
}
