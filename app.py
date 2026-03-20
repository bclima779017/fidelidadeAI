import streamlit as st
import pandas as pd
import ai_handler
import report_handler
import scraper
import sitemap
import config
import time

PERGUNTAS = [
    "Qual é a proposta de valor da marca?",
    "Quais são os principais diferenciais competitivos?",
    "Qual é o público-alvo da marca?",
    "Qual problema a marca resolve para seus clientes?",
    "Quais são os principais produtos e/ou serviços?",
]

st.set_page_config(
    page_title="Auditoria GEO — Kípiai",
    page_icon="🔍",
    layout="wide",
)

st.title("Auditoria de Fidelidade RAG/GEO — Kípiai")
st.markdown("Avalie a fidelidade das respostas de IA comparando com as respostas do especialista da marca.")

# --- Sidebar: Configuração ---
with st.sidebar:
    st.header("Configuração")
    api_key = st.text_input(
        "Gemini API Key",
        value=config.GEMINI_API_KEY or "",
        type="password",
        help="Informe sua chave da API Gemini. Também pode ser definida no .env",
    )

    # Métricas RAG no sidebar
    if "rag" in st.session_state and st.session_state.rag is not None and st.session_state.rag.is_ready:
        st.divider()
        st.subheader("Índice RAG")
        stats = st.session_state.rag.get_stats()
        st.metric("Total de Páginas", stats["total_pages"])
        st.metric("Total de Chunks", stats["total_chunks"])
        if stats["chunks_per_page"]:
            avg_chunks = stats["total_chunks"] / stats["total_pages"]
            st.metric("Chunks/Página (média)", f"{avg_chunks:.1f}")

# --- Inicializar session_state ---
for key in ["contexto", "page_contents", "rag", "discovered_urls", "results"]:
    if key not in st.session_state:
        st.session_state[key] = "" if key == "contexto" else None

# --- Seção 1: URL do site ---
st.header("1. Contexto do Site")

url = st.text_input("URL do site para análise", placeholder="https://www.exemplo.com.br")

modo = st.radio(
    "Modo de extração",
    ["Página única", "Site completo (sitemap)"],
    horizontal=True,
    help="Página única: extrai apenas a URL informada. Site completo: descobre e extrai múltiplas páginas.",
)

# --- Modo Página Única ---
if modo == "Página única":
    extrair = st.button("Extrair Contexto")

    if extrair and url:
        with st.spinner("Extraindo conteúdo do site..."):
            try:
                st.session_state.contexto = scraper.extract_site_content(url)
                st.session_state.page_contents = None
                st.session_state.rag = None
                st.success(f"Contexto extraído: {len(st.session_state.contexto):,} caracteres")
            except Exception as e:
                st.error(f"Erro ao acessar o site: {e}")

    if st.session_state.contexto and st.session_state.page_contents is None:
        with st.expander("Ver contexto extraído"):
            st.text(st.session_state.contexto[:5000] + ("..." if len(st.session_state.contexto) > 5000 else ""))

