"use client";

import React, { memo, useMemo } from "react";
import { useAuditStore } from "@/lib/store";
import { Badge } from "@/components/ui/Badge";

export const ScoreCards = memo(function ScoreCards() {
  const results = useAuditStore((s) => s.results);
  const weightedScore = useAuditStore((s) => s.weightedScore);

  const { minScore, maxScore, finalScore } = useMemo(() => {
    const scores = results.map((r) => r.score).filter((s) => s >= 0);
    return {
      minScore: scores.length > 0 ? Math.min(...scores) : 0,
      maxScore: scores.length > 0 ? Math.max(...scores) : 0,
      finalScore:
        weightedScore ??
        (scores.length > 0
          ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
          : 0),
    };
  }, [results, weightedScore]);

  const cards = [
    { label: "Score Final Ponderado", value: finalScore },
    { label: "Score Minimo", value: minScore },
    { label: "Score Maximo", value: maxScore },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4" role="group" aria-label="Resumo dos scores">
      {cards.map((card) => (
        <div
          key={card.label}
          className="bg-white rounded-xl shadow-md p-6 text-center"
          role="article"
          aria-label={`${card.label}: ${card.value}`}
        >
          <p className="text-sm text-kipiai-gray mb-2">{card.label}</p>
          <div className="flex items-center justify-center gap-3">
            <span className="text-4xl font-bold text-kipiai-dark">
              {card.value}
            </span>
            <Badge score={card.value} size="lg" />
          </div>
        </div>
      ))}
    </div>
  );
});
