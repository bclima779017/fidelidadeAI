"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { StepIndicator } from "./StepIndicator";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { useAuditStore } from "@/lib/store";

export function Sidebar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const ragStats = useAuditStore((s) => s.ragStats);

  return (
    <>
      {/* Mobile hamburger */}
      <button
        className="fixed top-4 left-4 z-50 md:hidden bg-kipiai-dark text-white p-2 rounded-lg"
        onClick={() => setMobileOpen(!mobileOpen)}
        aria-label="Menu"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          {mobileOpen ? (<><path d="M18 6 6 18" /><path d="m6 6 12 12" /></>) : (<><path d="M4 6h16" /><path d="M4 12h16" /><path d="M4 18h16" /></>)}
        </svg>
      </button>

      {mobileOpen && (
        <div className="fixed inset-0 bg-black/50 z-30 md:hidden" onClick={() => setMobileOpen(false)} />
      )}

      <aside className={`fixed top-0 left-0 h-full w-[280px] bg-kipiai-sidebar border-r border-gray-800/50 z-40 flex flex-col transition-transform duration-300 md:translate-x-0 ${mobileOpen ? "translate-x-0" : "-translate-x-full"}`}>
        {/* Top gradient line */}
        <div className="h-[2px] bg-kipiai-gradient w-full flex-shrink-0" />

        {/* Logo + Theme toggle */}
        <div className="px-6 py-5 border-b border-gray-800/50 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <Image src="/logo-icon.svg" alt="Kipiai" width={32} height={32} className="flex-shrink-0" />
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">Kipiai</h1>
              <p className="text-[10px] text-gray-500 tracking-wide uppercase">Auditoria GEO</p>
            </div>
          </Link>
          <ThemeToggle />
        </div>

        {/* Step Indicator */}
        <div className="flex-1 px-6 py-6 overflow-y-auto">
          <StepIndicator />

          {ragStats && (
            <div className="mt-6 pt-4 border-t border-gray-800/50">
              <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-3">Indice RAG</p>
              <div className="bg-kipiai-blue-900/20 border border-kipiai-blue/10 rounded-lg p-3 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Paginas</span>
                  <span className="text-kipiai-blue-light font-medium">{ragStats.total_pages}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Chunks</span>
                  <span className="text-kipiai-blue-light font-medium">{ragStats.total_chunks}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Chunks/pag</span>
                  <span className="text-kipiai-blue-light font-medium">
                    {ragStats.total_pages > 0 ? (ragStats.total_chunks / ragStats.total_pages).toFixed(1) : "0"}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-gray-800/50 flex items-center justify-between">
          <p className="text-[10px] text-gray-600 uppercase tracking-wider">Kipiai Audit</p>
          <p className="text-[10px] text-gray-600">v0.3.0</p>
        </div>
      </aside>
    </>
  );
}