# --- Modo Site Completo ---
else:
    col1, col2 = st.columns([1, 1])
    with col1:
        max_pages = st.number_input("Máximo de páginas", min_value=5, max_value=200, value=50, step=5)
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        descobrir = st.button("Descobrir Páginas")

    if descobrir and url:
        with st.spinner("Descobrindo páginas do site..."):
            try:
                urls = sitemap.discover_urls(url, max_pages=max_pages)
                if urls:
                    st.session_state.discovered_urls = urls
                    st.success(f"{len(urls)} páginas descobertas")
                else:
                    st.warning("Nenhuma página encontrada. Verifique a URL.")
            except Exception as e:
                st.error(f"Erro ao descobrir páginas: {e}")

    # Tabela de URLs com seleção
    if st.session_state.discovered_urls:
        st.subheader("Páginas Descobertas")
        urls_data = st.session_state.discovered_urls

        df_urls = pd.DataFrame(urls_data)
        df_urls["selecionar"] = True

        edited_df = st.data_editor(
            df_urls,
            column_config={
                "selecionar": st.column_config.CheckboxColumn("Selecionar", default=True),
                "url": st.column_config.TextColumn("URL", width="large"),
                "lastmod": st.column_config.TextColumn("Última Modificação"),
                "source": st.column_config.TextColumn("Fonte"),
            },
            disabled=["url", "lastmod", "source"],
            use_container_width=True,
            hide_index=True,
        )

        selected_urls = edited_df[edited_df["selecionar"]]["url"].tolist()
        st.caption(f"{len(selected_urls)} de {len(urls_data)} páginas selecionadas")

        extrair_multi = st.button("Extrair Selecionadas", type="primary")

        if extrair_multi and selected_urls:
            progress_bar = st.progress(0, text="Extraindo páginas...")

            def update_progress(p, text):
                progress_bar.progress(min(p, 1.0), text=text)

            try:
                pages = scraper.extract_multi_page_content(selected_urls, progress_callback=update_progress)
                st.session_state.page_contents = pages

                # Agrega contexto para compatibilidade
                all_text = []
                for page in pages:
                    all_text.append(f"--- {page['url']} ({page['title']}) ---\n{page['content']}")
                st.session_state.contexto = "\n\n".join(all_text)

                total_chars = sum(p["char_count"] for p in pages)
                progress_bar.progress(1.0, text="Extração concluída!")
                st.success(f"{len(pages)} páginas extraídas — {total_chars:,} caracteres no total")

                # Indexação RAG automática se API key disponível
                if api_key and pages:
                    from rag import AuditRAG

                    rag_progress = st.progress(0, text="Indexando conteúdo para RAG...")

                    def update_rag_progress(p, text):
                        rag_progress.progress(min(p, 1.0), text=text)

                    try:
                        rag_instance = AuditRAG(api_key)
                        n_chunks = rag_instance.ingest(pages, progress_callback=update_rag_progress)
                        st.session_state.rag = rag_instance
                        rag_progress.progress(1.0, text="Indexação concluída!")
                        st.success(f"RAG indexado: {n_chunks} chunks prontos para retrieval semântico")
                    except Exception as e:
                        st.warning(f"Falha na indexação RAG: {e}. A auditoria usará texto agregado.")
                        st.session_state.rag = None

            except Exception as e:
                st.error(f"Erro na extração: {e}")

    # Mostrar conteúdo extraído
    if st.session_state.page_contents:
        with st.expander(f"Ver conteúdo extraído ({len(st.session_state.page_contents)} páginas)"):
            for page in st.session_state.page_contents[:5]:
                st.markdown(f"**{page['title']}** — `{page['url']}` ({page['char_count']:,} chars)")
                st.text(page["content"][:500] + ("..." if len(page["content"]) > 500 else ""))
                st.divider()
            if len(st.session_state.page_contents) > 5:
                st.caption(f"... e mais {len(st.session_state.page_contents) - 5} páginas")

# --- Preview de Retrieval ---
if (st.session_state.get("rag") is not None
        and st.session_state.rag.is_ready):
    with st.expander("Preview de Retrieval RAG (ver contexto por pergunta)"):
        for pergunta in PERGUNTAS:
            st.markdown(f"**{pergunta}**")
            context_preview, sources = st.session_state.rag.retrieve(pergunta, top_k=3)
            if sources:
                st.caption(f"Fontes: {', '.join(sources[:3])}")
            st.text(context_preview[:800] + ("..." if len(context_preview) > 800 else ""))
            st.divider()

# --- Seção 2: Respostas do especialista ---
st.header("2. Respostas do Especialista")
st.markdown("Preencha as respostas oficiais da marca para cada pergunta:")

respostas = {}
for i, pergunta in enumerate(PERGUNTAS):
    respostas[i] = st.text_area(
        pergunta,
        key=f"resp_{i}",
        height=100,
    )

# --- Seção 3: Avaliação ---
st.header("3. Avaliação de Fidelidade")

