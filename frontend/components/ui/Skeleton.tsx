"use client";

import React from "react";

interface SkeletonProps {
  className?: string;
  variant?: "text" | "circular" | "rectangular";
  width?: string | number;
  height?: string | number;
}

export function Skeleton({
  className = "",
  variant = "text",
  width,
  height,
}: SkeletonProps) {
  const base = "bg-gradient-to-r from-gray-100 via-gray-200 to-gray-100 dark:from-gray-800 dark:via-gray-700 dark:to-gray-800 bg-[length:200%_100%] animate-shimmer";
  const shapes = {
    text: "rounded",
    circular: "rounded-full",
    rectangular: "rounded-lg",
  };

  return (
    <div
      className={`${base} ${shapes[variant]} ${className}`}
      style={{ width, height }}
    />
  );
}

/** Skeleton placeholder for a ScoreCard */
export function ScoreCardSkeleton() {
  return (
    <div className="bg-white dark:bg-kipiai-gray-800 rounded-xl shadow-kipiai-sm border border-gray-100 dark:border-gray-800/50 p-6 text-center space-y-3">
      <Skeleton variant="text" className="h-4 w-24 mx-auto" />
      <Skeleton variant="circular" className="h-24 w-24 mx-auto" />
    </div>
  );
}

/** Skeleton placeholder for a ResultCard row */
export function ResultCardSkeleton() {
  return (
    <div className="bg-white dark:bg-kipiai-gray-800 rounded-xl shadow-kipiai-sm border border-gray-100 dark:border-gray-800/50 p-4 flex items-center gap-3">
      <Skeleton variant="circular" className="h-7 w-7 flex-shrink-0" />
      <Skeleton variant="text" className="h-4 flex-1" />
      <Skeleton variant="text" className="h-6 w-16" />
    </div>
  );
}
