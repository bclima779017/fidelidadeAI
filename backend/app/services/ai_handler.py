"""Prompt de auditoria GEO e chamada ao Gemini para avaliação de fidelidade.

Usa google-genai SDK com async nativo para performance.
"""

import asyncio
import logging

import numpy as np
from google import genai
from google.genai import types

import config
from scoring import calcular_score_pergunta
from utils import cosine_similarity, embed_texts_async, get_genai_client, parse_json_response

logger = logging.getLogger("kipiai.ai_handler")

_SYSTEM_INSTRUCTION = (
    "Você é um auditor RIGOROSO especializado em GEO (Generative Engine Optimization) e "
    "fidelidade de RAG. Sua função é avaliar com alto nível de exigência se uma resposta "
    "gerada por IA preserva com precisão as informações da fonte original da marca.\n\n"
    "REGRAS DE RIGOR:\n"
    "- Na dúvida entre dois scores, SEMPRE escolha o menor.\n"
    "- Claims generalizados ou reformulados com perda de especificidade DEVEM ser penalizados.\n"
    "- Dados quantitativos (números, percentuais, valores) omitidos ou alterados: penalidade mínima de 15 pontos.\n"
    "- Informações inventadas (hallucination) não presentes no contexto: score máximo de 40.\n"
    "- Omissão de claims centrais da marca: score máximo de 60.\n"
    "- Score acima de 90 é EXCEPCIONAL e exige preservação literal de todos os claims.\n\n"
    "Princípios do Manifesto GEO da Kípiai que você deve aplicar:\n"
    "1. COMPREENSIBILIDADE: A resposta deve ser clara e acessível, sem distorcer o conteúdo original.\n"
    "2. CITAÇÃO DE AUTORIDADE: Claims técnicos, certificações, prêmios e dados quantitativos "
    "devem ser preservados fielmente.\n"
    "3. PRESERVAÇÃO DE CLAIMS: Nenhuma afirmação da marca deve ser omitida, inventada ou alterada."
)


async def _compute_semantic_similarity_async(api_key: str, text_a: str, text_b: str) -> float:
    """Calcula similaridade semântica via embeddings Gemini (async)."""
    if not text_a.strip() or not text_b.strip():
        return 0.0

    embeddings = await embed_texts_async(api_key, [text_a, text_b])
    emb_a = np.array(embeddings[0], dtype=np.float32)
    emb_b = np.array(embeddings[1], dtype=np.float32)

    similarity = cosine_similarity(emb_a, emb_b)
    return max(0.0, min(similarity, 1.0)) * 100


def _compute_claims_rate(claims_preservados: list, claims_omitidos: list) -> float:
    """Calcula a taxa de atingimento de claims (0-100)."""
    total = len(claims_preservados) + len(claims_omitidos)
    if total == 0:
        return 0.0
    return (len(claims_preservados) / total) * 100


def build_prompt(context: str, question: str, official_answer: str, rag_mode: bool = False, health=None) -> tuple[str, bool]:
    """Constrói o prompt de auditoria GEO. Retorna (prompt, context_truncated)."""
    context_truncated = False
    if len(context) > config.MAX_CONTEXT_CHARS:
        original_len = len(context)
        context = context[:config.MAX_CONTEXT_CHARS]
        context_truncated = True
        logger.warning("Contexto truncado de %d para %d chars.", original_len, config.MAX_CONTEXT_CHARS)
        if health is not None:
            health.context_truncated = True
            health.context_original_chars = original_len
            health.context_used_chars = config.MAX_CONTEXT_CHARS

    rag_note = ""
    if rag_mode:
        rag_note = (
            "\nNOTA: O contexto abaixo foi recuperado de múltiplas páginas do site, "
            "selecionado por relevância semântica para esta pergunta. "
            "Cada trecho está rotulado com sua URL de origem. "
            "Considere TODOS os trechos ao formular sua resposta.\n"
        )

    prompt = f"""## TAREFA DE AUDITORIA
{rag_note}
### Conteúdo original do site da marca (CONTEXTO):
{context}

### Pergunta estratégica:
{question}

### Resposta oficial esperada (ground truth):
{official_answer}

---

INSTRUÇÕES:
1. Com base EXCLUSIVAMENTE no contexto acima, responda à pergunta.
2. Compare sua resposta com a resposta oficial esperada.
3. ANTES de atribuir o score, analise EXPLICITAMENTE:
   a) Claims da resposta oficial que FORAM preservados na sua resposta
   b) Claims da resposta oficial que foram OMITIDOS ou generalizados
   c) Informações na sua resposta que NÃO constam no contexto original (hallucinations)
4. Atribua um score de 0 a 100 seguindo critérios RIGOROSOS.
5. Responda EXCLUSIVAMENTE no formato JSON abaixo, sem texto adicional:

{{
  "resposta_ia": "Sua resposta extraída do contexto",
  "score": <número inteiro de 0 a 100>,
  "claims_preservados": ["claim 1", "claim 2"],
  "claims_omitidos": ["claim omitido 1"],
  "hallucinations": ["informação inventada 1 (se houver)"],
  "justificativa": "Explicação concisa do score"
}}"""

    return prompt, context_truncated


