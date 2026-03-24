"""Pydantic models para validação de request/response da API."""

from pydantic import BaseModel, Field, field_validator
import re


# ── Extract ──

class ExtractRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048, description="URL do site para extrair conteúdo")

    @field_validator("url")
    @classmethod
    def validate_url_format(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("URL não informada.")
        if not re.match(r"^https?://", v, re.IGNORECASE):
            v = "https://" + v
        if not re.match(r"^https?://[a-zA-Z0-9]", v, re.IGNORECASE):
            raise ValueError("URL com formato inválido.")
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


# ── Health ──

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    knowledge_base_loaded: bool = False


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
