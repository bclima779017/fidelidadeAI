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

PLACEHOLDERS = {
    "Qual é a proposta de valor da marca?": (
        "Ex: A marca oferece soluções de automação industrial que reduzem custos "
        "operacionais em até 40%, com suporte técnico 24/7 e integração com sistemas legados."
    ),
    "Quais são os principais diferenciais competitivos?": (
        "Ex: Tecnologia patenteada de compressão a frio, certificação ISO 9001, "
        "presença em 15 países e atendimento personalizado com SLA de 4 horas."
    ),
    "Qual é o público-alvo da marca?": (
        "Ex: Empresas de médio e grande porte do setor alimentício, com faturamento "
        "acima de R$10M/ano, que buscam modernizar suas linhas de produção."
    ),
    "Qual problema a marca resolve para seus clientes?": (
        "Ex: Elimina o desperdício de matéria-prima no processo produtivo, que representa "
        "em média 12% dos custos, através de sensores IoT e análise preditiva."
    ),
    "Quais são os principais produtos e/ou serviços?": (
        "Ex: 1) Plataforma SaaS de gestão de frotas; 2) Hardware de rastreamento "
        "veicular com GPS+4G; 3) Consultoria de otimização logística; 4) API para ERPs."
    ),
}


# Pesos dos dois fatores do scoring por pergunta
PESO_SEMANTICO = 1  # Peso da similaridade semântica
PESO_CLAIMS = 2     # Peso da taxa de correspondência de claims


def calcular_score_pergunta(match_semantico: float, taxa_claims: float) -> float:
    """Calcula o score de uma pergunta pela média ponderada dos dois fatores.

    Args:
        match_semantico: Percentual de match semântico (0-100).
        taxa_claims: Percentual de atingimento de claims (0-100).

    Returns:
        Score final da pergunta (0-100).
    """
    soma_pesos = PESO_SEMANTICO + PESO_CLAIMS
    return (PESO_SEMANTICO * match_semantico + PESO_CLAIMS * taxa_claims) / soma_pesos


def calcular_score_ponderado(results: list[dict]) -> float:
    """Calcula o score final ponderado, normalizando pelos pesos das perguntas respondidas."""
    scores_validos = [(r["Pergunta"], r["Score"]) for r in results if r["Score"] >= 0]
    if not scores_validos:
        return 0.0

    soma_pesos = sum(PESOS.get(pergunta, 0.20) for pergunta, _ in scores_validos)
    score = sum(PESOS.get(pergunta, 0.20) * s for pergunta, s in scores_validos)
    return score / soma_pesos if soma_pesos > 0 else 0.0
