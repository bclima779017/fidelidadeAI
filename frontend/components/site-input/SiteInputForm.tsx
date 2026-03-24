"use client";

import React, { useState, useCallback } from "react";
import { useAuditStore } from "@/lib/store";
import { extractContent } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

const MIN_CONTENT_LENGTH = 100;
const MAX_URL_LENGTH = 2048;

function isValidUrl(input: string): boolean {
  let url = input.trim();
  if (!url) return false;
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    url = "https://" + url;
  }
  try {
    const parsed = new URL(url);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

export function SiteInputForm() {
  const url = useAuditStore((s) => s.url);
  const setUrl = useAuditStore((s) => s.setUrl);
  const setContent = useAuditStore((s) => s.setContent);
  const currentStep = useAuditStore((s) => s.currentStep);
  const setCurrentStep = useAuditStore((s) => s.setCurrentStep);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [charCount, setCharCount] = useState<number | null>(null);
  const [contentWarning, setContentWarning] = useState<string | null>(null);

  const isCompleted = currentStep >= 2;

  const handleExtract = useCallback(async () => {
    const trimmed = url.trim();

    if (!trimmed) {
      setError("Informe a URL do site");
      return;
    }

    if (trimmed.length > MAX_URL_LENGTH) {
      setError(`URL excede o tamanho maximo (${MAX_URL_LENGTH} caracteres)`);
      return;
    }

    if (!isValidUrl(trimmed)) {
      setError("URL com formato invalido. Exemplo: https://exemplo.com.br");
      return;
    }

    setLoading(true);
    setError(null);
    setContentWarning(null);

    try {
      const response = await extractContent(trimmed);
      setContent(response.content, response.title);
      setCharCount(response.content.length);

      if (response.content.length < MIN_CONTENT_LENGTH) {
        setContentWarning(
          `Conteudo extraido muito curto (${response.content.length} chars). A avaliacao pode ser imprecisa.`
        );
      }

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
  }, [url, setContent, setCurrentStep]);

  return (
    <Card title="1. URL do Site">
      <div className="space-y-4">
        <Input
          type="url"
          label="Endereco do site para auditoria"
          placeholder="https://exemplo.com.br"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !loading && !isCompleted && url.trim()) {
              handleExtract();
            }
          }}
          disabled={loading || isCompleted}
          error={error || undefined}
          aria-describedby={charCount ? "char-count-info" : undefined}
        />

        {!isCompleted && (
          <Button
            onClick={handleExtract}
            loading={loading}
            disabled={!url.trim()}
          >
            {loading ? "Extraindo..." : "Extrair Contexto"}
          </Button>
        )}

        {charCount !== null && (
          <div id="char-count-info" className="flex items-center gap-2 text-sm">
            <span className="w-2 h-2 rounded-full bg-kipiai-green" aria-hidden="true" />
            <span className="text-kipiai-gray">
              Conteudo extraido: {charCount.toLocaleString("pt-BR")} caracteres
            </span>
          </div>
        )}

        {contentWarning && (
          <div className="flex items-center gap-2 text-sm bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <span className="text-yellow-600">{contentWarning}</span>
          </div>
        )}
      </div>
    </Card>
  );
}
