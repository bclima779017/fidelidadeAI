"use client";

import React, { memo } from "react";
import { useAuditStore } from "@/lib/store";
import { Card } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Badge } from "@/components/ui/Badge";

const QUESTION_SHORT = [
  "Proposta de valor",
  "Diferenciais",
  "Publico-alvo",
  "Problema resolvido",
  "Produtos/servicos",
];

export const ResultsTable = memo(function ResultsTable() {
  const results = useAuditStore((s) => s.results);

  return (
    <Card title="Resumo dos Resultados">
      <div className="overflow-x-auto">
        <table className="w-full text-sm" aria-label="Tabela de resultados da auditoria">
          <thead>
            <tr className="border-b border-gray-200">
              <th scope="col" className="text-left py-3 px-2 text-kipiai-gray font-medium">
                Pergunta
              </th>
              <th scope="col" className="text-center py-3 px-2 text-kipiai-gray font-medium w-36">
                Match Semantico
              </th>
              <th scope="col" className="text-center py-3 px-2 text-kipiai-gray font-medium w-36">
                Taxa Claims
              </th>
              <th scope="col" className="text-center py-3 px-2 text-kipiai-gray font-medium w-24">
                Score
              </th>
            </tr>
          </thead>
          <tbody>
            {results.map((result, index) => (
              <tr
                key={index}
                className="border-b border-gray-100 last:border-b-0"
              >
                <td className="py-3 px-2 text-kipiai-dark font-medium">
                  {QUESTION_SHORT[index] || `Pergunta ${index + 1}`}
                </td>
                <td className="py-3 px-2">
                  <ProgressBar
                    value={Math.round(result.semantic_match ?? 0)}
                    height="sm"
                  />
                </td>
                <td className="py-3 px-2">
                  <ProgressBar
                    value={Math.round(result.claims_rate ?? 0)}
                    height="sm"
                  />
                </td>
                <td className="py-3 px-2 text-center">
                  <Badge score={result.score} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
});
