"""Pydantic models para validação de request/response da API."""

from pydantic import BaseModel, Field, field_validator


# ── Extract ──

class ExtractRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048, description="URL do site para extrair conteúdo")

    @field_validator("url")
    @classmethod
    def normalize_url(cls, v: str) -> str:
        """Normaliza URL (strip + prefixo https). Validação robusta via security.validate_url() nos routers."""
        v = v.strip()
        if not v:
            raise ValueError("URL não informada.")
        if not v.startswith(("http://", "https://")):
            v = "https://" + v
        return v


class ExtractResponse(BaseModel):
    url: str
    title: str
    content: str
    char_count: int


# ── Evaluate ──

class QuestionInput(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="Pergunta estratégica")
    official_answer: str = Field(..., min_length=1, max_length=10_000, description="Resposta oficial esperada (ground truth)")


class EvaluateRequest(BaseModel):
    context: str = Field(..., min_length=1, max_length=1_000_000, description="Conteúdo extraído do site (contexto)")
    questions: list[QuestionInput] = Field(..., min_length=1, max_length=10, description="Lista de perguntas com respostas oficiais")
    api_key: str | None = Field(None, description="Chave da API Gemini (opcional — usa env var se ausente)")

    @field_validator("api_key")
    @classmethod
    def sanitize_api_key(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class EvaluateResult(BaseModel):
    question: str
    official_answer: str
    resposta_ia: str = ""
    score: float = -1
    score_gemini_original: float | None = None
    match_semantico: float | None = None
    taxa_claims: float | None = None
    claims_preservados: list[str] = []
    claims_omitidos: list[str] = []
    hallucinations: list[str] = []
    justificativa: str = ""
    fontes: list[str] = []
    context_truncated: bool = False


# ── Sitemap ──

class SitemapRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048, description="URL base do site")
    max_pages: int = Field(50, ge=1, le=200, description="Máximo de páginas a descobrir")

    @field_validator("url")
    @classmethod
    def normalize_url(cls, v: str) -> str:
        """Normaliza URL (strip + prefixo https). Validação robusta via security.validate_url() nos routers."""
        v = v.strip()
        if not v:
            raise ValueError("URL não informada.")
        if not v.startswith(("http://", "https://")):
            v = "https://" + v
        return v


class UrlInfo(BaseModel):
    url: str
    lastmod: str = ""
    source: str = ""


class SitemapResponse(BaseModel):
    urls: list[UrlInfo]
    total: int


# ── Multi Extract ──

class MultiExtractRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=200, description="URLs para extrair")


class MultiExtractResponse(BaseModel):
    pages: list[ExtractResponse]
    total_extracted: int
    total_requested: int


# ── RAG ──

class RAGIndexRequest(BaseModel):
    pages: list[ExtractResponse] = Field(..., min_length=1, description="Páginas para indexar")
    api_key: str | None = Field(None, description="Chave da API Gemini")


class RAGIndexResponse(BaseModel):
    total_chunks: int
    total_pages: int
    chunks_per_page: dict[str, int]


class RAGStatsResponse(BaseModel):
    total_chunks: int
    total_pages: int
    chunks_per_page: dict[str, int]
    is_ready: bool


# ── Health ──

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    knowledge_base_loaded: bool = False
    rag_indexed: bool = False


# ── SSE Events ──

class SSEProgressEvent(BaseModel):
    type: str = "progress"
    current: int
    total: int
    question: str


class SSEResultEvent(BaseModel):
    type: str = "result"
    index: int
    data: EvaluateResult


class SSEDoneEvent(BaseModel):
    type: str = "done"
    total: int


class SSEErrorEvent(BaseModel):
    type: str = "error"
    message: str