async def evaluate_question_async(
    context: str,
    question: str,
    official_answer: str,
    api_key: str,
    rag=None,
    health=None,
) -> dict:
    """Avalia uma pergunta via Gemini (async nativo).

    Returns:
        Dict com resposta_ia, score, justificativa, etc.
    """
    if not api_key:
        api_key = config.GEMINI_API_KEY
    if not api_key:
        return {"resposta_ia": "", "score": -1, "justificativa": "[ERRO] API key não configurada."}

    # RAG retrieval (sync, CPU-bound)
    sources = []
    rag_mode = False
    if rag is not None and hasattr(rag, "is_ready") and rag.is_ready:
        try:
            context, sources = rag.retrieve(question)
            rag_mode = True
        except Exception as e:
            logger.warning("Falha no retrieval RAG (%s), usando contexto agregado.", e)
            if health is not None:
                health.total_retries += 1

    client = get_genai_client(api_key)
    prompt, context_truncated = build_prompt(context, question, official_answer, rag_mode=rag_mode, health=health)

    for attempt in range(config.MAX_RETRIES):
        try:
            # Chamada Gemini async nativa (sem to_thread!)
            response = await client.aio.models.generate_content(
                model=config.GEMINI_MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=_SYSTEM_INSTRUCTION,
                    temperature=0,
                    top_p=1.0,
                    top_k=1,
                ),
            )

            response_text = response.text if response.text else None

            if not response_text:
                result = {
                    "resposta_ia": "",
                    "score": -1,
                    "justificativa": "[BLOQUEADO] Resposta filtrada (safety filter).",
                    "context_truncated": context_truncated,
                }
                if sources:
                    result["fontes"] = sources
                return result

            result, used_fallback = parse_json_response(response_text)
            if used_fallback and health is not None:
                health.json_parse_failures += 1
                health.json_parse_details.append(question[:80])

            # Validar e normalizar campos obrigatórios
            if not isinstance(result, dict) or "error" in result:
                logger.warning("Resposta Gemini não parseável para: %s", question[:80])
                result = {
                    "resposta_ia": response_text[:500] if response_text else "",
                    "score": -1,
                    "justificativa": "[ERRO] Resposta do modelo em formato inesperado.",
                }

            # Garantir tipos corretos (Gemini pode retornar null)
            resposta_ia = result.get("resposta_ia") or ""
            claims_pres = result.get("claims_preservados") or []
            claims_omit = result.get("claims_omitidos") or []
            if not isinstance(claims_pres, list):
                claims_pres = []
            if not isinstance(claims_omit, list):
                claims_omit = []

            if resposta_ia and result.get("score", -1) >= 0:
                try:
                    match_semantico = await _compute_semantic_similarity_async(
                        api_key, official_answer, resposta_ia
                    )
                except Exception:
                    match_semantico = 0.0

                taxa_claims = _compute_claims_rate(claims_pres, claims_omit)
                score_composto = calcular_score_pergunta(match_semantico, taxa_claims)

                result["score_gemini_original"] = result.get("score", -1)
                result["match_semantico"] = round(match_semantico, 1)
                result["taxa_claims"] = round(taxa_claims, 1)
                result["score"] = round(score_composto, 1)

            result["context_truncated"] = context_truncated
            if sources:
                result["fontes"] = sources
            return result

        except Exception as e:
            error_msg = str(e).lower()
            is_rate_limit = any(k in error_msg for k in ("quota", "429", "resource"))
            if attempt < config.MAX_RETRIES - 1:
                wait = 2 ** (attempt + 1)
                logger.warning("Gemini %s, retry em %ds...", "rate limit" if is_rate_limit else f"erro ({e})", wait)
                if health is not None:
                    health.total_retries += 1
                    health.retry_details.append({
                        "question": question[:80], "attempt": attempt + 1,
                        "reason": "rate_limit" if is_rate_limit else "other", "wait_s": wait,
                    })
                await asyncio.sleep(wait)  # async sleep, não bloqueia!
            else:
                logger.error("Falha após %d tentativas: %s", config.MAX_RETRIES, str(e)[:200])
                result = {
                    "resposta_ia": "", "score": -1,
                    "justificativa": f"[ERRO] Falha após {config.MAX_RETRIES} tentativas.",
                    "context_truncated": context_truncated,
                }
                if sources:
                    result["fontes"] = sources
                return result
