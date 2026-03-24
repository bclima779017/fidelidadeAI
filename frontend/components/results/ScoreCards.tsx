"use client";

import React, { memo, useMemo, useEffect, useRef } from "react";
import { motion } from "motion/react";
import confetti from "canvas-confetti";
import { useAuditStore } from "@/lib/store";
import { ScoreGauge } from "@/components/ui/ScoreGauge";

export const ScoreCards = memo(function ScoreCards() {
  const results = useAuditStore((s) => s.results);
  const weightedScore = useAuditStore((s) => s.weightedScore);
  const confettiFired = useRef(false);

  const { minScore, maxScore, finalScore } = useMemo(() => {
    const scores = results.filter(Boolean).map((r) => r.score).filter((s) => s >= 0);
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

  // Confetti for high scores
  useEffect(() => {
    if (finalScore >= 90 && !confettiFired.current) {
      confettiFired.current = true;
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ["#28a745", "#116dff", "#ffc107"],
      });
    }
  }, [finalScore]);

  const cards = [
    { label: "Score Final Ponderado", value: finalScore },
    { label: "Score Minimo", value: minScore },
    { label: "Score Maximo", value: maxScore },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4" role="group" aria-label="Resumo dos scores">
      {cards.map((card, i) => (
        <motion.div
          key={card.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: i * 0.1 }}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 flex flex-col items-center"
          role="article"
          aria-label={`${card.label}: ${card.value}`}
        >
          <p className="text-sm text-kipiai-gray dark:text-gray-400 mb-3">{card.label}</p>
          <ScoreGauge
            value={card.value}
            size={i === 0 ? 130 : 100}
          />
        </motion.div>
      ))}
    </div>
  );
});
