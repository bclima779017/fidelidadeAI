"use client";

import React from "react";
import { useAuditStore } from "@/lib/store";
import { Badge } from "@/components/ui/Badge";

export function ScoreCards() {
  const { results, weightedScore } = useAuditStore();

  const scores = results.map((r) => r.score).filter((s) => s >= 0);
  const minScore = scores.length > 0 ? Math.min(...scores) : 0;
  const maxScore = scores.length > 0 ? Math.max(...scores) : 0;
  const finalScore = weightedScore ?? (scores.length > 0
    ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
    : 0);

  const cards = [
    { label: "Score Final Ponderado", value: finalScore },
    { label: "Score Minimo", value: minScore },
    { label: "Score Maximo", value: maxScore },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="bg-white rounded-xl shadow-md p-6 text-center"
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
}
