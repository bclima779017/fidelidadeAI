"use client";

import React, { useState } from "react";
import { useAuditStore } from "@/lib/store";
import { extractContent } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

export function SiteInputForm() {
  const { url, setUrl, setContent, currentStep, setCurrentStep } =
    useAuditStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [charCount, setCharCount] = useState<number | null>(null);

  const isCompleted = currentStep >= 2;

  async function handleExtract() {
    if (!url.trim()) {
      setError("Informe a URL do site");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await extractContent(url.trim());
      setContent(response.content);
      setCharCount(response.content.length);
      setCurrentStep(2);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Erro ao extrair conteudo do site"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card title="1. URL do Site">
      <div className="space-y-4">
        <Input
          label="Endereco do site para auditoria"
          placeholder="https://exemplo.com.br"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={loading || isCompleted}
          error={error || undefined}
        />

        {!isCompleted && (
          <Button
            onClick={handleExtract}
            loading={loading}
            disabled={!url.trim()}
          >
            Extrair Contexto
          </Button>
        )}

        {charCount !== null && (
          <div className="flex items-center gap-2 text-sm">
            <span className="w-2 h-2 rounded-full bg-kipiai-green" />
            <span className="text-kipiai-gray">
              Conteudo extraido: {charCount.toLocaleString("pt-BR")} caracteres
            </span>
          </div>
        )}
      </div>
    </Card>
  );
}
