"use client";

import React, { useEffect, useRef } from "react";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import { toast } from "sonner";
import { useAuditStore } from "@/lib/store";
import { connectEvaluation } from "@/lib/sse";
import { QUESTIONS } from "@/lib/constants";
import { Card } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Button } from "@/components/ui/Button";
import { ResultCardSkeleton } from "@/components/ui/Skeleton";

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
        onResult: (result) => {
          useAuditStore.getState().addResult(result);
          const score = result.score;
          if (score >= 0) {
            toast.success(`Pergunta avaliada — Score: ${score}`, { duration: 2000 });
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
  const isDone = evaluationStatus === "done";
  const isError = evaluationStatus === "error";
  const isRunning = evaluationStatus === "running";

  return (
    <Card title="3. Avaliacao em Andamento">
      <div className="space-y-4">
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span className="text-kipiai-gray dark:text-gray-400">
              {isDone ? "Avaliacao concluida"
                : isError ? "Erro na avaliacao"
                : isRunning && evaluationProgress.current === 0 ? "Iniciando avaliacao..."
                : `Avaliando pergunta ${evaluationProgress.current} de ${totalQuestions}...`}
            </span>
            <span className="font-medium text-kipiai-dark dark:text-white">
              {evaluationProgress.current}/{totalQuestions}
            </span>
          </div>
          <ProgressBar value={isDone ? 100 : progressPercent} height="lg" />
        </div>

        {/* Question status list with auto-animate */}
        <div ref={listRef} className="space-y-2" role="list" aria-label="Status das perguntas">
          {filledQuestions.map((q, index) => {
            const hasResult = index < results.length;
            const isEvaluating = isRunning && !isDone && index === evaluationProgress.current - 1;

            return (
              <div key={q.key} role="listitem" className="flex items-center gap-3 text-sm">
                <div
                  className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 ${
                    hasResult ? "bg-kipiai-green text-white"
                    : isEvaluating ? "bg-kipiai-blue text-white animate-pulse"
                    : "bg-gray-200 dark:bg-gray-700 text-gray-400"
                  }`}
                  aria-hidden="true"
                >
                  {hasResult ? (
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5" /></svg>
                  ) : isEvaluating ? (
                    <div className="w-2 h-2 bg-white rounded-full" />
                  ) : (
                    <span className="text-xs">{index + 1}</span>
                  )}
                </div>
                <span className={hasResult ? "text-kipiai-dark dark:text-gray-200" : isEvaluating ? "text-kipiai-blue font-medium" : "text-gray-400"}>
                  {q.label}
                  {hasResult && results[index] && (
                    <span className="ml-2 text-kipiai-gray">— Score: {results[index].score >= 0 ? results[index].score : "erro"}</span>
                  )}
                </span>
              </div>
            );
          })}
        </div>

        {/* Skeleton placeholders for upcoming results */}
        {isRunning && results.length < totalQuestions && (
          <div className="space-y-2 mt-2">
            {Array.from({ length: Math.min(2, totalQuestions - results.length) }).map((_, i) => (
              <ResultCardSkeleton key={`skel-${i}`} />
            ))}
          </div>
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
