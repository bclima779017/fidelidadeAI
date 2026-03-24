"""Router para avaliação de fidelidade via SSE (Server-Sent Events)."""

import json
import asyncio
import logging
from dataclasses import asdict
from typing import AsyncGenerator

from fastapi import APIRouter, Header, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas import EvaluateRequest, EvaluateResult
import ai_handler
import config
import security
from health import EvalHealth
from scoring import PESOS, PERGUNTAS

logger = logging.getLogger("kipiai.evaluate")

router = APIRouter(prefix="/api", tags=["evaluate"])

limiter = Limiter(key_func=get_remote_address)

# RAG instance global (gerenciada pelo router de RAG)
_current_rag = None


def set_rag_instance(rag):
    """Chamado pelo router de RAG para setar a instância ativa."""
    global _current_rag
    _current_rag = rag


def get_rag_instance():
    """Retorna a instância RAG ativa (ou None)."""
    return _current_rag


def _resolve_api_key(request_key: str | None, auth_header: str | None) -> str:
    """Resolve a API key por prioridade: header > body > env var."""
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            return token
    if request_key:
        return request_key
    return config.GEMINI_API_KEY


def _compute_weighted_score(results_data: list[dict]) -> float:
    """Calcula score ponderado usando os pesos de scoring.py."""
    valid = [(r["question"], r["score"]) for r in results_data if r.get("score", -1) >= 0]
    if not valid:
        return 0.0

    total_weight = 0.0
    weighted_sum = 0.0
    for pergunta, score in valid:
        # Encontra peso correspondente
        peso = 0.20  # default
        for p_text, p_peso in PESOS.items():
            if p_text in pergunta or pergunta in p_text:
                peso = p_peso
                break
        weighted_sum += peso * score
        total_weight += peso

    return round(weighted_sum / total_weight, 1) if total_weight > 0 else 0.0


def _serialize_health(health: EvalHealth) -> dict:
    """Serializa EvalHealth para JSON, incluindo propriedades computadas."""
    data = asdict(health)
    data["pct_lost"] = health.pct_lost
    data["has_warnings"] = health.has_warnings
    return data


async def _evaluate_stream(
    request: EvaluateRequest, api_key: str
) -> AsyncGenerator[str, None]:
    """Gera eventos SSE para cada pergunta avaliada sequencialmente."""
    total = len(request.questions)
    context = request.context
    health = EvalHealth()
    results_data: list[dict] = []

    rag = get_rag_instance()
    rag_active = rag is not None and hasattr(rag, "is_ready") and rag.is_ready

    for i, q in enumerate(request.questions):
        question_text = security.sanitize_user_input(q.question)
        official_answer = security.sanitize_user_input(q.official_answer)

        # Emite evento de progresso
        progress_event = {
            "type": "progress",
            "current": i + 1,
            "total": total,
            "question": question_text[:80],
        }
        yield f"data: {json.dumps(progress_event, ensure_ascii=False)}\n\n"

        try:
            result = await asyncio.to_thread(
                ai_handler.evaluate_question,
                context,
                question_text,
                official_answer,
                api_key,
                rag=rag if rag_active else None,
                health=health,
            )

            eval_result = EvaluateResult(
                question=question_text,
                official_answer=official_answer,
                resposta_ia=result.get("resposta_ia", ""),
                score=result.get("score", -1),
                score_gemini_original=result.get("score_gemini_original"),
                match_semantico=result.get("match_semantico"),
                taxa_claims=result.get("taxa_claims"),
                claims_preservados=result.get("claims_preservados", []),
                claims_omitidos=result.get("claims_omitidos", []),
                hallucinations=result.get("hallucinations", []),
                justificativa=result.get("justificativa", ""),
                fontes=result.get("fontes", []),
                context_truncated=result.get("context_truncated", False),
            )

            result_event = {
                "type": "result",
                "index": i,
                "data": eval_result.model_dump(),
            }
            yield f"data: {json.dumps(result_event, ensure_ascii=False)}\n\n"

            results_data.append({
                "question": question_text,
                "score": eval_result.score,
            })

        except Exception as e:
            safe_msg = security.safe_error_message(e)
            logger.error("Erro na avaliação da pergunta %d: %s", i + 1, e)
            error_event = {
                "type": "error",
                "message": f"Erro na pergunta {i + 1}: {safe_msg}",
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

            results_data.append({
                "question": question_text,
                "score": -1,
            })

    # Evento final com score ponderado e health
    weighted_score = _compute_weighted_score(results_data)
    done_event = {
        "type": "done",
        "total": total,
        "weighted_score": weighted_score,
        "health": _serialize_health(health),
    }
    yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"


@router.post("/evaluate")
@limiter.limit("30/minute")
async def evaluate_questions(
    request: Request,
    body: EvaluateRequest,
    authorization: str | None = Header(None),
) -> StreamingResponse:
    """Avalia perguntas via SSE — emite progresso, resultados e evento done."""
    api_key = _resolve_api_key(body.api_key, authorization)

    if not api_key:
        error_event = json.dumps({
            "type": "error",
            "message": "API key não configurada. Informe via header Authorization ou variável de ambiente GEMINI_API_KEY.",
        }, ensure_ascii=False)
        return StreamingResponse(
            iter([f"data: {error_event}\n\n"]),
            media_type="text/event-stream",
            status_code=401,
        )

    return StreamingResponse(
        _evaluate_stream(body, api_key),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
