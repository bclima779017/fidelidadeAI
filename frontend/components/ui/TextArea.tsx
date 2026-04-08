"use client";

import React from "react";

interface TextAreaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export function TextArea({
  label,
  error,
  className = "",
  id,
  ...props
}: TextAreaProps) {
  const textareaId = id || label?.toLowerCase().replace(/\s+/g, "-");

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={textareaId}
          className="block text-sm font-medium text-kipiai-dark dark:text-gray-200 mb-1.5"
        >
          {label}
        </label>
      )}
      <textarea
        id={textareaId}
        className={`
          w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-lg
          bg-white dark:bg-kipiai-gray-900
          hover:border-kipiai-blue/40 dark:hover:border-kipiai-blue/30
          focus:outline-none focus:ring-1 focus:ring-kipiai-blue focus:border-kipiai-blue focus:shadow-kipiai-glow
          placeholder-gray-400 text-kipiai-dark dark:text-gray-100
          transition-all duration-200 resize-vertical min-h-[100px]
          disabled:opacity-60 disabled:cursor-not-allowed disabled:bg-gray-100 dark:disabled:bg-gray-800
          ${error ? "border-kipiai-red ring-1 ring-kipiai-red" : ""}
          ${className}
        `}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm text-kipiai-red">{error}</p>
      )}
    </div>
  );
}
