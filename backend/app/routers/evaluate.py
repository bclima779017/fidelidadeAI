"""Router para avaliação de fidelidade via SSE — avaliação concorrente."""

import asyncio
import json
import logging
import threading
from dataclasses import asdict
from typing import AsyncGenerator

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas import EvaluateRequest, EvaluateResult
import ai_handler
import config
import security
from health import EvalHealth
from scoring import PESOS

logger = logging.getLogger("kipiai.evaluate")

router = APIRouter(prefix="/api", tags=["evaluate"])
limiter = Limiter(key_func=get_remote_address)

# RAG instance global (thread-safe)
_rag_lock = threading.Lock()
_current_rag = None


def set_rag_instance(rag):
    global _current_rag
    with _rag_lock:
        _current_rag = rag


def get_rag_instance():
    with _rag_lock:
        return _current_rag


def resolve_api_key(request_key: str | None, auth_header: str | None) -> str:
    """Resolve API key: header Authorization > body > env var. Compartilhado entre routers."""
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            return token
    if request_key:
        return request_key
    return config.GEMINI_API_KEY


def _compute_weighted_score(results_data: list[dict]) -> float:
    valid = [(r["question"], r["score"]) for r in results_data if r.get("score", -1) >= 0]
    if not valid:
        return 0.0
    total_weight = 0.0
    weighted_sum = 0.0
    for pergunta, score in valid:
        peso = 0.20
        for p_text, p_peso in PESOS.items():
            if p_text in pergunta or pergunta in p_text:
                peso = p_peso
                break
        weighted_sum += peso * score
        total_weight += peso
    return round(weighted_sum / total_weight, 1) if total_weight > 0 else 0.0


def _serialize_health(health: EvalHealth) -> dict:
    data = asdict(health)
    data["pct_lost"] = health.pct_lost
    data["has_warnings"] = health.has_warnings
    return data


async def _evaluate_stream(
    request: EvaluateRequest, api_key: str
) -> AsyncGenerator[str, None]:
    """Avalia perguntas concorrentemente e emite SSE em ordem de conclusão."""
    total = len(request.questions)
    context = request.context
    health = EvalHealth()
    results_data: list[dict] = []
    completed = 0

    rag = get_rag_instance()
    rag_active = rag is not None and hasattr(rag, "is_ready") and rag.is_ready

    # Semáforo para limitar chamadas Gemini simultâneas
    sem = asyncio.Semaphore(config.MAX_CONCURRENT_GEMINI)
    queue: asyncio.Queue = asyncio.Queue()

    async def _evaluate_one(i: int, q):
        """Avalia uma pergunta e coloca o resultado na queue (com timeout)."""
        question_text = security.sanitize_user_input(q.question)
        official_answer = security.sanitize_user_input(q.official_answer)

        async with sem:
            try:
                result = await asyncio.wait_for(
                    ai_handler.evaluate_question_async(
                        context, question_text, official_answer, api_key,
                        rag=rag if rag_active else None,
                        health=health,
                    ),
                    timeout=config.EVAL_TIMEOUT,
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
                await queue.put(("result", i, eval_result))
            except asyncio.TimeoutError:
                logger.error("Timeout na pergunta %d após %ds", i + 1, config.EVAL_TIMEOUT)
                await queue.put(("error", i, f"Timeout: pergunta {i + 1} excedeu {config.EVAL_TIMEOUT}s"))
            except Exception as e:
                safe_msg = security.safe_error_message(e)
                logger.error("Erro na pergunta %d: %s", i + 1, e)
                await queue.put(("error", i, safe_msg))

    # Emite evento de início
    start_event = {"type": "progress", "current": 0, "total": total, "question": "Iniciando avaliação concorrente..."}
    yield f"data: {json.dumps(start_event, ensure_ascii=False)}\n\n"

    # Lança todas as perguntas em paralelo
    tasks = [asyncio.create_task(_evaluate_one(i, q)) for i, q in enumerate(request.questions)]

    # Sentinel: quando todas terminarem, sinaliza na queue
    async def _sentinel():
        await asyncio.gather(*tasks)
        await queue.put(None)

    asyncio.create_task(_sentinel())

    # Consome resultados conforme completam
    while True:
        item = await queue.get()
        if item is None:
            break

        completed += 1
        event_type, index, data = item

        # Progresso
        progress_event = {"type": "progress", "current": completed, "total": total, "question": f"Pergunta {index + 1} concluída"}
        yield f"data: {json.dumps(progress_event, ensure_ascii=False)}\n\n"

        if event_type == "result":
            result_event = {"type": "result", "index": index, "data": data.model_dump()}
            yield f"data: {json.dumps(result_event, ensure_ascii=False)}\n\n"
            results_data.append({"question": data.question, "score": data.score})
        else:
            error_event = {"type": "error", "message": f"Erro na pergunta {index + 1}: {data}"}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
            results_data.append({"question": f"Pergunta {index + 1}", "score": -1})

    # Evento done
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
    """Avalia perguntas via SSE concorrente."""
    api_key = resolve_api_key(body.api_key, authorization)

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key não configurada. Informe via header Authorization ou variável de ambiente GEMINI_API_KEY.",
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
