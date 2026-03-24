"use client";

import React from "react";

interface ProgressBarProps {
  value: number;
  className?: string;
  showLabel?: boolean;
  height?: "sm" | "md" | "lg";
}

function getScoreColor(value: number): string {
  if (value >= 70) return "bg-kipiai-green";
  if (value >= 50) return "bg-kipiai-yellow";
  return "bg-kipiai-red";
}

const heightStyles = {
  sm: "h-2",
  md: "h-3",
  lg: "h-4",
};

export function ProgressBar({
  value,
  className = "",
  showLabel = false,
  height = "md",
}: ProgressBarProps) {
  const clampedValue = Math.max(0, Math.min(100, value));

  return (
    <div className={`w-full ${className}`}>
      {showLabel && (
        <div className="flex justify-between mb-1">
          <span className="text-sm font-medium text-kipiai-dark">
            Progresso
          </span>
          <span className="text-sm font-medium text-kipiai-dark">
            {clampedValue}%
          </span>
        </div>
      )}
      <div
        className={`w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden ${heightStyles[height]}`}
      >
        <div
          className={`${getScoreColor(clampedValue)} ${heightStyles[height]} rounded-full transition-all duration-500 ease-out`}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
    </div>
  );
}
