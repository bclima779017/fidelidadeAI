"use client";

import React, { useState } from "react";

interface CardProps {
  title?: string;
  collapsible?: boolean;
  defaultOpen?: boolean;
  children: React.ReactNode;
  className?: string;
}

export function Card({
  title,
  collapsible = false,
  defaultOpen = true,
  children,
  className = "",
}: CardProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 ${className}`}>
      {title && (
        <div
          className={`flex items-center justify-between mb-4 ${
            collapsible ? "cursor-pointer select-none" : ""
          }`}
          onClick={collapsible ? () => setOpen(!open) : undefined}
        >
          <h3 className="text-lg font-semibold text-kipiai-dark dark:text-white">{title}</h3>
          {collapsible && (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className={`text-kipiai-gray transition-transform ${
                open ? "rotate-180" : ""
              }`}
            >
              <path d="m6 9 6 6 6-6" />
            </svg>
          )}
        </div>
      )}
      {(!collapsible || open) && children}
    </div>
  );
}
