"""Motor de sugestões: cruza resultados da auditoria com a base de conhecimento First-Claim."""

import functools
import json
import logging
import os

import numpy as np
from google.genai import types

import config
from utils import get_genai_client, parse_json_response

KB_PATH = config.KB_PATH
EMB_PATH = config.EMB_PATH

# Mapeamento de perguntas da auditoria -> chave curta usada na knowledge base
_QUESTION_KEY_MAP = {
    "proposta de valor": "proposta de valor",
    "diferenciais competitivos": "diferenciais competitivos",
    "diferenciais": "diferenciais competitivos",
    "público-alvo": "público-alvo",
    "problema": "problema",
    "produtos": "produtos",
    "serviços": "produtos",
}


def _question_to_key(question: str) -> str:
    """Mapeia texto da pergunta para a chave curta."""
    q_lower = question.lower()
    for pattern, key in _QUESTION_KEY_MAP.items():
        if pattern in q_lower:
            return key
    return ""


@functools.lru_cache(maxsize=1)
def load_knowledge() -> tuple[list[dict], np.ndarray] | None:
    """Carrega a base de conhecimento uma unica vez (cache compartilhado entre sessoes)."""
    if not os.path.exists(KB_PATH) or not os.path.exists(EMB_PATH):
        return None

    with open(KB_PATH, "r", encoding="utf-8") as f:
        kb = json.load(f)

    with np.load(EMB_PATH) as data:
        embeddings = data["embeddings"].copy()

    return kb, embeddings


def is_available() -> bool:
    """Verifica se a base de conhecimento esta disponivel."""
    return os.path.exists(KB_PATH) and os.path.exists(EMB_PATH)


def match_suggestions(results: list[dict], top_k: int = 5) -> list[dict]:
    """Retorna as top_k sugestoes mais relevantes para os resultados da auditoria.

    Logica simplificada:
    1. Para cada recomendacao do KB, verifica se ao menos 1 pergunta relacionada tem score < 80
    2. Calcula relevancia = media dos gaps (80 - score) * multiplicador de impacto
    3. Ordena por relevancia e retorna as top_k

    Args:
        results: Lista de resultados da auditoria.
        top_k: Numero maximo de sugestoes retornadas (default: 5).

    Returns:
        Lista de sugestoes rankeadas por relevancia.
    """
    loaded = load_knowledge()
    if loaded is None:
        return []

    kb, _embeddings = loaded

    # Monta mapa pergunta_key -> (score, texto_pergunta)
    scores_by_key: dict[str, tuple[float, str]] = {}
    for r in results:
        pergunta = r["Pergunta"]
        score = r.get("Score", -1)
        if score < 0:
            continue
        q_key = _question_to_key(pergunta)
        if q_key:
            scores_by_key[q_key] = (score, pergunta)

    # Boost por impacto
    impact_boost = {"alto": 1.3, "medio": 1.0, "baixo": 0.7}

    candidates = []

    for init in kb:
        perguntas_rel = init.get("perguntas_relacionadas", [])
        impacto = init.get("impacto", "medio")

        # Coleta gaps das perguntas relacionadas que tem score < 80
        gaps = []
        perguntas_afetadas = []
        for p_key in perguntas_rel:
            if p_key in scores_by_key:
                score, pergunta_texto = scores_by_key[p_key]
                if score < config.SUGGESTION_THRESHOLD_SCORE:
                    gaps.append(config.SUGGESTION_THRESHOLD_SCORE - score)
                    perguntas_afetadas.append(f"{pergunta_texto} ({score:.0f})")

        # Recomendacao so ativa se ao menos 1 pergunta relacionada tem gap
        if not gaps:
            continue

        # Relevancia = media dos gaps * multiplicador de impacto
        base = sum(gaps) / len(gaps)
        relevancia = min(base * impact_boost.get(impacto, 1.0), 100)

        candidates.append({
            "id": init.get("id", ""),
            "titulo": init.get("titulo", ""),
            "eixo": f"Eixo {init.get('eixo_numero', '')}: {init.get('eixo', '')}",
            "impacto": impacto,
            "relevancia": round(relevancia, 1),
            "por_que": init.get("descricao_profunda", ""),
            "o_que_fazer": init.get("implementacao_humana", ""),
            "perguntas_afetadas": perguntas_afetadas,
        })

    # Ordena por relevancia e retorna top_k
    candidates.sort(key=lambda x: x["relevancia"], reverse=True)
    return candidates[:top_k]


def contextualize_suggestion(
    suggestion: dict,
    claims_omitidos: list[str],
    contexto_resumo: str,
    api_key: str,
) -> dict:
    """Contextualiza uma sugestao generica para a marca avaliada via Gemini.

    Returns:
        Dict com sugestao_contextualizada, exemplo_antes, exemplo_depois.
    """
    client = get_genai_client(api_key)

    claims_text = "\n".join(f"- {c}" for c in claims_omitidos) if claims_omitidos else "Nenhum claim omitido especifico."

    # Usa os nomes de campo do novo formato
    titulo = suggestion.get("titulo", "")
    descricao = suggestion.get("por_que", "") or suggestion.get("descricao", "")
    implementacao = suggestion.get("o_que_fazer", "") or suggestion.get("implementacao", "")

    prompt = f"""Voce e um consultor GEO da Kipiai. Adapte a sugestao generica abaixo para o caso especifico desta marca.

CONTEXTO DO SITE DA MARCA (resumo):
{contexto_resumo[:3000]}

CLAIMS OMITIDOS PELA IA:
{claims_text}

SUGESTAO GENERICA DO PROTOCOLO FIRST-CLAIM:
Titulo: {titulo}
Descricao: {descricao}
Implementacao: {implementacao}

Responda EXCLUSIVAMENTE em JSON:
{{
  "sugestao_contextualizada": "Texto adaptado explicando o que a marca especifica deve fazer",
  "exemplo_antes": "Como o conteudo esta hoje (baseado nos claims omitidos)",
  "exemplo_depois": "Como deveria ficar apos a melhoria"
}}"""

    try:
        response = client.models.generate_content(
            model=config.GEMINI_MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.3),
        )
        parsed, _ = parse_json_response(response.text)
        return parsed
    except (ConnectionError, TimeoutError, ValueError, RuntimeError) as e:
        logging.getLogger("kipiai.suggestions").warning("Falha ao contextualizar sugestão: %s", e)
        return {
            "sugestao_contextualizada": implementacao,
            "exemplo_antes": "",
            "exemplo_depois": "",
        }
