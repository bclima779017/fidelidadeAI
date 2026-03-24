"use client";

import React, { useEffect, useRef, useState } from "react";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import { motion, AnimatePresence } from "motion/react";
import { toast } from "sonner";
import { useAuditStore } from "@/lib/store";
import { connectEvaluation } from "@/lib/sse";
import { QUESTIONS } from "@/lib/constants";
import { Card } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Button } from "@/components/ui/Button";
import { ResultCardSkeleton } from "@/components/ui/Skeleton";

// ── Mensagens rotativas de feedback ──
const HEARTBEAT_MESSAGES = [
  "Analisando conteudo do site...",
  "Comparando claims com a resposta oficial...",
  "Verificando fidelidade semantica...",
  "Processando resposta da IA...",
  "Calculando score composto...",
  "Checando claims preservados e omitidos...",
  "Avaliando hallucinations...",
  "Quase la, finalizando analise...",
  "Depurando detalhes da resposta...",
  "Validando justificativa...",
];

function useHeartbeat(isActive: boolean) {
  const [elapsed, setElapsed] = useState(0);
  const [messageIndex, setMessageIndex] = useState(0);

  // Timer único que gerencia ambos: elapsed + mensagem
  useEffect(() => {
    if (!isActive) {
      setElapsed(0);
      setMessageIndex(0);
      return;
    }

    setElapsed(0);
    setMessageIndex(0);

    const timerInterval = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);

    const msgInterval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % HEARTBEAT_MESSAGES.length);
    }, 4000);

    return () => {
      clearInterval(timerInterval);
      clearInterval(msgInterval);
    };
  }, [isActive]);

  return {
    elapsed,
    message: HEARTBEAT_MESSAGES[messageIndex],
    formattedTime: `${Math.floor(elapsed / 60)}:${String(elapsed % 60).padStart(2, "0")}`,
  };
}

