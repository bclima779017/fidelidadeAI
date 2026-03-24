"use client";

import React, { memo } from "react";
import { motion } from "motion/react";

interface ScoreGaugeProps {
  value: number;
  size?: number;
  label?: string;
}

function getColor(value: number): string {
  if (value >= 70) return "#28a745";
  if (value >= 50) return "#ffc107";
  return "#dc3545";
}

export const ScoreGauge = memo(function ScoreGauge({
  value,
  size = 120,
  label,
}: ScoreGaugeProps) {
  const clamped = Math.max(0, Math.min(100, value));
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const color = value < 0 ? "#6c757d" : getColor(clamped);
  const displayValue = value < 0 ? "—" : Math.round(clamped);

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            className="text-gray-200 dark:text-gray-700"
            strokeWidth={10}
          />
          {/* Animated progress circle */}
          {value >= 0 && (
            <motion.circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={color}
              strokeWidth={10}
              strokeLinecap="round"
              strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: circumference - (clamped / 100) * circumference }}
              transition={{ duration: 1.2, ease: "easeOut", delay: 0.2 }}
            />
          )}
        </svg>
        {/* Center value */}
        <div className="absolute inset-0 flex items-center justify-center">
          <motion.span
            className="text-2xl font-bold text-kipiai-dark dark:text-white"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            {displayValue}
          </motion.span>
        </div>
      </div>
      {label && (
        <span className="text-xs text-kipiai-gray dark:text-gray-400">{label}</span>
      )}
    </div>
  );
});
