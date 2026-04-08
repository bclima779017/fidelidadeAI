"use client";

import React from "react";
import { useAuditStore } from "@/lib/store";

const steps = [
  { label: "URL do site", step: 1 },
  { label: "Respostas do especialista", step: 2 },
  { label: "Avaliacao", step: 3 },
  { label: "Resultados", step: 4 },
];

export function StepIndicator() {
  const currentStep = useAuditStore((s) => s.currentStep);

  return (
    <nav aria-label="Etapas da auditoria">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">
        Etapas
      </p>
      <ol className="space-y-0">
        {steps.map((item, index) => {
          const isCompleted = currentStep > item.step;
          const isCurrent = currentStep === item.step;
          const isFuture = currentStep < item.step;

          return (
            <li
              key={item.step}
              className="relative flex items-start gap-3"
              aria-current={isCurrent ? "step" : undefined}
            >
              {/* Connecting line */}
              {index < steps.length - 1 && (
                <div
                  className={`absolute left-[11px] top-6 w-0.5 h-6 transition-colors duration-500 ${
                    isCompleted ? "bg-kipiai-green" : "bg-gray-700/50"
                  }`}
                  aria-hidden="true"
                />
              )}

              {/* Circle indicator */}
              <div
                className={`
                  flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center
                  text-xs font-bold transition-all duration-300
                  ${
                    isCompleted
                      ? "bg-kipiai-green text-white"
                      : isCurrent
                      ? "bg-kipiai-blue text-white shadow-kipiai-glow animate-glow-pulse"
                      : "bg-gray-800 text-gray-600"
                  }
                `}
                aria-hidden="true"
              >
                {isCompleted ? (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="3"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M20 6 9 17l-5-5" />
                  </svg>
                ) : (
                  item.step
                )}
              </div>

              {/* Label */}
              <span
                className={`
                  text-sm pt-0.5 pb-6 transition-all duration-300
                  ${
                    isCompleted
                      ? "text-kipiai-green font-medium"
                      : isCurrent
                      ? "text-white font-medium"
                      : "text-gray-500"
                  }
                  ${isFuture ? "opacity-35" : ""}
                `}
              >
                {item.label}
              </span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