export function EvaluationProgress() {
  const evaluationStatus = useAuditStore((s) => s.evaluationStatus);
  const evaluationProgress = useAuditStore((s) => s.evaluationProgress);
  const results = useAuditStore((s) => s.results);
  const errorMessage = useAuditStore((s) => s.errorMessage);
  const expertAnswers = useAuditStore((s) => s.expertAnswers);

  const abortRef = useRef<AbortController | null>(null);
  const startedRef = useRef(false);
  const [listRef] = useAutoAnimate();

  const filledQuestions = QUESTIONS.filter((q) => expertAnswers[q.key]?.trim());
  const totalQuestions = filledQuestions.length;

  const isRunning = evaluationStatus === "running";
  const isDone = evaluationStatus === "done";
  const isError = evaluationStatus === "error";

  // Heartbeat ativo enquanto avaliação roda
  const heartbeat = useHeartbeat(isRunning && !isDone);

  useEffect(() => {
    if (evaluationStatus !== "running") return;
    if (startedRef.current) return;
    startedRef.current = true;

    const state = useAuditStore.getState();

    const controller = connectEvaluation(
      { context: state.extractedContent, expertAnswers: state.expertAnswers },
      {
        onProgress: (data) => {
          useAuditStore.getState().setEvaluationProgress(data.current, data.total);
        },
        onResult: (result, index) => {
          useAuditStore.getState().addResult(result, index);
          const score = result.score;
          if (score >= 0) {
            toast.success(`Pergunta ${index + 1} avaliada — Score: ${score}`, { duration: 2000 });
          }
        },
        onDone: (data) => {
          if (data.weighted_score !== undefined) {
            useAuditStore.getState().setWeightedScore(data.weighted_score);
          }
          if (data.health) {
            useAuditStore.getState().setHealth(data.health);
          }
          useAuditStore.getState().setEvaluationStatus("done");
          useAuditStore.getState().setCurrentStep(4);
          toast.success("Avaliacao concluida!", { duration: 3000 });
        },
        onError: (error) => {
          useAuditStore.getState().setErrorMessage(error);
          useAuditStore.getState().setEvaluationStatus("error");
          toast.error(error, { duration: 5000 });
        },
      }
    );

    abortRef.current = controller;
  }, [evaluationStatus]);

  const handleCancel = () => {
    if (abortRef.current) { abortRef.current.abort(); abortRef.current = null; }
    startedRef.current = false;
    // Se já tem resultados parciais, mostra o que tem; senão, reseta
    const currentResults = useAuditStore.getState().results.filter(Boolean);
    if (currentResults.length > 0) {
      useAuditStore.getState().setEvaluationStatus("done");
      useAuditStore.getState().setCurrentStep(4);
      toast.info(`Avaliacao cancelada. ${currentResults.length} de ${totalQuestions} perguntas avaliadas.`, { duration: 4000 });
    } else {
      useAuditStore.getState().resetEvaluation();
      toast.info("Avaliacao cancelada.", { duration: 3000 });
    }
  };

  const handleRetry = () => {
    if (abortRef.current) { abortRef.current.abort(); abortRef.current = null; }
    startedRef.current = false;
    useAuditStore.getState().resetEvaluation();
    setTimeout(() => {
      useAuditStore.getState().setEvaluationStatus("running");
      useAuditStore.getState().setCurrentStep(3);
    }, 150);
  };

  const progressPercent = totalQuestions > 0
    ? Math.round((evaluationProgress.current / totalQuestions) * 100)
    : 0;

  return (
    <Card title="3. Avaliacao em Andamento">
      <div className="space-y-4">
        {/* Header com progresso + timer */}
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span className="text-kipiai-gray dark:text-gray-400">
              {isDone ? "Avaliacao concluida"
                : isError ? "Erro na avaliacao"
                : isRunning && evaluationProgress.current === 0 ? "Iniciando avaliacao..."
                : `Avaliando pergunta ${evaluationProgress.current} de ${totalQuestions}...`}
            </span>
            <div className="flex items-center gap-3">
              {isRunning && (
                <span className="font-mono text-xs text-kipiai-blue bg-kipiai-blue/10 dark:bg-kipiai-blue/20 px-2 py-0.5 rounded">
                  {heartbeat.formattedTime}
                </span>
              )}
              <span className="font-medium text-kipiai-dark dark:text-white">
                {evaluationProgress.current}/{totalQuestions}
              </span>
            </div>
          </div>
          <ProgressBar value={isDone ? 100 : progressPercent} height="lg" />
        </div>

        {/* Heartbeat + cancel */}
        {isRunning && !isDone && (
          <div className="flex items-center gap-3 bg-kipiai-blue/5 dark:bg-kipiai-blue/10 rounded-lg px-4 py-2.5">
            {/* Spinner pulsante */}
            <div className="flex-shrink-0 relative w-5 h-5">
              <div className="absolute inset-0 rounded-full bg-kipiai-blue/30 animate-ping" />
              <div className="relative w-5 h-5 rounded-full bg-kipiai-blue flex items-center justify-center">
                <div className="w-2 h-2 bg-white rounded-full" />
              </div>
            </div>
            {/* Mensagem com fade transition */}
            <AnimatePresence mode="wait">
              <motion.span
                key={heartbeat.message}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.25 }}
                className="text-sm text-kipiai-blue dark:text-kipiai-blue-light"
              >
                {heartbeat.message}
              </motion.span>
            </AnimatePresence>
            {/* Cancel button */}
            <button
              onClick={handleCancel}
              className="ml-auto flex-shrink-0 text-xs text-kipiai-gray hover:text-kipiai-red transition-colors px-2 py-1 rounded hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              Cancelar
            </button>
          </div>
        )}

        {/* Question status list */}
        <div ref={listRef} className="space-y-2" role="list" aria-label="Status das perguntas">
          {filledQuestions.map((q, index) => {
            const hasResult = !!results[index];
            const isEvaluating = isRunning && !isDone && index === evaluationProgress.current - 1;

            return (
              <div key={q.key} role="listitem" className="flex items-center gap-3 text-sm">
                <div
                  className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 transition-colors ${
                    hasResult ? "bg-kipiai-green text-white"
                    : isEvaluating ? "bg-kipiai-blue text-white"
                    : "bg-gray-200 dark:bg-gray-700 text-gray-400"
                  }`}
                  aria-hidden="true"
                >
                  {hasResult ? (
                    <motion.svg
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring", stiffness: 300 }}
                      xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"
                    >
                      <path d="M20 6 9 17l-5-5" />
                    </motion.svg>
                  ) : isEvaluating ? (
                    <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                  ) : (
                    <span className="text-xs">{index + 1}</span>
                  )}
                </div>
                <span className={`flex-1 ${hasResult ? "text-kipiai-dark dark:text-gray-200" : isEvaluating ? "text-kipiai-blue font-medium" : "text-gray-400"}`}>
                  {q.label}
                  {hasResult && results[index] && (
                    <motion.span
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="ml-2 text-kipiai-gray"
                    >
                      — Score: {results[index].score >= 0 ? results[index].score : "erro"}
                    </motion.span>
                  )}
                </span>
                {/* Mini timer por pergunta ativa */}
                {isEvaluating && (
                  <span className="font-mono text-xs text-kipiai-gray">
                    {heartbeat.formattedTime}
                  </span>
                )}
              </div>
            );
          })}
        </div>

        {/* Skeleton placeholders */}
        {isRunning && results.length < totalQuestions && (
          <div className="space-y-2 mt-2">
            {Array.from({ length: Math.min(2, totalQuestions - results.length) }).map((_, i) => (
              <ResultCardSkeleton key={`skel-${i}`} />
            ))}
          </div>
        )}

        {/* Conclusão com animação */}
        {isDone && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-kipiai-green/10 dark:bg-kipiai-green/20 border border-kipiai-green/20 rounded-lg p-3 flex items-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-kipiai-green flex-shrink-0">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><path d="m9 11 3 3L22 4" />
            </svg>
            <span className="text-sm text-kipiai-green font-medium">
              Todas as perguntas foram avaliadas com sucesso
            </span>
          </motion.div>
        )}

        {isError && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-kipiai-red/20 rounded-lg p-4 space-y-3">
            <p className="text-sm text-kipiai-red">{errorMessage || "Ocorreu um erro durante a avaliacao."}</p>
            <Button variant="danger" size="sm" onClick={handleRetry}>Tentar novamente</Button>
          </div>
        )}
      </div>
    </Card>
  );
}