rag_active = (st.session_state.get("rag") is not None
              and st.session_state.rag.is_ready)
if rag_active:
    st.info("Modo RAG ativo: retrieval semântico será usado para cada pergunta.")

avaliar = st.button("Avaliar Fidelidade", type="primary", use_container_width=True)

if avaliar:
    if not api_key:
        st.error("Informe a Gemini API Key na sidebar.")
        st.stop()

    if not st.session_state.contexto:
        st.error("Extraia o contexto do site primeiro.")
        st.stop()

    perguntas_preenchidas = [(i, PERGUNTAS[i], respostas[i]) for i in range(len(PERGUNTAS)) if respostas[i].strip()]
    if not perguntas_preenchidas:
        st.error("Preencha pelo menos uma resposta do especialista.")
        st.stop()

    results = []
    progress = st.progress(0, text="Avaliando...")

    rag_instance = st.session_state.get("rag")

    for idx, (i, pergunta, resposta_oficial) in enumerate(perguntas_preenchidas):
        progress.progress(
            idx / len(perguntas_preenchidas),
            text=f"Avaliando pergunta {idx + 1}/{len(perguntas_preenchidas)}...",
        )

        result = ai_handler.evaluate_question(
            context=st.session_state.contexto,
            question=pergunta,
            official_answer=resposta_oficial,
            api_key=api_key,
            rag=rag_instance,
        )

        row = {
            "Pergunta": pergunta,
            "Resposta Oficial": resposta_oficial,
            "Resposta IA": result.get("resposta_ia", ""),
            "Score": result.get("score", -1),
            "Justificativa": result.get("justificativa", ""),
        }
        if result.get("fontes"):
            row["Fontes Consultadas"] = "\n".join(result["fontes"])

        results.append(row)

        if idx < len(perguntas_preenchidas) - 1:
            time.sleep(2)

    progress.progress(1.0, text="Concluído!")
    st.session_state.results = results

# --- Seção 4: Resultados ---
if st.session_state.get("results"):
    results = st.session_state.results
    st.header("4. Resultados")

    # Score cards
    scores = [r["Score"] for r in results if r["Score"] >= 0]
    if scores:
        col1, col2, col3 = st.columns(3)
        col1.metric("Score Médio", f"{sum(scores) / len(scores):.1f}")
        col2.metric("Score Mínimo", min(scores))
        col3.metric("Score Máximo", max(scores))

    # Tabela de resultados
    df = pd.DataFrame(results)
    display_cols = ["Pergunta", "Resposta Oficial", "Resposta IA", "Score", "Justificativa"]
    has_sources = "Fontes Consultadas" in df.columns
    if has_sources:
        display_cols.append("Fontes Consultadas")

    st.dataframe(
        df[display_cols],
        use_container_width=True,
        column_config={
            "Score": st.column_config.ProgressColumn(
                "Score",
                min_value=0,
                max_value=100,
                format="%d",
            ),
        },
    )

    # Atribuição de fontes por pergunta
    if has_sources:
        with st.expander("Fontes consultadas por pergunta"):
            for r in results:
                if r.get("Fontes Consultadas"):
                    st.markdown(f"**{r['Pergunta']}**")
                    for fonte in r["Fontes Consultadas"].split("\n"):
                        st.markdown(f"- `{fonte}`")
                    st.divider()

    # Preparar metadados RAG para o relatório
    rag_metadata = None
    if st.session_state.get("rag") is not None and st.session_state.rag.is_ready:
        stats = st.session_state.rag.get_stats()
        rag_metadata = {
            "total_pages": stats["total_pages"],
            "total_chunks": stats["total_chunks"],
            "chunks_per_page": stats["chunks_per_page"],
        }

    # Download Excel
    filepath = report_handler.generate_report(results, rag_metadata=rag_metadata)
    with open(filepath, "rb") as f:
        st.download_button(
            label="Download Relatório Excel",
            data=f.read(),
            file_name=filepath.split("/")[-1].split("\\")[-1],
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
