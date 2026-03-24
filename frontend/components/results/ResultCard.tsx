"use client";

import React, { useState, memo } from "react";
import { motion, AnimatePresence } from "motion/react";
import { EvaluateResult } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { QUESTIONS } from "@/lib/constants";

interface ResultCardProps {
  result: EvaluateResult;
  index: number;
}

export const ResultCard = memo(function ResultCard({ result, index }: ResultCardProps) {
  const [expanded, setExpanded] = useState(false);
  const question = QUESTIONS[index]?.text || `Pergunta ${index + 1}`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.08 }}
      className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden"
    >
      <button
        className="w-full flex items-center gap-3 p-4 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors text-left cursor-pointer"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
        aria-label={`${question} — Score: ${result.score}`}
      >
        <span className="flex-shrink-0 w-7 h-7 rounded-full bg-kipiai-blue/10 dark:bg-kipiai-blue/20 flex items-center justify-center text-xs font-bold text-kipiai-blue">
          {index + 1}
        </span>
        <span className="flex-1 font-medium text-kipiai-dark dark:text-gray-100 text-sm">{question}</span>
        <Badge score={result.score} />
        <motion.svg
          xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          className="text-kipiai-gray flex-shrink-0"
          animate={{ rotate: expanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <path d="m6 9 6 6 6-6" />
        </motion.svg>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="border-t border-gray-100 dark:border-gray-700 p-4 space-y-4">
              {/* Responses comparison */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="text-xs font-semibold text-kipiai-gray uppercase tracking-wider mb-2">Resposta do Especialista</h4>
                  <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3 text-sm text-kipiai-dark dark:text-gray-200 whitespace-pre-wrap">
                    {result.expert_answer || result.official_answer || "Nao informada"}
                  </div>
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-kipiai-gray uppercase tracking-wider mb-2">Resposta da IA</h4>
                  <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-sm text-kipiai-dark dark:text-gray-200 whitespace-pre-wrap">
                    {result.ai_answer || result.resposta_ia || "Nao disponivel"}
                  </div>
                </div>
              </div>

              {/* Score breakdown */}
              <div>
                <h4 className="text-xs font-semibold text-kipiai-gray uppercase tracking-wider mb-2">Detalhamento do Score</h4>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { label: "Score", value: result.score >= 0 ? result.score : "N/A" },
                    { label: "Match Semantico", value: result.semantic_match ?? result.match_semantico != null ? `${Math.round(result.semantic_match ?? result.match_semantico ?? 0)}%` : "N/A" },
                    { label: "Taxa Claims", value: result.claims_rate ?? result.taxa_claims != null ? `${Math.round(result.claims_rate ?? result.taxa_claims ?? 0)}%` : "N/A" },
                  ].map((item) => (
                    <div key={item.label} className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3 text-center">
                      <p className="text-xs text-kipiai-gray mb-1">{item.label}</p>
                      <p className="text-lg font-bold text-kipiai-dark dark:text-white">{item.value}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Justificativa */}
              {result.justificativa && (
                <div>
                  <h4 className="text-xs font-semibold text-kipiai-gray uppercase tracking-wider mb-2">Justificativa</h4>
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3 text-sm text-kipiai-dark dark:text-gray-200 whitespace-pre-wrap">
                    {result.justificativa}
                  </div>
                </div>
              )}

              {/* Claims */}
              {((result.claims_preservados?.length ?? 0) > 0 || (result.claims_omitidos?.length ?? 0) > 0) && (
                <div>
                  <h4 className="text-xs font-semibold text-kipiai-gray uppercase tracking-wider mb-2">Analise de Claims</h4>
                  <div className="space-y-1.5" role="list">
                    {(result.claims_preservados || []).map((claim, ci) => (
                      <div key={`p-${ci}`} role="listitem" className="flex items-start gap-2 bg-gray-50 dark:bg-gray-900 rounded-lg p-2 text-sm">
                        <span className="mt-0.5 flex-shrink-0 w-4 h-4 rounded-full flex items-center justify-center text-xs bg-kipiai-green text-white" aria-label="Preservado">{"\u2713"}</span>
                        <span className="text-kipiai-dark dark:text-gray-200">{claim}</span>
                      </div>
                    ))}
                    {(result.claims_omitidos || []).map((claim, ci) => (
                      <div key={`o-${ci}`} role="listitem" className="flex items-start gap-2 bg-gray-50 dark:bg-gray-900 rounded-lg p-2 text-sm">
                        <span className="mt-0.5 flex-shrink-0 w-4 h-4 rounded-full flex items-center justify-center text-xs bg-kipiai-red text-white" aria-label="Omitido">{"\u2717"}</span>
                        <span className="text-kipiai-dark dark:text-gray-200">{claim}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
});
