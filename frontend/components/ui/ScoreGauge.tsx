"use client";

import React, { memo } from "react";
import { motion } from "motion/react";

interface ScoreGaugeProps {
  value: number;
  size?: number;
  label?: string;
}

function getColor(value: number): { main: string; gradient: string } {
  if (value >= 70) return { main: "#28a745", gradient: "#116dff" };
  if (value >= 50) return { main: "#ffc107", gradient: "#f59e0b" };
  return { main: "#dc3545", gradient: "#ef4444" };
}

export const ScoreGauge = memo(function ScoreGauge({
  value,
  size = 120,
  label,
}: ScoreGaugeProps) {
  const clamped = Math.max(0, Math.min(100, value));
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const colors = value < 0 ? { main: "#6c757d", gradient: "#6c757d" } : getColor(clamped);
  const displayValue = value < 0 ? "—" : Math.round(clamped);
  const gaugeId = `gauge-grad-${size}-${label || "default"}`;

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <defs>
            <linearGradient id={gaugeId} x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor={colors.gradient} />
              <stop offset="100%" stopColor={colors.main} />
            </linearGradient>
            <filter id={`${gaugeId}-glow`}>
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            className="text-gray-100 dark:text-gray-800"
            strokeWidth={8}
          />
          {/* Animated progress circle */}
          {value >= 0 && (
            <motion.circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={`url(#${gaugeId})`}
              strokeWidth={8}
              strokeLinecap="round"
              strokeDasharray={circumference}
              filter={`url(#${gaugeId}-glow)`}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: circumference - (clamped / 100) * circumference }}
              transition={{ duration: 1.2, ease: "easeOut", delay: 0.2 }}
            />
          )}
        </svg>
        {/* Center value */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            className="text-2xl font-bold text-kipiai-dark dark:text-white"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            {displayValue}
          </motion.span>
          {value >= 0 && (
            <span className="text-[10px] text-kipiai-gray dark:text-gray-500 -mt-0.5">/100</span>
          )}
        </div>
      </div>
      {label && (
        <span className="text-xs font-medium text-kipiai-gray dark:text-gray-400">{label}</span>
      )}
    </div>
  );
});
