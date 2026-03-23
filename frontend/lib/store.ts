import { create } from "zustand";
import { EvaluateResult, EvalHealth } from "./types";

interface AuditState {
  // Input
  url: string;
  extractedContent: string;

  // Flow
  currentStep: number;

  // Expert answers (q1-q5)
  expertAnswers: Record<string, string>;

  // Evaluation
  evaluationStatus: "idle" | "running" | "done" | "error";
  evaluationProgress: { current: number; total: number };

  // Results
  results: EvaluateResult[];
  weightedScore: number | null;
  health: EvalHealth | null;

  // Actions
  setUrl: (url: string) => void;
  setContent: (content: string) => void;
  setCurrentStep: (step: number) => void;
  setAnswer: (key: string, value: string) => void;
  setEvaluationStatus: (status: AuditState["evaluationStatus"]) => void;
  setEvaluationProgress: (current: number, total: number) => void;
  addResult: (result: EvaluateResult) => void;
  setWeightedScore: (score: number) => void;
  setHealth: (health: EvalHealth) => void;
  reset: () => void;
}

const initialState = {
  url: "",
  extractedContent: "",
  currentStep: 1,
  expertAnswers: {} as Record<string, string>,
  evaluationStatus: "idle" as const,
  evaluationProgress: { current: 0, total: 0 },
  results: [] as EvaluateResult[],
  weightedScore: null as number | null,
  health: null as EvalHealth | null,
};

export const useAuditStore = create<AuditState>((set) => ({
  ...initialState,

  setUrl: (url) => set({ url }),

  setContent: (content) => set({ extractedContent: content }),

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

  reset: () => set(initialState),
}));
