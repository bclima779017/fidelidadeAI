import { create } from "zustand";
import { EvaluateResult, EvalHealth } from "./types";

interface AuditState {
  // Input
  url: string;
  extractedContent: string;
  extractedTitle: string;

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

  // Actions
  setUrl: (url: string) => void;
  setContent: (content: string, title?: string) => void;
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
  currentStep: 1,
  expertAnswers: {} as Record<string, string>,
  evaluationStatus: "idle" as const,
  evaluationProgress: { current: 0, total: 0 },
  errorMessage: null as string | null,
  results: [] as EvaluateResult[],
  weightedScore: null as number | null,
  health: null as EvalHealth | null,
};

export const useAuditStore = create<AuditState>((set) => ({
  ...initialState,

  setUrl: (url) => set({ url }),

  setContent: (content, title) =>
    set({ extractedContent: content, extractedTitle: title || "" }),

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

  // Reset parcial: limpa resultados mas mantém URL e respostas do especialista
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
