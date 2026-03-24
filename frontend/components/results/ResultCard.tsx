"use client";

import React, { useState, memo } from "react";
import { EvaluateResult } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";

const QUESTION_LABELS = [
  "Qual e a proposta de valor da marca?",
  "Quais sao os principais diferenciais competitivos?",
  "Qual e o publico-alvo da marca?",
  "Qual problema a marca resolve para seus clientes?",
  "Quais sao os principais produtos e/ou servicos?",
];

interface ResultCardProps {
  result: EvaluateResult;
  index: number;
}

export const ResultCard = memo(function ResultCard({
  result,
  index,
}: ResultCardProps) {
  const [expanded, setExpanded] = useState(false);

  const question = QUESTION_LABELS[index] || `Pergunta ${index + 1}`;

  return (
    <div className="bg-white rounded-xl shadow-md overflow-hidden">
      {/* Header */}
      <button
        className="w-full flex items-center gap-3 p-4 hover:bg-gray-50 transition-colors text-left cursor-pointer"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
        aria-label={`${question} — Score: ${result.score}. ${expanded ? "Recolher" : "Expandir"} detalhes`}
      >
        <span className="flex-shrink-0 w-7 h-7 rounded-full bg-kipiai-blue/10 flex items-center justify-center text-xs font-bold text-kipiai-blue">
          {index + 1}
        </span>
        <span className="flex-1 font-medium text-kipiai-dark text-sm">
          {question}
        </span>
        <Badge score={result.score} />
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`text-kipiai-gray transition-transform flex-shrink-0 ${
            expanded ? "rotate-180" : ""
          }`}
          aria-hidden="true"
        >
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-gray-100 p-4 space-y-4">
          {/* Responses comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="text-xs font-semibold text-kipiai-gray uppercase tracking-wider mb-2">
                Resposta do Especialista
              </h4>
              <div className="bg-gray-50 rounded-lg p-3 text-sm text-kipiai-dark whitespace-pre-wrap">
                {result.expert_answer || "Nao informada"}
              </div>
            </div>
            <div>
              <h4 className="text-xs font-semibold text-kipiai-gray uppercase tracking-wider mb-2">
                Resposta da IA
              </h4>
              <div className="bg-blue-50 rounded-lg p-3 text-sm text-kipiai-dark whitespace-pre-wrap">
                {result.ai_answer || "Nao disponivel"}
              </div>
            </div>
          </div>

          {/* Score breakdown */}
          <div>
            <h4 className="text-xs font-semibold text-kipiai-gray uppercase tracking-wider mb-2">
              Detalhamento do Score
            </h4>
            <div className="grid grid-cols-3 gap-3" role="group" aria-label="Metricas do score">
              <div className="bg-gray-50 rounded-lg p-3 text-center">
                <p className="text-xs text-kipiai-gray mb-1">Score</p>
                <p className="text-lg font-bold text-kipiai-dark">
                  {result.score >= 0 ? result.score : "N/A"}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3 text-center">
                <p className="text-xs text-kipiai-gray mb-1">
                  Match Semantico
                </p>
                <p className="text-lg font-bold text-kipiai-dark">
                  {result.semantic_match != null
                    ? `${Math.round(result.semantic_match)}%`
                    : "N/A"}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3 text-center">
                <p className="text-xs text-kipiai-gray mb-1">Taxa Claims</p>
                <p className="text-lg font-bold text-kipiai-dark">
                  {result.claims_rate != null
                    ? `${Math.round(result.claims_rate)}%`
                    : "N/A"}
                </p>
              </div>
            </div>
          </div>

          {/* Justificativa */}
          {result.justificativa && (
            <div>
              <h4 className="text-xs font-semibold text-kipiai-gray uppercase tracking-wider mb-2">
                Justificativa
              </h4>
              <div className="bg-yellow-50 rounded-lg p-3 text-sm text-kipiai-dark whitespace-pre-wrap">
                {result.justificativa}
              </div>
            </div>
          )}

          {/* Claims analysis */}
          {((result.claims_preservados && result.claims_preservados.length > 0) ||
            (result.claims_omitidos && result.claims_omitidos.length > 0)) && (
            <div>
              <h4 className="text-xs font-semibold text-kipiai-gray uppercase tracking-wider mb-2">
                Analise de Claims
              </h4>
              <div className="space-y-2" role="list">
                {(result.claims_preservados || []).map((claim, ci) => (
                  <div
                    key={`p-${ci}`}
                    role="listitem"
                    className="flex items-start gap-2 bg-gray-50 rounded-lg p-2 text-sm"
                  >
                    <span
                      className="mt-0.5 flex-shrink-0 w-4 h-4 rounded-full flex items-center justify-center text-xs bg-kipiai-green text-white"
                      aria-label="Preservado"
                    >
                      {"\u2713"}
                    </span>
                    <span className="text-kipiai-dark">{claim}</span>
                  </div>
                ))}
                {(result.claims_omitidos || []).map((claim, ci) => (
                  <div
                    key={`o-${ci}`}
                    role="listitem"
                    className="flex items-start gap-2 bg-gray-50 rounded-lg p-2 text-sm"
                  >
                    <span
                      className="mt-0.5 flex-shrink-0 w-4 h-4 rounded-full flex items-center justify-center text-xs bg-kipiai-red text-white"
                      aria-label="Omitido"
                    >
                      {"\u2717"}
                    </span>
                    <span className="text-kipiai-dark">{claim}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
});
