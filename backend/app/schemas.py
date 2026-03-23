"""Pydantic models para validação de request/response da API."""

from pydantic import BaseModel, Field


# ── Extract ──

class ExtractRequest(BaseModel):
    url: str = Field(..., description="URL do site para extrair conteúdo")


class ExtractResponse(BaseModel):
    url: str
    title: str
    content: str
    char_count: int


# ── Evaluate ──

class QuestionInput(BaseModel):
    question: str = Field(..., description="Pergunta estratégica")
    official_answer: str = Field(..., description="Resposta oficial esperada (ground truth)")


class EvaluateRequest(BaseModel):
    context: str = Field(..., description="Conteúdo extraído do site (contexto)")
    questions: list[QuestionInput] = Field(..., description="Lista de perguntas com respostas oficiais")
    api_key: str = Field(..., description="Chave da API Gemini")


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
