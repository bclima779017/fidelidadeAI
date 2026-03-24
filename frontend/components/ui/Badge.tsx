"use client";

import React from "react";

interface BadgeProps {
  score: number;
  size?: "sm" | "md" | "lg";
}

function getScoreStyle(score: number): string {
  if (!Number.isFinite(score) || score < 0) return "bg-gray-100 text-kipiai-gray";
  if (score >= 70) return "bg-green-100 text-kipiai-green";
  if (score >= 50) return "bg-yellow-100 text-kipiai-yellow";
  return "bg-red-100 text-kipiai-red";
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
