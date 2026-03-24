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
          className="block text-sm font-medium text-kipiai-dark mb-1.5"
        >
          {label}
        </label>
      )}
      <textarea
        id={textareaId}
        className={`
          w-full px-4 py-2.5 border border-gray-300 rounded-lg
          focus:outline-none focus:ring-2 focus:ring-kipiai-blue focus:border-transparent
          placeholder-gray-400 text-kipiai-dark
          transition-shadow duration-200 resize-vertical min-h-[100px]
          disabled:opacity-60 disabled:cursor-not-allowed disabled:bg-gray-100
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
