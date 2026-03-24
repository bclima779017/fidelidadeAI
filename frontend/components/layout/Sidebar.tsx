"use client";

import React, { useState } from "react";
import Link from "next/link";
import { StepIndicator } from "./StepIndicator";
import { useAuditStore } from "@/lib/store";

export function Sidebar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const ragStats = useAuditStore((s) => s.ragStats);

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        className="fixed top-4 left-4 z-50 md:hidden bg-kipiai-dark text-white p-2 rounded-lg"
        onClick={() => setMobileOpen(!mobileOpen)}
        aria-label="Menu"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          {mobileOpen ? (
            <>
              <path d="M18 6 6 18" />
              <path d="m6 6 12 12" />
            </>
          ) : (
            <>
              <path d="M4 6h16" />
              <path d="M4 12h16" />
              <path d="M4 18h16" />
            </>
          )}
        </svg>
      </button>

      {/* Overlay for mobile */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 h-full w-[280px] bg-kipiai-dark z-40
          flex flex-col transition-transform duration-300
          md:translate-x-0
          ${mobileOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        {/* Logo */}
        <div className="px-6 py-6 border-b border-gray-800">
          <Link href="/" className="block">
            <h1 className="text-2xl font-bold text-kipiai-blue tracking-tight">
              Kipiai
            </h1>
            <p className="text-xs text-gray-500 mt-0.5">
              Auditoria de Fidelidade GEO
            </p>
          </Link>
        </div>

        {/* Step Indicator */}
        <div className="flex-1 px-6 py-6 overflow-y-auto">
          <StepIndicator />

          {/* RAG Stats no sidebar */}
          {ragStats && (
            <div className="mt-6 pt-4 border-t border-gray-800">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                Indice RAG
              </p>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Paginas</span>
                  <span className="text-white font-medium">{ragStats.total_pages}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Chunks</span>
                  <span className="text-white font-medium">{ragStats.total_chunks}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Chunks/pag</span>
                  <span className="text-white font-medium">
                    {ragStats.total_pages > 0
                      ? (ragStats.total_chunks / ragStats.total_pages).toFixed(1)
                      : "0"}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-800">
          <p className="text-xs text-gray-600">
            v0.2.0
          </p>
        </div>
      </aside>
    </>
  );
}
