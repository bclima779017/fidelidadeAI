export interface ExtractResponse {
  content: string;
  url: string;
  title?: string;
  char_count?: number;
}

export interface UrlInfo {
  url: string;
  lastmod: string;
  source: string;
}

export interface SitemapResponse {
  urls: UrlInfo[];
  total: number;
}

export interface MultiExtractResponse {
  pages: ExtractResponse[];
  total_extracted: number;
  total_requested: number;
}

export interface RAGIndexResponse {
  total_chunks: number;
  total_pages: number;
  chunks_per_page: Record<string, number>;
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
  // Campos normalizados para o frontend
  ai_answer?: string;
  expert_answer?: string;
  semantic_match?: number | null;
  claims_rate?: number | null;
}

/** Alinhado com EvalHealth do backend (health.py) */
export interface EvalHealth {
  context_truncated: boolean;
  context_original_chars: number;
  context_used_chars: number;
  pct_lost: number;
  json_parse_failures: number;
  json_parse_details: string[];
  total_retries: number;
  retry_details: { question: string; attempt: number; reason: string; wait_s: number }[];
  poor_extraction_pages: { url: string; char_count: number }[];
  thin_chunks: { url: string; text_preview: string; char_count: number }[];
  has_warnings: boolean;
}

export interface EvaluationSSEData {
  type: "progress" | "result" | "done" | "error";
  current?: number;
  total?: number;
  data?: EvaluateResult;
  weighted_score?: number;
  health?: EvalHealth;
  message?: string;
}
