"""Motor de matching: cruza resultados da auditoria com a base de conhecimento First-Claim."""

import json
import os
import re

import numpy as np
import streamlit as st

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge")
KB_PATH = os.path.join(KNOWLEDGE_DIR, "knowledge_base.json")
EMB_PATH = os.path.join(KNOWLEDGE_DIR, "embeddings.npz")

# Mapeamento de perguntas da auditoria → chave curta usada na knowledge base
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


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Similaridade cosseno entre dois vetores."""
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def _has_quantitative_claims(claims: list[str]) -> bool:
    """Verifica se algum claim contém dados quantitativos."""
    for claim in claims:
        if re.search(r"\d+[%,.]|\d+\s*(mil|reais|dólares|anos|meses|horas)", claim, re.IGNORECASE):
            return True
    return False


@st.cache_resource
def load_knowledge() -> tuple[list[dict], np.ndarray] | None:
    """Carrega a base de conhecimento uma única vez (cache compartilhado entre sessões)."""
    if not os.path.exists(KB_PATH) or not os.path.exists(EMB_PATH):
        return None

    with open(KB_PATH, "r", encoding="utf-8") as f:
        kb = json.load(f)

    data = np.load(EMB_PATH)
    embeddings = data["embeddings"]

    return kb, embeddings


def is_available() -> bool:
    """Verifica se a base de conhecimento está disponível."""
    return os.path.exists(KB_PATH) and os.path.exists(EMB_PATH)


def match_suggestions(
    results: list[dict],
    claims_embeddings: dict[str, np.ndarray] | None = None,
    top_k: int = 3,
) -> dict[str, list[dict]]:
    """Para cada pergunta, retorna as top-k sugestões mais relevantes.

    Args:
        results: Lista de resultados da auditoria (mesma estrutura do session_state.results).
        claims_embeddings: Embeddings dos claims omitidos por pergunta (opcional, para similaridade).
        top_k: Número máximo de sugestões por pergunta.

    Returns:
        Dict mapeando pergunta → lista de sugestões rankeadas.
    """
    loaded = load_knowledge()
    if loaded is None:
        return {}

    kb, embeddings = loaded
    suggestions_by_question: dict[str, list[dict]] = {}
    used_ids: set[str] = set()  # Para deduplicação entre perguntas

    # Boost por impacto
    impact_boost = {"alto": 1.3, "medio": 1.0, "baixo": 0.7}

    for r in results:
        pergunta = r["Pergunta"]
        score = r.get("Score", -1)
        match_sem = r.get("Match Semântico", -1)
        taxa_cl = r.get("Taxa Claims", -1)
        claims_omitidos = r.get("Claims Omitidos", []) or []
        hallucinations = r.get("Hallucinations", []) or []

        if score < 0:
            continue  # Erro na avaliação, pula

        q_key = _question_to_key(pergunta)
        candidates = []

        for i, init in enumerate(kb):
            criterios = init.get("criterios_ativacao", {})
            init_id = init.get("id", f"FC-{i}")

            # --- Filtro por critérios de ativação ---
            # Normaliza: se valores vieram como decimal (0-1), converte para 0-100
            score_max = criterios.get("score_max", 70)
            match_max = criterios.get("match_semantico_max", 75)
            taxa_max = criterios.get("taxa_claims_max", 70)
            if score_max <= 1:
                score_max *= 100
            if match_max <= 1:
                match_max *= 100
            if taxa_max <= 1:
                taxa_max *= 100

            # Pelo menos um critério deve ser atingido
            score_match = score < score_max
            sem_match = match_sem >= 0 and match_sem < match_max
            taxa_match = taxa_cl >= 0 and taxa_cl < taxa_max

            if not (score_match or sem_match or taxa_match):
                continue

            # Filtro por hallucinations (se requerido)
            if criterios.get("requer_hallucinations", False) and not hallucinations:
                continue

            # Filtro por claims quantitativos (se requerido)
            if criterios.get("requer_claims_quantitativos", False):
                if not _has_quantitative_claims(claims_omitidos):
                    continue

            # --- Scoring de relevância ---
            relevance = 0.0

            # Fator 1: Quantos critérios foram atingidos (0-3)
            criteria_hits = sum([score_match, sem_match, taxa_match])
            relevance += criteria_hits * 15  # Max 45

            # Fator 2: Match de pergunta relacionada (0 ou 25)
            perguntas_rel = init.get("perguntas_relacionadas", [])
            if q_key and q_key in perguntas_rel:
                relevance += 25

            # Fator 3: Severidade do problema (quanto pior o score, mais relevante)
            if score_match:
                gap = score_max - score
                relevance += min(gap, 30)  # Max 30, proporcional à distância

            # Fator 4: Similaridade semântica com claims omitidos (se embeddings disponíveis)
            if claims_embeddings and pergunta in claims_embeddings and i < len(embeddings):
                sim = _cosine_similarity(claims_embeddings[pergunta], embeddings[i])
                relevance += sim * 20  # Max ~20

            # Boost por impacto
            impacto = init.get("impacto", "medio")
            relevance *= impact_boost.get(impacto, 1.0)

            # Normaliza para 0-100
            relevance = min(relevance, 100)

            candidates.append({
                "id": init_id,
                "titulo": init.get("titulo", ""),
                "eixo": init.get("eixo", ""),
                "eixo_numero": init.get("eixo_numero", 0),
                "descricao": init.get("descricao_profunda", ""),
                "implementacao": init.get("implementacao_humana", ""),
                "impacto": impacto,
                "relevancia": round(relevance, 1),
            })

        # Ordena por relevância e deduplica
        candidates.sort(key=lambda x: x["relevancia"], reverse=True)
        selected = []
        for c in candidates:
            if c["id"] not in used_ids and len(selected) < top_k:
                selected.append(c)
                used_ids.add(c["id"])

        if selected:
            suggestions_by_question[pergunta] = selected

    return suggestions_by_question


def contextualize_suggestion(
    suggestion: dict,
    claims_omitidos: list[str],
    contexto_resumo: str,
    api_key: str,
) -> dict:
    """Contextualiza uma sugestão genérica para a marca avaliada via Gemini.

    Returns:
        Dict com sugestao_contextualizada, exemplo_antes, exemplo_depois.
    """
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=genai.GenerationConfig(temperature=0.3),
    )

    claims_text = "\n".join(f"- {c}" for c in claims_omitidos) if claims_omitidos else "Nenhum claim omitido específico."

    prompt = f"""Você é um consultor GEO da Kípiai. Adapte a sugestão genérica abaixo para o caso específico desta marca.

CONTEXTO DO SITE DA MARCA (resumo):
{contexto_resumo[:3000]}

CLAIMS OMITIDOS PELA IA:
{claims_text}

SUGESTÃO GENÉRICA DO PROTOCOLO FIRST-CLAIM:
Título: {suggestion['titulo']}
Descrição: {suggestion['descricao']}
Implementação: {suggestion['implementacao']}

Responda EXCLUSIVAMENTE em JSON:
{{
  "sugestao_contextualizada": "Texto adaptado explicando o que a marca específica deve fazer",
  "exemplo_antes": "Como o conteúdo está hoje (baseado nos claims omitidos)",
  "exemplo_depois": "Como deveria ficar após a melhoria"
}}"""

    try:
        response = model.generate_content(prompt)
        raw = response.text
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            return json.loads(match.group())
        return json.loads(raw)
    except Exception:
        return {
            "sugestao_contextualizada": suggestion["implementacao"],
            "exemplo_antes": "",
            "exemplo_depois": "",
        }
