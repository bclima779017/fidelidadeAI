export interface ExtractResponse {
  content: string;
  url: string;
  title?: string;
  char_count?: number;
  pages_found?: number;
}

export interface QuestionInput {
  question: string;
  expert_answer: string;
  weight?: number;
}

export interface ClaimAnalysis {
  text: string;
  preserved: boolean;
}

export interface EvaluateResult {
  question: string;
  official_answer: string;
  resposta_ia: string;
  score: number;
  score_gemini_original?: number | null;
  match_semantico?: number | null;
  taxa_claims?: number | null;
  claims_preservados?: string[];
  claims_omitidos?: string[];
  hallucinations?: string[];
  justificativa?: string;
  fontes?: string[];
  context_truncated?: boolean;
  // Campos de compatibilidade com o frontend
  question_index?: number;
  expert_answer?: string;
  ai_answer?: string;
  semantic_match?: number | null;
  claims_rate?: number | null;
  claims?: ClaimAnalysis[];
}

export interface EvalHealth {
  score_spread: number;
  has_low_scores: boolean;
  avg_justification_length: number;
  claims_coverage: number;
  overall_quality: "good" | "warning" | "poor";
}

export interface SuggestionItem {
  rank: number;
  category: string;
  suggestion: string;
  priority: "alta" | "media" | "baixa";
  related_question?: number;
}

export interface EvaluationSSEData {
  type: "progress" | "result" | "done" | "error";
  current?: number;
  total?: number;
  result?: EvaluateResult;
  data?: EvaluateResult;
  weighted_score?: number;
  health?: EvalHealth;
  message?: string;
}
