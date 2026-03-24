import { create } from "zustand";
import { EvaluateResult, EvalHealth, UrlInfo, ExtractResponse, RAGIndexResponse } from "./types";

interface AuditState {
  // Input
  url: string;
  extractedContent: string;
  extractedTitle: string;
  extractionMode: "single" | "multi";

  // Sitemap
  discoveredUrls: UrlInfo[];
  selectedUrls: string[];
  extractedPages: ExtractResponse[];

  // Extraction progress
  extractionProgress: { current: number; total: number; currentUrl: string } | null;

  // RAG
  ragStats: RAGIndexResponse | null;

  // Flow
  currentStep: number;

  // Expert answers (q1-q5)
  expertAnswers: Record<string, string>;

  // Evaluation
  evaluationStatus: "idle" | "running" | "done" | "error";
  evaluationProgress: { current: number; total: number };
  errorMessage: string | null;

  // Results
  results: EvaluateResult[];
  weightedScore: number | null;
  health: EvalHealth | null;

  // Actions — Input
  setUrl: (url: string) => void;
  setContent: (content: string, title?: string) => void;
  setExtractionMode: (mode: "single" | "multi") => void;

  // Actions — Sitemap
  setDiscoveredUrls: (urls: UrlInfo[]) => void;
  toggleUrlSelection: (url: string) => void;
  selectAllUrls: () => void;
  deselectAllUrls: () => void;
  setExtractedPages: (pages: ExtractResponse[]) => void;

  // Actions — Extraction progress
  setExtractionProgress: (progress: { current: number; total: number; currentUrl: string } | null) => void;

  // Actions — RAG
  setRagStats: (stats: RAGIndexResponse | null) => void;

  // Actions — Flow
  setCurrentStep: (step: number) => void;
  setAnswer: (key: string, value: string) => void;
  setEvaluationStatus: (status: AuditState["evaluationStatus"]) => void;
  setEvaluationProgress: (current: number, total: number) => void;
  setErrorMessage: (message: string | null) => void;
  addResult: (result: EvaluateResult) => void;
  setWeightedScore: (score: number) => void;
  setHealth: (health: EvalHealth) => void;
  resetEvaluation: () => void;
  reset: () => void;
}

const initialState = {
  url: "",
  extractedContent: "",
  extractedTitle: "",
  extractionMode: "single" as const,
  discoveredUrls: [] as UrlInfo[],
  selectedUrls: [] as string[],
  extractedPages: [] as ExtractResponse[],
  extractionProgress: null as { current: number; total: number; currentUrl: string } | null,
  ragStats: null as RAGIndexResponse | null,
  currentStep: 1,
  expertAnswers: {} as Record<string, string>,
  evaluationStatus: "idle" as const,
  evaluationProgress: { current: 0, total: 0 },
  errorMessage: null as string | null,
  results: [] as EvaluateResult[],
  weightedScore: null as number | null,
  health: null as EvalHealth | null,
};

export const useAuditStore = create<AuditState>((set, get) => ({
  ...initialState,

  setUrl: (url) => set({ url }),

  setContent: (content, title) =>
    set({ extractedContent: content, extractedTitle: title || "" }),

  setExtractionMode: (mode) => set({ extractionMode: mode }),

  // Sitemap
  setDiscoveredUrls: (urls) =>
    set({ discoveredUrls: urls, selectedUrls: urls.map((u) => u.url) }),

  toggleUrlSelection: (url) =>
    set((state) => {
      const isSelected = state.selectedUrls.includes(url);
      return {
        selectedUrls: isSelected
          ? state.selectedUrls.filter((u) => u !== url)
          : [...state.selectedUrls, url],
      };
    }),

  selectAllUrls: () =>
    set((state) => ({
      selectedUrls: state.discoveredUrls.map((u) => u.url),
    })),

  deselectAllUrls: () => set({ selectedUrls: [] }),

  setExtractedPages: (pages) => set({ extractedPages: pages }),

  // Extraction progress
  setExtractionProgress: (progress) => set({ extractionProgress: progress }),

  // RAG
  setRagStats: (stats) => set({ ragStats: stats }),

  // Flow
  setCurrentStep: (step) =>
    set((state) => ({
      currentStep: Math.max(state.currentStep, step),
    })),

  setAnswer: (key, value) =>
    set((state) => ({
      expertAnswers: { ...state.expertAnswers, [key]: value },
    })),

  setEvaluationStatus: (status) => set({ evaluationStatus: status }),

  setEvaluationProgress: (current, total) =>
    set({ evaluationProgress: { current, total } }),

  setErrorMessage: (message) => set({ errorMessage: message }),

  addResult: (result) =>
    set((state) => ({
      results: [...state.results, result],
      evaluationProgress: {
        ...state.evaluationProgress,
        current: state.results.length + 1,
      },
    })),

  setWeightedScore: (score) => set({ weightedScore: score }),

  setHealth: (health) => set({ health }),

  resetEvaluation: () =>
    set({
      evaluationStatus: "idle",
      evaluationProgress: { current: 0, total: 0 },
      errorMessage: null,
      results: [],
      weightedScore: null,
      health: null,
      currentStep: 2,
    }),

  reset: () => set(initialState),
}));
