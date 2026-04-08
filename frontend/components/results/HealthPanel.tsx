"use client";

import React, { memo, useMemo } from "react";
import { motion } from "motion/react";
import { useAuditStore } from "@/lib/store";
import { EvalHealth } from "@/lib/types";
import { Tooltip } from "@/components/ui/Tooltip";

const GRADE_STYLES = {
  green: "bg-kipiai-gradient text-white",
  blue: "bg-kipiai-blue text-white",
  yellow: "bg-yellow-500 text-white",
  red: "bg-kipiai-red text-white",
};

function getHealthGrade(health: EvalHealth): { label: string; color: keyof typeof GRADE_STYLES } {
  if (health.total_retries > 3) return { label: "Fraca", color: "red" };
  if (health.pct_lost > 20) return { label: "Fraca", color: "red" };
  if (health.poor_extraction_pages.length > 3) return { label: "Fraca", color: "red" };
  if (health.context_truncated) return { label: "Mediana", color: "yellow" };
  const wc =
    (health.json_parse_failures > 0 ? 1 : 0) +
    (health.total_retries > 0 ? 1 : 0) +
    (health.thin_chunks.length > 0 ? 1 : 0) +
    (health.poor_extraction_pages.length > 0 ? 1 : 0);
  if (wc >= 3) return { label: "Mediana", color: "yellow" };
  if (wc > 0) return { label: "Boa", color: "blue" };
  return { label: "Excelente", color: "green" };
}

interface IndicatorProps {
  label: string;
  value: string | number;
  warn: boolean;
  tooltip: string;
  extra?: string;
}

function Indicator({ label, value, warn, tooltip, extra }: IndicatorProps) {
  return (
    <Tooltip content={tooltip}>
      <div className={`rounded-lg p-3 text-center cursor-help border transition-colors ${warn ? "bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200/50 dark:border-yellow-800/30" : "bg-kipiai-gray-50 dark:bg-kipiai-gray-900 border-gray-100 dark:border-gray-800/50"}`}>
        <p className="text-xs text-kipiai-gray dark:text-gray-400 mb-1">{label}</p>
        <p className={`text-lg font-bold ${warn ? "text-yellow-600" : "text-kipiai-green"}`}>{value}</p>
        {extra && <p className="text-xs text-yellow-600 mt-1">{extra}</p>}
      </div>
    </Tooltip>
  );
}

export const HealthPanel = memo(function HealthPanel() {
  const health = useAuditStore((s) => s.health);
  const ragStats = useAuditStore((s) => s.ragStats);
  const grade = useMemo(() => (health ? getHealthGrade(health) : null), [health]);

  if (!health && !ragStats) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.15 }}
      className="bg-white dark:bg-kipiai-gray-800 rounded-xl shadow-kipiai-sm border border-gray-100 dark:border-gray-800/50 overflow-hidden"
    >
      <div className="flex items-center justify-between p-5 pb-0">
        <h3 className="text-lg font-semibold text-kipiai-dark dark:text-white">Saude da Avaliacao</h3>
        {grade && (
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 300, delay: 0.3 }}
            className={`px-4 py-1.5 rounded-full text-sm font-bold ${GRADE_STYLES[grade.color]}`}
          >
            {grade.label}
          </motion.span>
        )}
      </div>

      <div className="p-5 space-y-4">
        {ragStats && (
          <div>
            <h4 className="text-xs font-semibold text-kipiai-gray uppercase tracking-wider mb-2">Indice RAG</h4>
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: "Paginas", value: ragStats.total_pages },
                { label: "Chunks", value: ragStats.total_chunks },
                { label: "Chunks/Pag", value: ragStats.total_pages > 0 ? (ragStats.total_chunks / ragStats.total_pages).toFixed(1) : "0" },
              ].map((item) => (
                <div key={item.label} className="bg-kipiai-blue-50 dark:bg-kipiai-blue-900/20 rounded-lg p-3 text-center border border-kipiai-blue/10 dark:border-kipiai-blue/5">
                  <p className="text-xs text-kipiai-gray dark:text-gray-400 mb-1">{item.label}</p>
                  <p className="text-xl font-bold text-kipiai-dark dark:text-white">{item.value}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {health && (
          <div>
            <h4 className="text-xs font-semibold text-kipiai-gray uppercase tracking-wider mb-2">Indicadores de Qualidade</h4>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <Indicator
                label="Truncado"
                value={health.context_truncated ? "Sim" : "Nao"}
                warn={health.context_truncated}
                tooltip="Indica se o contexto foi cortado por exceder 100k caracteres"
                extra={health.context_truncated ? `-${health.pct_lost.toFixed(1)}%` : undefined}
              />
              <Indicator
                label="Fallback JSON"
                value={health.json_parse_failures}
                warn={health.json_parse_failures > 0}
                tooltip="Vezes que o parsing JSON do Gemini precisou de regex fallback"
              />
              <Indicator
                label="Retries API"
                value={health.total_retries}
                warn={health.total_retries > 0}
                tooltip="Chamadas a API que precisaram ser repetidas (rate limit ou erro)"
              />
              <Indicator
                label="Pag. Fracas"
                value={health.poor_extraction_pages.length}
                warn={health.poor_extraction_pages.length > 0}
                tooltip="Paginas com menos de 500 caracteres extraidos"
              />
              <Indicator
                label="Chunks Finos"
                value={health.thin_chunks.length}
                warn={health.thin_chunks.length > 0}
                tooltip="Chunks com menos de 200 caracteres (podem ter pouco conteudo semantico)"
              />
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
});
