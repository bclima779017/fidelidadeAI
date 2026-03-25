"use client";

import React, { useState, useCallback, useRef } from "react";
import { toast } from "sonner";
import { useAuditStore } from "@/lib/store";
import { extractContent, discoverSitemap, connectMultiExtract, indexRAG } from "@/lib/api";
import { MAX_URL_LENGTH, MIN_CONTENT_LENGTH } from "@/lib/constants";
import { ExtractResponse } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { ProgressBar } from "@/components/ui/ProgressBar";

function isValidUrl(input: string): boolean {
  let url = input.trim();
  if (!url) return false;
  if (!url.startsWith("http://") && !url.startsWith("https://")) url = "https://" + url;
  try {
    const parsed = new URL(url);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch { return false; }
}

export function SiteInputForm() {
  const url = useAuditStore((s) => s.url);
  const setUrl = useAuditStore((s) => s.setUrl);
  const setContent = useAuditStore((s) => s.setContent);
  const currentStep = useAuditStore((s) => s.currentStep);
  const setCurrentStep = useAuditStore((s) => s.setCurrentStep);
  const extractionMode = useAuditStore((s) => s.extractionMode);
  const setExtractionMode = useAuditStore((s) => s.setExtractionMode);
  const discoveredUrls = useAuditStore((s) => s.discoveredUrls);
  const setDiscoveredUrls = useAuditStore((s) => s.setDiscoveredUrls);
  const selectedUrls = useAuditStore((s) => s.selectedUrls);
  const toggleUrlSelection = useAuditStore((s) => s.toggleUrlSelection);
  const selectAllUrls = useAuditStore((s) => s.selectAllUrls);
  const deselectAllUrls = useAuditStore((s) => s.deselectAllUrls);
  const extractionProgress = useAuditStore((s) => s.extractionProgress);
  const setExtractionProgress = useAuditStore((s) => s.setExtractionProgress);
  const setExtractedPages = useAuditStore((s) => s.setExtractedPages);
  const setRagStats = useAuditStore((s) => s.setRagStats);

  const [loading, setLoading] = useState(false);
  const [loadingPhase, setLoadingPhase] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [charCount, setCharCount] = useState<number | null>(null);
  const [pageCount, setPageCount] = useState<number | null>(null);
  const [contentWarning, setContentWarning] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const isCompleted = currentStep >= 2;

  const validateUrl = useCallback((): boolean => {
    const trimmed = url.trim();
    if (!trimmed) { setError("Informe a URL do site"); return false; }
    if (trimmed.length > MAX_URL_LENGTH) { setError(`URL excede o tamanho maximo`); return false; }
    if (!isValidUrl(trimmed)) { setError("URL com formato invalido. Ex: https://exemplo.com.br"); return false; }
    return true;
  }, [url]);

  // ── Modo Single ──
  const handleExtractSingle = useCallback(async () => {
    if (!validateUrl()) return;
    setLoading(true); setError(null); setContentWarning(null);
    setLoadingPhase("Extraindo conteudo...");
    try {
      const response = await extractContent(url.trim());
      setContent(response.content, response.title);
      setCharCount(response.content.length);
      setPageCount(1);
      if (response.content.length < MIN_CONTENT_LENGTH) {
        setContentWarning(`Conteudo extraido muito curto (${response.content.length} chars).`);
      }
      setCurrentStep(2);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erro ao extrair conteudo";
      setError(msg);
      toast.error(msg, { duration: 4000 });
    } finally { setLoading(false); setLoadingPhase(""); }
  }, [url, validateUrl, setContent, setCurrentStep]);

  // ── Descobrir Sitemap ──
  const handleDiscoverSitemap = useCallback(async () => {
    if (!validateUrl()) return;
    setLoading(true); setError(null);
    setLoadingPhase("Descobrindo paginas do site...");
    try {
      const result = await discoverSitemap(url.trim(), 50);
      if (result.urls.length === 0) {
        setError("Nenhuma pagina encontrada. Use o modo pagina unica.");
        return;
      }
      setDiscoveredUrls(result.urls);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erro ao descobrir paginas";
      setError(msg);
      toast.error(msg, { duration: 4000 });
    } finally { setLoading(false); setLoadingPhase(""); }
  }, [url, validateUrl, setDiscoveredUrls]);

  // ── Extrair Selecionadas via SSE ──
  const handleExtractSelected = useCallback(() => {
    if (selectedUrls.length === 0) { setError("Selecione pelo menos uma pagina."); return; }

    setLoading(true); setError(null); setContentWarning(null);
    setLoadingPhase("Extraindo paginas...");
    setExtractionProgress({ current: 0, total: selectedUrls.length, currentUrl: "" });

    const controller = connectMultiExtract(selectedUrls, {
      onExtracting: (data) => {
        setExtractionProgress({ current: data.current, total: data.total, currentUrl: data.url });
        setLoadingPhase(`Extraindo pagina ${data.current} de ${data.total}...`);
      },
      onExtracted: (data) => {
        setExtractionProgress({ current: data.current, total: data.total, currentUrl: data.url });
      },
      onFailed: (data) => {
        setExtractionProgress({ current: data.current, total: data.total, currentUrl: data.url });
      },
      onDone: async (data) => {
        setExtractionProgress(null);

        if (data.pages.length === 0) {
          setError("Nenhuma pagina extraida com sucesso.");
          setLoading(false);
          return;
        }

        const pages = data.pages as ExtractResponse[];
        setExtractedPages(pages);

        // Agrega contexto
        const allContent = pages
          .map((p) => `--- ${p.url} (${p.title || "sem titulo"}) ---\n${p.content}`)
          .join("\n\n");
        const totalChars = pages.reduce((sum, p) => sum + (p.char_count || p.content.length), 0);

        setContent(allContent, `${data.total_extracted} paginas`);
        setCharCount(totalChars);
        setPageCount(data.total_extracted);

        if (data.total_extracted < data.total_requested) {
          setContentWarning(`${data.total_requested - data.total_extracted} paginas falharam na extracao.`);
        }

        // Indexar RAG
        setLoadingPhase("Indexando conteudo para RAG (chunking + embeddings)...");
        try {
          const ragResult = await indexRAG(pages);
          setRagStats(ragResult);
        } catch (ragErr) {
          setContentWarning(`RAG nao indexado (${ragErr instanceof Error ? ragErr.message : "erro"}). Avaliacao usara texto agregado.`);
        }

        setCurrentStep(2);
        setLoading(false);
        setLoadingPhase("");
      },
      onError: (err) => {
        setExtractionProgress(null);
        setError(err);
        toast.error(err, { duration: 4000 });
        setLoading(false);
        setLoadingPhase("");
      },
    });

    abortRef.current = controller;
  }, [selectedUrls, setContent, setCurrentStep, setExtractedPages, setRagStats, setExtractionProgress]);

  const progressPercent = extractionProgress
    ? Math.round((extractionProgress.current / extractionProgress.total) * 100)
    : 0;

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
              if (extractionMode === "single") handleExtractSingle();
            }
          }}
          disabled={loading || isCompleted}
          error={error || undefined}
        />

        {/* Seletor de modo */}
        {!isCompleted && !loading && discoveredUrls.length === 0 && (
          <fieldset className="flex items-center gap-4">
            <legend className="sr-only">Modo de extracao</legend>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="radio" name="mode" checked={extractionMode === "single"}
                onChange={() => setExtractionMode("single")} className="accent-kipiai-blue" />
              Pagina unica
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="radio" name="mode" checked={extractionMode === "multi"}
                onChange={() => setExtractionMode("multi")} className="accent-kipiai-blue" />
              Site completo (sitemap)
            </label>
          </fieldset>
        )}

        {/* Botões de ação */}
        {!isCompleted && discoveredUrls.length === 0 && !extractionProgress && (
          <div className="flex gap-3">
            {extractionMode === "single" ? (
              <Button onClick={handleExtractSingle} loading={loading} disabled={!url.trim()}>
                {loading ? loadingPhase : "Extrair Contexto"}
              </Button>
            ) : (
              <Button onClick={handleDiscoverSitemap} loading={loading} disabled={!url.trim()}>
                {loading ? loadingPhase : "Descobrir Paginas"}
              </Button>
            )}
          </div>
        )}

        {/* Barra de progresso de extração multi-página */}
        {extractionProgress && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-kipiai-gray">
                Extraindo pagina {extractionProgress.current} de {extractionProgress.total}...
              </span>
              <span className="font-medium text-kipiai-dark">
                {extractionProgress.current}/{extractionProgress.total}
              </span>
            </div>
            <ProgressBar value={progressPercent} height="md" showLabel />
            {extractionProgress.currentUrl && (
              <p className="text-xs text-kipiai-gray truncate" title={extractionProgress.currentUrl}>
                {extractionProgress.currentUrl}
              </p>
            )}
          </div>
        )}

        {/* Loading para fases não-SSE (RAG indexing) */}
        {loading && !extractionProgress && loadingPhase && (
          <div className="flex items-center gap-2 text-sm text-kipiai-blue">
            <svg aria-hidden="true" className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {loadingPhase}
          </div>
        )}

        {/* Tabela de URLs descobertas */}
        {discoveredUrls.length > 0 && !isCompleted && !extractionProgress && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-kipiai-dark">
                {discoveredUrls.length} paginas descobertas
              </h3>
              <div className="flex gap-2">
                <button className="text-xs text-kipiai-blue hover:underline" onClick={selectAllUrls}>
                  Selecionar todas
                </button>
                <button className="text-xs text-kipiai-gray hover:underline" onClick={deselectAllUrls}>
                  Desmarcar todas
                </button>
              </div>
            </div>

            <div className="max-h-64 overflow-y-auto border border-gray-200 rounded-lg">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="w-10 px-3 py-2" />
                    <th className="text-left px-3 py-2 text-kipiai-gray font-medium">URL</th>
                    <th className="text-left px-3 py-2 text-kipiai-gray font-medium w-24">Fonte</th>
                  </tr>
                </thead>
                <tbody>
                  {discoveredUrls.map((u) => (
                    <tr key={u.url} className="border-t border-gray-100 hover:bg-gray-50">
                      <td className="px-3 py-1.5 text-center">
                        <input type="checkbox" checked={selectedUrls.includes(u.url)}
                          onChange={() => toggleUrlSelection(u.url)} className="accent-kipiai-blue"
                          aria-label={`Selecionar ${u.url}`} />
                      </td>
                      <td className="px-3 py-1.5 text-kipiai-dark truncate max-w-md" title={u.url}>{u.url}</td>
                      <td className="px-3 py-1.5 text-kipiai-gray text-xs">{u.source}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex items-center gap-4">
              <Button onClick={handleExtractSelected} loading={loading} disabled={selectedUrls.length === 0}>
                {loading && !extractionProgress ? loadingPhase : `Extrair ${selectedUrls.length} paginas`}
              </Button>
              <span className="text-sm text-kipiai-gray">
                {selectedUrls.length} de {discoveredUrls.length} selecionadas
              </span>
            </div>
          </div>
        )}

        {/* Info de extração concluída */}
        {charCount !== null && (
          <div className="flex items-center gap-2 text-sm">
            <span className="w-2 h-2 rounded-full bg-kipiai-green" aria-hidden="true" />
            <span className="text-kipiai-gray">
              Conteudo extraido: {charCount.toLocaleString("pt-BR")} caracteres
              {pageCount && pageCount > 1 && ` (${pageCount} paginas)`}
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
