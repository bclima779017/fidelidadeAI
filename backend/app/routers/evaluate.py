"""Router para avaliação de fidelidade via SSE (Server-Sent Events)."""

import json
import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas import EvaluateRequest, EvaluateResult
import ai_handler
import security

router = APIRouter(prefix="/api", tags=["evaluate"])


async def _evaluate_stream(request: EvaluateRequest) -> AsyncGenerator[str, None]:
    """Gera eventos SSE para cada pergunta avaliada sequencialmente."""
    total = len(request.questions)
    api_key = request.api_key
    context = request.context

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
            # Executa a avaliação em thread separada para não bloquear o event loop
            result = await asyncio.to_thread(
                ai_handler.evaluate_question,
                context,
                question_text,
                official_answer,
                api_key,
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
            )

            result_event = {
                "type": "result",
                "index": i,
                "data": eval_result.model_dump(),
            }
            yield f"data: {json.dumps(result_event, ensure_ascii=False)}\n\n"

        except Exception as e:
            safe_msg = security.safe_error_message(e)
            error_event = {
                "type": "error",
                "message": f"Erro na pergunta {i + 1}: {safe_msg}",
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    # Evento final
    done_event = {"type": "done", "total": total}
    yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"


@router.post("/evaluate")
async def evaluate_questions(request: EvaluateRequest):
    """Avalia perguntas via SSE — emite progresso, resultados e evento done."""
    return StreamingResponse(
        _evaluate_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
