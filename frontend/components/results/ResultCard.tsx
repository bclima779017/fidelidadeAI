"use client";

import React, { useState } from "react";
import { EvaluateResult } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";

const QUESTION_EMOJIS = ["💎", "⚡", "🎯", "🔧", "📦"];

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

export function ResultCard({ result, index }: ResultCardProps) {
  const [expanded, setExpanded] = useState(false);

  const emoji = QUESTION_EMOJIS[index] || "📋";
  const question = QUESTION_LABELS[index] || `Pergunta ${index + 1}`;

  return (
    <div className="bg-white rounded-xl shadow-md overflow-hidden">
      {/* Header */}
      <button
        className="w-full flex items-center gap-3 p-4 hover:bg-gray-50 transition-colors text-left"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="text-xl flex-shrink-0">{emoji}</span>
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
              <div className="bg-gray-50 rounded-lg p-3 text-sm text-kipiai-dark">
                {result.expert_answer || "Nao informada"}
              </div>
            </div>
            <div>
              <h4 className="text-xs font-semibold text-kipiai-gray uppercase tracking-wider mb-2">
                Resposta da IA
              </h4>
              <div className="bg-blue-50 rounded-lg p-3 text-sm text-kipiai-dark">
                {result.ai_answer || "Nao disponivel"}
              </div>
            </div>
          </div>

          {/* Score breakdown */}
          <div>
            <h4 className="text-xs font-semibold text-kipiai-gray uppercase tracking-wider mb-2">
              Detalhamento do Score
            </h4>
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-gray-50 rounded-lg p-3 text-center">
                <p className="text-xs text-kipiai-gray mb-1">Score</p>
                <p className="text-lg font-bold text-kipiai-dark">
                  {result.score}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3 text-center">
                <p className="text-xs text-kipiai-gray mb-1">
                  Match Semantico
                </p>
                <p className="text-lg font-bold text-kipiai-dark">
                  {result.semantic_match !== undefined
                    ? `${Math.round(result.semantic_match * 100)}%`
                    : "N/A"}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3 text-center">
                <p className="text-xs text-kipiai-gray mb-1">Taxa Claims</p>
                <p className="text-lg font-bold text-kipiai-dark">
                  {result.claims_rate !== undefined
                    ? `${Math.round(result.claims_rate * 100)}%`
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
              <div className="bg-yellow-50 rounded-lg p-3 text-sm text-kipiai-dark">
                {result.justificativa}
              </div>
            </div>
          )}

          {/* Claims analysis */}
          {result.claims && result.claims.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-kipiai-gray uppercase tracking-wider mb-2">
                Analise de Claims ({result.claims.length})
              </h4>
              <div className="space-y-2">
                {result.claims.map((claim, ci) => (
                  <div
                    key={ci}
                    className="flex items-start gap-2 bg-gray-50 rounded-lg p-2 text-sm"
                  >
                    <span
                      className={`mt-0.5 flex-shrink-0 w-4 h-4 rounded-full flex items-center justify-center text-xs ${
                        claim.preserved
                          ? "bg-kipiai-green text-white"
                          : "bg-kipiai-red text-white"
                      }`}
                    >
                      {claim.preserved ? "✓" : "✗"}
                    </span>
                    <span className="text-kipiai-dark">{claim.text}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
