PERGUNTAS = [
    "Qual é a proposta de valor da marca?",
    "Quais são os principais diferenciais competitivos?",
    "Qual é o público-alvo da marca?",
    "Qual problema a marca resolve para seus clientes?",
    "Quais são os principais produtos e/ou serviços?",
]

PESOS = {
    "Qual é a proposta de valor da marca?": 0.25,
    "Quais são os principais diferenciais competitivos?": 0.20,
    "Qual é o público-alvo da marca?": 0.20,
    "Qual problema a marca resolve para seus clientes?": 0.15,
    "Quais são os principais produtos e/ou serviços?": 0.20,
}


def calcular_score_ponderado(results: list[dict]) -> float:
    """Calcula o score final ponderado, normalizando pelos pesos das perguntas respondidas."""
    scores_validos = [(r["Pergunta"], r["Score"]) for r in results if r["Score"] >= 0]
    if not scores_validos:
        return 0.0

    soma_pesos = sum(PESOS.get(pergunta, 0.20) for pergunta, _ in scores_validos)
    score = sum(PESOS.get(pergunta, 0.20) * s for pergunta, s in scores_validos)
    return score / soma_pesos if soma_pesos > 0 else 0.0
