"use client";

import React, { memo, useMemo } from "react";
import { useAuditStore } from "@/lib/store";
import { EvalHealth } from "@/lib/types";
import { Card } from "@/components/ui/Card";

const GRADE_STYLES = {
  green: "bg-kipiai-green text-white",
  blue: "bg-kipiai-blue text-white",
  yellow: "bg-yellow-500 text-white",
  red: "bg-kipiai-red text-white",
};

function getHealthGrade(health: EvalHealth): { label: string; color: keyof typeof GRADE_STYLES } {
  // Fraca: problemas graves
  if (health.total_retries > 3) return { label: "Fraca", color: "red" };
  if (health.pct_lost > 20) return { label: "Fraca", color: "red" };
  if (health.poor_extraction_pages.length > 3) return { label: "Fraca", color: "red" };

  // Mediana: warnings significativos
  if (health.context_truncated) return { label: "Mediana", color: "yellow" };
  const warningCount =
    (health.json_parse_failures > 0 ? 1 : 0) +
    (health.total_retries > 0 ? 1 : 0) +
    (health.thin_chunks.length > 0 ? 1 : 0) +
    (health.poor_extraction_pages.length > 0 ? 1 : 0);
  if (warningCount >= 3) return { label: "Mediana", color: "yellow" };

  // Boa: 1-2 warnings menores
  if (warningCount > 0) return { label: "Boa", color: "blue" };

  // Excelente: sem warnings
  return { label: "Excelente", color: "green" };
}

export const HealthPanel = memo(function HealthPanel() {
  const health = useAuditStore((s) => s.health);
  const ragStats = useAuditStore((s) => s.ragStats);

  const grade = useMemo(() => (health ? getHealthGrade(health) : null), [health]);

  if (!health && !ragStats) return null;

  return (
    <div className="bg-white rounded-xl shadow-md overflow-hidden">
      {/* Header com selo */}
      <div className="flex items-center justify-between p-5 pb-0">
        <h3 className="text-lg font-semibold text-kipiai-dark">Saude da Avaliacao</h3>
        {grade && (
          <span
            className={`px-4 py-1.5 rounded-full text-sm font-bold ${GRADE_STYLES[grade.color]}`}
            aria-label={`Qualidade: ${grade.label}`}
          >
            {grade.label}
          </span>
        )}
      </div>

      <div className="p-5 space-y-4">
        {/* RAG Stats */}
        {ragStats && (
          <div>
            <h4 className="text-xs font-semibold text-kipiai-gray uppercase tracking-wider mb-2">
              Indice RAG
            </h4>
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-blue-50 rounded-lg p-3 text-center">
                <p className="text-xs text-kipiai-gray mb-1">Paginas</p>
                <p className="text-xl font-bold text-kipiai-dark">{ragStats.total_pages}</p>
              </div>
              <div className="bg-blue-50 rounded-lg p-3 text-center">
                <p className="text-xs text-kipiai-gray mb-1">Chunks</p>
                <p className="text-xl font-bold text-kipiai-dark">{ragStats.total_chunks}</p>
              </div>
              <div className="bg-blue-50 rounded-lg p-3 text-center">
                <p className="text-xs text-kipiai-gray mb-1">Chunks/Pagina</p>
                <p className="text-xl font-bold text-kipiai-dark">
                  {ragStats.total_pages > 0
                    ? (ragStats.total_chunks / ragStats.total_pages).toFixed(1)
                    : "0"}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Health Indicators */}
        {health && (
          <div>
            <h4 className="text-xs font-semibold text-kipiai-gray uppercase tracking-wider mb-2">
              Indicadores de Qualidade
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <div className={`rounded-lg p-3 text-center ${health.context_truncated ? "bg-yellow-50" : "bg-gray-50"}`}>
                <p className="text-xs text-kipiai-gray mb-1">Contexto Truncado</p>
                <p className={`text-lg font-bold ${health.context_truncated ? "text-yellow-600" : "text-kipiai-green"}`}>
                  {health.context_truncated ? "Sim" : "Nao"}
                </p>
                {health.context_truncated && (
                  <p className="text-xs text-yellow-600 mt-1">-{health.pct_lost.toFixed(1)}%</p>
                )}
              </div>

              <div className={`rounded-lg p-3 text-center ${health.json_parse_failures > 0 ? "bg-yellow-50" : "bg-gray-50"}`}>
                <p className="text-xs text-kipiai-gray mb-1">Fallback JSON</p>
                <p className={`text-lg font-bold ${health.json_parse_failures > 0 ? "text-yellow-600" : "text-kipiai-green"}`}>
                  {health.json_parse_failures}
                </p>
              </div>

              <div className={`rounded-lg p-3 text-center ${health.total_retries > 0 ? "bg-yellow-50" : "bg-gray-50"}`}>
                <p className="text-xs text-kipiai-gray mb-1">Retries API</p>
                <p className={`text-lg font-bold ${health.total_retries > 0 ? "text-yellow-600" : "text-kipiai-green"}`}>
                  {health.total_retries}
                </p>
              </div>

              <div className={`rounded-lg p-3 text-center ${health.poor_extraction_pages.length > 0 ? "bg-yellow-50" : "bg-gray-50"}`}>
                <p className="text-xs text-kipiai-gray mb-1">Pag. Fracas</p>
                <p className={`text-lg font-bold ${health.poor_extraction_pages.length > 0 ? "text-yellow-600" : "text-kipiai-green"}`}>
                  {health.poor_extraction_pages.length}
                </p>
              </div>

              <div className={`rounded-lg p-3 text-center ${health.thin_chunks.length > 0 ? "bg-yellow-50" : "bg-gray-50"}`}>
                <p className="text-xs text-kipiai-gray mb-1">Chunks Finos</p>
                <p className={`text-lg font-bold ${health.thin_chunks.length > 0 ? "text-yellow-600" : "text-kipiai-green"}`}>
                  {health.thin_chunks.length}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
});
