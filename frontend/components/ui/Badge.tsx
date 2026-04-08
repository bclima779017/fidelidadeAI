"use client";

import React from "react";

interface BadgeProps {
  score: number;
  size?: "sm" | "md" | "lg";
}

function getScoreStyle(score: number): string {
  if (!Number.isFinite(score) || score < 0)
    return "bg-gray-100 text-kipiai-gray dark:bg-gray-800 dark:text-gray-400";
  if (score >= 70)
    return "bg-green-50 text-kipiai-green border border-green-200/50 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800/30";
  if (score >= 50)
    return "bg-yellow-50 text-kipiai-yellow border border-yellow-200/50 dark:bg-yellow-900/20 dark:text-yellow-400 dark:border-yellow-800/30";
  return "bg-red-50 text-kipiai-red border border-red-200/50 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800/30";
}

const sizeStyles = {
  sm: "px-2 py-0.5 text-xs",
  md: "px-3 py-1 text-sm",
  lg: "px-4 py-1.5 text-base",
};

export function Badge({ score, size = "md" }: BadgeProps) {
  const label = !Number.isFinite(score) || score < 0 ? "Erro" : `${score}`;

  return (
    <span
      className={`
        inline-flex items-center font-bold rounded-full
        ${getScoreStyle(score)}
        ${sizeStyles[size]}
      `}
    >
      {label}
    </span>
  );
}
