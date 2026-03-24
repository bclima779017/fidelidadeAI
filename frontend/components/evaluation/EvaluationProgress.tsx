"use client";

import React, { useEffect, useRef, useCallback } from "react";
import { useAuditStore } from "@/lib/store";
import { connectEvaluation } from "@/lib/sse";
import { Card } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Button } from "@/components/ui/Button";

const QUESTION_LABELS = [
  "Proposta de valor",
  "Diferenciais competitivos",
  "Publico-alvo",
  "Problema resolvido",
  "Produtos e servicos",
];

export function EvaluationProgress() {
  const url = useAuditStore((s) => s.url);
  const extractedContent = useAuditStore((s) => s.extractedContent);
  const expertAnswers = useAuditStore((s) => s.expertAnswers);
  const evaluationStatus = useAuditStore((s) => s.evaluationStatus);
  const evaluationProgress = useAuditStore((s) => s.evaluationProgress);
  const results = useAuditStore((s) => s.results);
  const errorMessage = useAuditStore((s) => s.errorMessage);
  const setEvaluationStatus = useAuditStore((s) => s.setEvaluationStatus);
  const setEvaluationProgress = useAuditStore((s) => s.setEvaluationProgress);
  const setErrorMessage = useAuditStore((s) => s.setErrorMessage);
  const addResult = useAuditStore((s) => s.addResult);
  const setWeightedScore = useAuditStore((s) => s.setWeightedScore);
  const setHealth = useAuditStore((s) => s.setHealth);
  const setCurrentStep = useAuditStore((s) => s.setCurrentStep);
  const resetEvaluation = useAuditStore((s) => s.resetEvaluation);

  const abortControllerRef = useRef<AbortController | null>(null);
  const startedRef = useRef(false);

  const startEvaluation = useCallback(() => {
    if (startedRef.current) return;
    startedRef.current = true;

    const controller = connectEvaluation(
      {
        url,
        content: extractedContent,
        expert_answers: expertAnswers,
      },
      {
        onProgress: (data) => {
          setEvaluationProgress(data.current, data.total);
        },
        onResult: (result) => {
          addResult(result);
        },
        onDone: (data) => {
          if (data.weighted_score !== undefined) {
            setWeightedScore(data.weighted_score);
          }
          if (data.health) {
            setHealth(data.health);
          }
          setEvaluationStatus("done");
          setCurrentStep(4);
        },
        onError: (error) => {
          setErrorMessage(error);
          setEvaluationStatus("error");
        },
      }
    );

    abortControllerRef.current = controller;
  }, [
    url,
    extractedContent,
    expertAnswers,
    setEvaluationProgress,
    addResult,
    setWeightedScore,
    setHealth,
    setEvaluationStatus,
    setCurrentStep,
    setErrorMessage,
  ]);

  useEffect(() => {
    if (evaluationStatus !== "running") return;

    startEvaluation();

    return () => {
      // Cleanup: aborta conexão SSE se componente desmontar
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
    };
  }, [evaluationStatus, startEvaluation]);

  const handleRetry = useCallback(() => {
    startedRef.current = false;
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    resetEvaluation();
    // Pequeno delay para garantir que o estado resetou antes de re-disparar
    setTimeout(() => {
      setEvaluationStatus("running");
      setCurrentStep(3);
    }, 100);
  }, [resetEvaluation, setEvaluationStatus, setCurrentStep]);

  const totalQuestions = Object.keys(expertAnswers).filter(
    (k) => expertAnswers[k]?.trim()
  ).length;
  const progressPercent =
    totalQuestions > 0
      ? Math.round((evaluationProgress.current / totalQuestions) * 100)
      : 0;

  const isDone = evaluationStatus === "done";
  const isError = evaluationStatus === "error";

  return (
    <Card title="3. Avaliacao em Andamento">
      <div className="space-y-4">
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span className="text-kipiai-gray">
              {isDone
                ? "Avaliacao concluida"
                : isError
                ? "Erro na avaliacao"
                : `Avaliando pergunta ${evaluationProgress.current} de ${totalQuestions}...`}
            </span>
            <span className="font-medium text-kipiai-dark">
              {evaluationProgress.current}/{totalQuestions}
            </span>
          </div>
          <ProgressBar value={isDone ? 100 : progressPercent} height="lg" />
        </div>

        {/* Individual question status */}
        <div className="space-y-2" role="list" aria-label="Status das perguntas">
          {QUESTION_LABELS.slice(0, totalQuestions).map((label, index) => {
            const hasResult = index < results.length;
            const isEvaluating =
              !isDone && index === evaluationProgress.current - 1;

            return (
              <div
                key={index}
                role="listitem"
                className="flex items-center gap-3 text-sm"
              >
                <div
                  className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 ${
                    hasResult
                      ? "bg-kipiai-green text-white"
                      : isEvaluating
                      ? "bg-kipiai-blue text-white animate-pulse"
                      : "bg-gray-200 text-gray-400"
                  }`}
                  aria-hidden="true"
                >
                  {hasResult ? (
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="12"
                      height="12"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="3"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M20 6 9 17l-5-5" />
                    </svg>
                  ) : isEvaluating ? (
                    <div className="w-2 h-2 bg-white rounded-full" />
                  ) : (
                    <span className="text-xs">{index + 1}</span>
                  )}
                </div>
                <span
                  className={
                    hasResult
                      ? "text-kipiai-dark"
                      : isEvaluating
                      ? "text-kipiai-blue font-medium"
                      : "text-gray-400"
                  }
                >
                  {label}
                  {hasResult && results[index] && (
                    <span className="ml-2 text-kipiai-gray">
                      — Score: {results[index].score}
                    </span>
                  )}
                </span>
              </div>
            );
          })}
        </div>

        {isError && (
          <div className="bg-red-50 border border-kipiai-red/20 rounded-lg p-4 space-y-3">
            <p className="text-sm text-kipiai-red">
              {errorMessage || "Ocorreu um erro durante a avaliacao."}
            </p>
            <Button variant="danger" size="sm" onClick={handleRetry}>
              Tentar novamente
            </Button>
          </div>
        )}
      </div>
    </Card>
  );
}
