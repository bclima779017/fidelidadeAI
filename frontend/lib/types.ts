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
  question_index: number;
  question: string;
  expert_answer: string;
  ai_answer: string;
  score: number;
  semantic_match?: number;
  claims_rate?: number;
  justificativa?: string;
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
  weighted_score?: number;
  health?: EvalHealth;
  message?: string;
}
