"use client";

import React, { memo } from "react";
import { motion } from "motion/react";
import { useAuditStore } from "@/lib/store";
import { Card } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Badge } from "@/components/ui/Badge";
import { QUESTIONS } from "@/lib/constants";

export const ResultsTable = memo(function ResultsTable() {
  const results = useAuditStore((s) => s.results);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.2 }}
    >
      <Card title="Resumo dos Resultados">
        <div className="overflow-x-auto">
          <table className="w-full text-sm" aria-label="Tabela de resultados">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th scope="col" className="text-left py-3 px-2 text-kipiai-gray font-medium">Pergunta</th>
                <th scope="col" className="text-center py-3 px-2 text-kipiai-gray font-medium w-36">Match Semantico</th>
                <th scope="col" className="text-center py-3 px-2 text-kipiai-gray font-medium w-36">Taxa Claims</th>
                <th scope="col" className="text-center py-3 px-2 text-kipiai-gray font-medium w-24">Score</th>
              </tr>
            </thead>
            <tbody>
              {results.map((result, index) => result ? (
                <tr key={index} className="border-b border-gray-100 dark:border-gray-800 last:border-b-0">
                  <td className="py-3 px-2 text-kipiai-dark dark:text-gray-200 font-medium">
                    {QUESTIONS[index]?.label || `Pergunta ${index + 1}`}
                  </td>
                  <td className="py-3 px-2">
                    <ProgressBar value={Math.round(result.semantic_match ?? result.match_semantico ?? 0)} height="sm" />
                  </td>
                  <td className="py-3 px-2">
                    <ProgressBar value={Math.round(result.claims_rate ?? result.taxa_claims ?? 0)} height="sm" />
                  </td>
                  <td className="py-3 px-2 text-center">
                    <Badge score={result.score} />
                  </td>
                </tr>
              ) : null)}
            </tbody>
          </table>
        </div>
      </Card>
    </motion.div>
  );
});
