"""CLI alternativo para auditoria de fidelidade RAG/GEO via terminal."""

import time

import ai_handler
import report_handler
import scraper
import sitemap
from scoring import PERGUNTAS, calcular_score_ponderado


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

    # 2. Escolher modo de extração
    print("\nModo de extração:")
    print("  1. Página única (apenas a URL informada)")
    print("  2. Site completo (descobre páginas via sitemap)")
    modo = input("Escolha [1/2] (padrão: 1): ").strip() or "1"

    contexto = ""
    page_contents = None
    rag_instance = None

    if modo == "2":
        # Modo multi-página
        max_pages_input = input("Máximo de páginas (padrão: 50): ").strip() or "50"
        max_pages = int(max_pages_input)

        print(f"\n[1/4] Descobrindo páginas do site (máx {max_pages})...")
        urls = sitemap.discover_urls(url, max_pages=max_pages)

        if not urls:
            print("[AVISO] Nenhuma página descoberta. Usando modo página única.")
            modo = "1"
        else:
            print(f"       {len(urls)} páginas encontradas:")
            for i, u in enumerate(urls, 1):
                print(f"       {i}. {u['url']} [{u['source']}]")

            print(f"\n[2/4] Extraindo conteúdo de {len(urls)} páginas...")
            selected_urls = [u["url"] for u in urls]
            page_contents = scraper.extract_multi_page_content(selected_urls)
            total_chars = sum(p["char_count"] for p in page_contents)
            print(f"       {len(page_contents)} páginas extraídas — {total_chars:,} caracteres.\n")

            # Agrega contexto
            all_text = []
            for page in page_contents:
                all_text.append(f"--- {page['url']} ({page['title']}) ---\n{page['content']}")
            contexto = "\n\n".join(all_text)

            # Tenta indexar com RAG
            usar_rag = input("Usar RAG semântico? [S/n] (requer API key): ").strip().lower()
            if usar_rag != "n":
                print("\n[3/4] Indexando conteúdo para RAG...")
                try:
                    from rag import AuditRAG
                    import config
                    api_key = config.GEMINI_API_KEY
                    if not api_key:
                        api_key = input("Gemini API Key: ").strip()
                    rag_instance = AuditRAG(api_key)
                    n_chunks = rag_instance.ingest(page_contents)
                    print(f"       {n_chunks} chunks indexados.\n")
                except Exception as e:
                    print(f"[AVISO] Falha na indexação RAG: {e}. Usando texto agregado.\n")
                    rag_instance = None

    if modo == "1":
        # Modo página única (original)
        print("\n[1/3] Extraindo conteúdo do site...")
        try:
            contexto = scraper.extract_site_content(url)
        except Exception as e:
            print(f"[ERRO] Não foi possível acessar o site: {e}")
            return
        print(f"       {len(contexto)} caracteres extraídos.\n")

    # 3. Coletar respostas do especialista
    step = "2/4" if modo == "2" else "2/3"
    print(f"[{step}] Informe as respostas do especialista para cada pergunta:\n")
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
    step = "4/4" if modo == "2" else "3/3"
    print(f"\n[{step}] Avaliando {len(questions)} pergunta(s) com Gemini...\n")
    results = []

    for i, q in enumerate(questions, start=1):
        print(f"--- [{i}/{len(questions)}] ---")
        print(f"  Pergunta: \"{q['pergunta']}\"")

        result = ai_handler.evaluate_question(
            context=contexto,
            question=q["pergunta"],
            official_answer=q["resposta_oficial"],
            rag=rag_instance,
        )

        score = result.get("score", -1)
        ai_answer = result.get("resposta_ia", "")
        justification = result.get("justificativa", "")
        fontes = result.get("fontes", [])

        print(f"  Score: {score}/100")
        print(f"  Justificativa: {justification[:120]}{'...' if len(justification) > 120 else ''}")
        if fontes:
            print(f"  Fontes: {', '.join(fontes[:3])}")

        row = {
            "Pergunta": q["pergunta"],
            "Resposta Oficial": q["resposta_oficial"],
            "Resposta IA": ai_answer,
            "Score": score,
            "Justificativa": justification,
        }
        if fontes:
            row["Fontes Consultadas"] = "\n".join(fontes)
        results.append(row)

        if i < len(questions):
            time.sleep(2)

        print()

    # 5. Gerar relatório Excel
    print("Gerando relatório Excel...")
    rag_metadata = None
    if rag_instance and rag_instance.is_ready:
        stats = rag_instance.get_stats()
        rag_metadata = {
            "total_pages": stats["total_pages"],
            "total_chunks": stats["total_chunks"],
            "chunks_per_page": stats["chunks_per_page"],
        }
    # Resumo final
    scores = [r["Score"] for r in results if r["Score"] >= 0]
    errors = [r for r in results if r["Score"] == -1]
    score_ponderado = calcular_score_ponderado(results) if scores else None

    filepath = report_handler.generate_report(results, rag_metadata=rag_metadata, score_ponderado=score_ponderado)
    print(f"Relatório salvo em: {filepath}\n")

    print("=" * 60)
    print("  AUDITORIA GEO CONCLUÍDA")
    print("=" * 60)
    if scores:
        score_ponderado = calcular_score_ponderado(results)
        print(f"  Total de perguntas:  {len(results)}")
        print(f"  Score ponderado:     {score_ponderado:.1f}")
        print(f"  Score mínimo:        {min(scores)}")
        print(f"  Score máximo:        {max(scores)}")
    if errors:
        print(f"  Linhas com erro:     {len(errors)}")
    if rag_instance and rag_instance.is_ready:
        print(f"  Modo:                RAG Multi-Página")
        stats = rag_instance.get_stats()
        print(f"  Páginas indexadas:   {stats['total_pages']}")
        print(f"  Chunks indexados:    {stats['total_chunks']}")
    print("=" * 60)


if __name__ == "__main__":
    run_audit()
