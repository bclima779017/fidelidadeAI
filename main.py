import time
import ai_handler
import report_handler
import scraper


PERGUNTAS = [
    "Qual é a proposta de valor da marca?",
    "Quais são os principais diferenciais competitivos?",
    "Qual é o público-alvo da marca?",
    "Qual problema a marca resolve para seus clientes?",
    "Quais são os principais produtos e/ou serviços?",
]


def run_audit():
    print("=" * 60)
    print("  AUDITORIA DE FIDELIDADE RAG/GEO — Kípiai")
    print("=" * 60)
    print()

    # 1. Obter URL do site
    url = input("URL do site para análise: ").strip()
    if not url:
        print("[ERRO] URL não informada.")
        return

    # 2. Extrair contexto do site
    print("\n[1/3] Extraindo conteúdo do site...")
    try:
        contexto = scraper.extract_site_content(url)
    except Exception as e:
        print(f"[ERRO] Não foi possível acessar o site: {e}")
        return
    print(f"       {len(contexto)} caracteres extraídos.\n")

    # 3. Coletar respostas do especialista
    print("[2/3] Informe as respostas do especialista para cada pergunta:\n")
    questions = []
    for i, pergunta in enumerate(PERGUNTAS, start=1):
        print(f"  {i}. {pergunta}")
        resposta = input("     Resposta: ").strip()
        if not resposta:
            print("     [AVISO] Resposta vazia, pergunta será ignorada.")
            continue
        questions.append({"pergunta": pergunta, "resposta_oficial": resposta})

    if not questions:
        print("\n[ERRO] Nenhuma resposta fornecida.")
        return

    # 4. Avaliar com Gemini
    print(f"\n[3/3] Avaliando {len(questions)} pergunta(s) com Gemini...\n")
    results = []

    for i, q in enumerate(questions, start=1):
        print(f"--- [{i}/{len(questions)}] ---")
        print(f"  Pergunta: \"{q['pergunta']}\"")

        result = ai_handler.evaluate_question(
            context=contexto,
            question=q["pergunta"],
            official_answer=q["resposta_oficial"],
        )

        score = result.get("score", -1)
        ai_answer = result.get("resposta_ia", "")
        justification = result.get("justificativa", "")

        print(f"  Score: {score}/100")
        print(f"  Justificativa: {justification[:120]}{'...' if len(justification) > 120 else ''}")

        results.append({
            "Pergunta": q["pergunta"],
            "Resposta Oficial": q["resposta_oficial"],
            "Resposta IA": ai_answer,
            "Score": score,
            "Justificativa": justification,
        })

        if i < len(questions):
            time.sleep(2)

        print()

    # 5. Gerar relatório Excel
    print("Gerando relatório Excel...")
    filepath = report_handler.generate_report(results)
    print(f"Relatório salvo em: {filepath}\n")

    # Resumo final
    scores = [r["Score"] for r in results if r["Score"] >= 0]
    errors = [r for r in results if r["Score"] == -1]

    print("=" * 60)
    print("  AUDITORIA GEO CONCLUÍDA")
    print("=" * 60)
    if scores:
        avg = sum(scores) / len(scores)
        print(f"  Total de perguntas:  {len(results)}")
        print(f"  Score médio:         {avg:.1f}")
        print(f"  Score mínimo:        {min(scores)}")
        print(f"  Score máximo:        {max(scores)}")
    if errors:
        print(f"  Linhas com erro:     {len(errors)}")
    print("=" * 60)


if __name__ == "__main__":
    run_audit()
