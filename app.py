import os
import streamlit as st
import pandas as pd
import ai_handler
import report_handler
import scraper
import sitemap
import config
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from scoring import PERGUNTAS, PLACEHOLDERS, calcular_score_ponderado
from health import EvalHealth
import suggestions

def _render_health_panel(health: EvalHealth):
    """Renderiza o painel de Saúde da Avaliação."""
    cols = st.columns(5)

    with cols[0]:
        if health.context_truncated:
            st.metric("Contexto Truncado", "Sim", f"-{health.pct_lost:.1f}%")
            st.caption(f"{health.context_original_chars:,} &rarr; {health.context_used_chars:,} chars")
        else:
            st.metric("Contexto Truncado", "Não")

    with cols[1]:
        if health.json_parse_failures > 0:
            st.metric("Fallback JSON", health.json_parse_failures)
            for q in health.json_parse_details[:3]:
                st.caption(f"&bull; {q[:50]}")
        else:
            st.metric("Fallback JSON", "0")

    with cols[2]:
        if health.total_retries > 0:
            rate = sum(1 for d in health.retry_details if d["reason"] == "rate_limit")
            st.metric("Retries API", health.total_retries)
            st.caption(f"{rate} rate-limit, {health.total_retries - rate} outros")
        else:
            st.metric("Retries API", "0")

    with cols[3]:
        n_poor = len(health.poor_extraction_pages)
        if n_poor > 0:
            st.metric("Páginas Fracas", n_poor, f"<{health.poor_extraction_threshold} chars")
            for p in health.poor_extraction_pages[:3]:
                st.caption(f"&bull; {p['url'][-45:]} ({p['char_count']})")
        else:
            st.metric("Páginas Fracas", "0")

    with cols[4]:
        n_thin = len(health.thin_chunks)
        if n_thin > 0:
            st.metric("Chunks Finos", n_thin, f"<{health.thin_chunk_threshold} chars")
            for c in health.thin_chunks[:3]:
                st.caption(f"&bull; {c['text_preview'][:40]}... ({c['char_count']})")
        else:
            st.metric("Chunks Finos", "0")


st.set_page_config(
    page_title="Auditoria GEO — Kípiai",
    page_icon="🔍",
    layout="wide",
)

# --- Inicializar session_state ---
_DEFAULTS = {
    "contexto": "",
    "page_contents": None,
    "rag": None,
    "discovered_urls": None,
    "results": None,
    "last_url": "",
    "current_step": 0,
    "welcome_dismissed": False,
    "eval_health": None,
}
for key, default in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default


# --- Modal de boas-vindas ---
@st.dialog("Bem-vindo à Auditoria GEO — Kípiai", width="large")
def show_welcome():
    welcome_path = os.path.join(os.path.dirname(__file__), "content", "welcome.md")
    try:
        with open(welcome_path, "r", encoding="utf-8") as f:
            st.markdown(f.read())
    except FileNotFoundError:
        st.markdown("Bem-vindo! Siga os passos na interface para auditar a fidelidade do seu site.")
    if st.button("Entendido! Vamos começar", type="primary", use_container_width=True):
        st.session_state.welcome_dismissed = True
        st.rerun()


if not st.session_state.welcome_dismissed:
    show_welcome()


# --- Sidebar: Configuração + Progresso ---
STEPS = [
    ("Seleção de site", "site"),
    ("Seleção de páginas", "pages"),
    ("Interpretação das páginas", "extract"),
    ("Preparo de base (chunking)", "chunk"),
    ("Respostas às perguntas", "answers"),
    ("Relatório final", "report"),
]

with st.sidebar:
    st.header("Configuração")
    api_key = st.text_input(
        "Gemini API Key",
        value=config.GEMINI_API_KEY or "",
        type="password",
        help="Informe sua chave da API Gemini. Também pode ser definida no .env",
    )

    # Barra de progresso vertical
    st.divider()
    st.subheader("Progresso")
    current = st.session_state.current_step
    steps_html = ""
    for i, (label, _) in enumerate(STEPS):
        if i < current:
            color = "#28a745"
            icon = "&#10003;"
            font_weight = "normal"
            opacity = "1"
        elif i == current:
            color = "#007bff"
            icon = "&#9679;"
            font_weight = "bold"
            opacity = "1"
        else:
            color = "#6c757d"
            icon = "&#9675;"
            font_weight = "normal"
            opacity = "0.5"

        connector = ""
        if i < len(STEPS) - 1:
            line_color = "#28a745" if i < current else "#dee2e6"
            connector = (
                f'<div style="border-left: 2px solid {line_color}; '
                f'height: 20px; margin-left: 9px;"></div>'
            )

        steps_html += (
            f'<div style="display:flex; align-items:center; gap:8px; opacity:{opacity}">'
            f'<span style="color:{color}; font-size:18px; width:20px; text-align:center">{icon}</span>'
            f'<span style="color:{color}; font-weight:{font_weight}; font-size:14px">{label}</span>'
            f'</div>{connector}'
        )

    st.markdown(f'<div style="padding:8px 0">{steps_html}</div>', unsafe_allow_html=True)

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


st.title("Auditoria de Fidelidade RAG/GEO — Kípiai")
st.markdown("Avalie a fidelidade das respostas de IA comparando com as respostas do especialista da marca.")

# --- Seção 1: URL do site ---
st.header("1. Contexto do Site")

url = st.text_input("URL do site para análise", placeholder="https://www.exemplo.com.br")

# Detecção de troca de URL
url_changed = url.strip() != "" and url.strip() != st.session_state.last_url and st.session_state.last_url != ""
has_context = bool(st.session_state.contexto)

if url_changed and has_context:
    st.warning("URL diferente da última análise detectada.")
    if st.button("Reiniciar com novo site", type="primary"):
        for key in ["contexto", "page_contents", "rag", "discovered_urls", "results"]:
            st.session_state[key] = "" if key == "contexto" else None
        st.session_state.last_url = ""
        st.session_state.current_step = 0
        st.rerun()

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
                health = EvalHealth()
                content = scraper.extract_site_content(url)
                if len(content) < health.poor_extraction_threshold:
                    health.poor_extraction_pages.append({"url": url, "char_count": len(content)})
                st.session_state.contexto = content
                st.session_state.page_contents = None
                st.session_state.rag = None
                st.session_state.eval_health = health
                st.session_state.last_url = url.strip()
                st.session_state.current_step = 4  # Pula para respostas (sem seleção/chunk)
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
                    st.session_state.last_url = url.strip()
                    st.session_state.current_step = max(st.session_state.current_step, 1)
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
            st.session_state.current_step = max(st.session_state.current_step, 2)
            progress_bar = st.progress(0, text="Extraindo páginas...")
            health = EvalHealth()

            def update_progress(p, text):
                progress_bar.progress(min(p, 1.0), text=text)

            try:
                pages = scraper.extract_multi_page_content(selected_urls, progress_callback=update_progress, health=health)
                st.session_state.page_contents = pages

                # Agrega contexto para compatibilidade
                all_text = []
                for page in pages:
                    all_text.append(f"--- {page['url']} ({page['title']}) ---\n{page['content']}")
                st.session_state.contexto = "\n\n".join(all_text)

                total_chars = sum(p["char_count"] for p in pages)
                progress_bar.progress(1.0, text="Extração concluída!")
                st.session_state.current_step = max(st.session_state.current_step, 3)
                st.success(f"{len(pages)} páginas extraídas — {total_chars:,} caracteres no total")

                # Indexação RAG automática se API key disponível
                if api_key and pages:
                    from rag import AuditRAG

                    rag_progress = st.progress(0, text="Indexando conteúdo para RAG...")

                    def update_rag_progress(p, text):
                        rag_progress.progress(min(p, 1.0), text=text)

                    try:
                        rag_instance = AuditRAG(api_key)
                        n_chunks = rag_instance.ingest(pages, progress_callback=update_rag_progress, health=health)
                        st.session_state.rag = rag_instance
                        rag_progress.progress(1.0, text="Indexação concluída!")
                        st.session_state.current_step = max(st.session_state.current_step, 4)
                        st.success(f"RAG indexado: {n_chunks} chunks prontos para retrieval semântico")
                    except Exception as e:
                        st.warning(f"Falha na indexação RAG: {e}. A auditoria usará texto agregado.")
                        st.session_state.rag = None
                        st.session_state.current_step = max(st.session_state.current_step, 4)

                st.session_state.eval_health = health

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
        placeholder=PLACEHOLDERS.get(pergunta, ""),
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

    progress = st.progress(0, text="Avaliando perguntas em paralelo...")

    rag_instance = st.session_state.get("rag")
    contexto_atual = st.session_state.contexto
    total = len(perguntas_preenchidas)

    def _evaluate(item):
        idx, pergunta, resposta_oficial = item
        q_health = EvalHealth()
        result = ai_handler.evaluate_question(
            context=contexto_atual,
            question=pergunta,
            official_answer=resposta_oficial,
            api_key=api_key,
            rag=rag_instance,
            health=q_health,
        )
        return idx, pergunta, resposta_oficial, result, q_health

    # Processa em paralelo (max 3 threads para respeitar rate limits)
    results_map = {}
    completed = 0
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(_evaluate, item): item
            for item in perguntas_preenchidas
        }
        for future in as_completed(futures):
            completed += 1
            progress.progress(
                completed / total,
                text=f"Avaliadas {completed}/{total} perguntas...",
            )
            idx, pergunta, resposta_oficial, result, q_health = future.result()
            # Mescla health da thread no health master
            master_health = st.session_state.get("eval_health") or EvalHealth()
            master_health.merge(q_health)
            st.session_state.eval_health = master_health
            row = {
                "Pergunta": pergunta,
                "Resposta Oficial": resposta_oficial,
                "Resposta IA": result.get("resposta_ia", ""),
                "Score": result.get("score", -1),
                "Match Semântico": result.get("match_semantico", -1),
                "Taxa Claims": result.get("taxa_claims", -1),
                "Score Gemini Original": result.get("score_gemini_original", -1),
                "Justificativa": result.get("justificativa", ""),
            }
            if result.get("fontes"):
                row["Fontes Consultadas"] = "\n".join(result["fontes"])
            if result.get("claims_preservados"):
                row["Claims Preservados"] = result["claims_preservados"]
            if result.get("claims_omitidos"):
                row["Claims Omitidos"] = result["claims_omitidos"]
            if result.get("hallucinations"):
                row["Hallucinations"] = result["hallucinations"]
            results_map[idx] = row

    # Ordena resultados pela ordem original das perguntas
    results = [results_map[i] for i, _, _ in perguntas_preenchidas]

    progress.progress(1.0, text="Concluído!")
    st.session_state.results = results
    st.session_state.current_step = 5

# --- Seção 4: Resultados ---
if st.session_state.get("results"):
    results = st.session_state.results
    st.header("4. Resultados")

    # Score cards
    scores = [r["Score"] for r in results if r["Score"] >= 0]
    score_ponderado = calcular_score_ponderado(results) if scores else None
    if scores:
        col1, col2, col3 = st.columns(3)
        col1.metric("Score Final Ponderado", f"{score_ponderado:.1f}")
        col2.metric("Score Mínimo", min(scores))
        col3.metric("Score Máximo", max(scores))

    # Painel de Saúde da Avaliação
    health = st.session_state.get("eval_health")
    if health is not None and health.has_warnings:
        with st.expander("Saúde da Avaliação", expanded=False):
            _render_health_panel(health)

    # Tabela resumo compacta com breakdown
    df_resumo = pd.DataFrame([
        {
            "Pergunta": r["Pergunta"],
            "Match Semântico": r.get("Match Semântico", -1),
            "Taxa Claims": r.get("Taxa Claims", -1),
            "Score": r["Score"],
        }
        for r in results
    ])
    st.dataframe(
        df_resumo,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Match Semântico": st.column_config.ProgressColumn(
                "Match Semântico (peso 1)", min_value=0, max_value=100, format="%.1f",
            ),
            "Taxa Claims": st.column_config.ProgressColumn(
                "Taxa Claims (peso 2)", min_value=0, max_value=100, format="%.1f",
            ),
            "Score": st.column_config.ProgressColumn(
                "Score Final", min_value=0, max_value=100, format="%.1f",
            ),
        },
    )

    # Cards expandíveis por pergunta (resolve truncamento)
    for r in results:
        score = r["Score"]
        if score >= 70:
            score_emoji = "🟢"
        elif score >= 50:
            score_emoji = "🟡"
        elif score >= 0:
            score_emoji = "🔴"
        else:
            score_emoji = "⚫"

        with st.expander(f"{score_emoji} {r['Pergunta']} — Score: {score}", expanded=False):
            col_left, col_right = st.columns(2)
            with col_left:
                st.markdown("**Resposta do Especialista:**")
                st.markdown(r["Resposta Oficial"])
            with col_right:
                st.markdown("**Resposta da IA:**")
                st.markdown(r["Resposta IA"])

            # Breakdown do score
            if r.get("Match Semântico", -1) >= 0:
                st.divider()
                sc1, sc2, sc3, sc4 = st.columns(4)
                sc1.metric("Match Semântico", f"{r['Match Semântico']:.1f}%", help="Peso 1")
                sc2.metric("Taxa de Claims", f"{r['Taxa Claims']:.1f}%", help="Peso 2")
                sc3.metric("Score Composto", f"{r['Score']:.1f}")
                sc4.metric("Score Gemini (ref.)", r.get("Score Gemini Original", "—"), help="Score original do modelo, apenas referência")

            st.divider()
            st.markdown(f"**Justificativa:** {r['Justificativa']}")

            # Análise de claims (se disponível)
            if r.get("Claims Preservados") or r.get("Claims Omitidos") or r.get("Hallucinations"):
                st.divider()
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.markdown("**Claims Preservados:**")
                    for c in (r.get("Claims Preservados") or []):
                        st.markdown(f"- ✅ {c}")
                with col_b:
                    st.markdown("**Claims Omitidos:**")
                    for c in (r.get("Claims Omitidos") or []):
                        st.markdown(f"- ⚠️ {c}")
                with col_c:
                    st.markdown("**Hallucinations:**")
                    hallu = r.get("Hallucinations") or []
                    if hallu:
                        for c in hallu:
                            st.markdown(f"- ❌ {c}")
                    else:
                        st.markdown("Nenhuma detectada")

            if r.get("Fontes Consultadas"):
                st.divider()
                st.markdown("**Fontes Consultadas:**")
                for fonte in r["Fontes Consultadas"].split("\n"):
                    st.markdown(f"- `{fonte}`")

    # --- Seção 5: Sugestões de Melhoria ---
    suggestions_map = {}
    if suggestions.is_available():
        suggestions_map = suggestions.match_suggestions(results)

    if suggestions_map:
        st.header("5. Sugestões de Melhoria — Protocolo First Claim")
        st.markdown("Iniciativas recomendadas com base nos resultados da auditoria e no estudo de First-Claim da Kípiai.")

        for pergunta, sugs in suggestions_map.items():
            # Encontra o score da pergunta
            pergunta_score = next((r["Score"] for r in results if r["Pergunta"] == pergunta), -1)
            if pergunta_score >= 70:
                p_emoji = "🟢"
            elif pergunta_score >= 50:
                p_emoji = "🟡"
            else:
                p_emoji = "🔴"

            with st.expander(f"{p_emoji} {pergunta} — Score: {pergunta_score:.1f}", expanded=(pergunta_score < 70)):
                for sug in sugs:
                    imp = sug["impacto"]
                    imp_color = {"alto": "🔴", "medio": "🟡", "baixo": "🟢"}.get(imp, "⚪")

                    st.markdown(f"**{imp_color} {sug['titulo']}** — Eixo {sug['eixo_numero']}: {sug['eixo']}")

                    col_rel, col_imp = st.columns([1, 1])
                    col_rel.metric("Relevância", f"{sug['relevancia']:.0f}%")
                    col_imp.metric("Impacto", imp.capitalize())

                    st.markdown(f"**O que fazer:** {sug['implementacao']}")
                    with st.popover("Ver descrição completa"):
                        st.markdown(sug["descricao"])

                    # Contextualização via Gemini (sob demanda)
                    pergunta_results = next((r for r in results if r["Pergunta"] == pergunta), {})
                    claims_omit = pergunta_results.get("Claims Omitidos", []) or []

                    if claims_omit and api_key:
                        btn_key = f"ctx_{sug['id']}_{hash(pergunta) % 10000}"
                        if st.button(f"Contextualizar para esta marca", key=btn_key):
                            with st.spinner("Adaptando sugestão para a marca..."):
                                ctx = suggestions.contextualize_suggestion(
                                    suggestion=sug,
                                    claims_omitidos=claims_omit,
                                    contexto_resumo=st.session_state.contexto[:3000],
                                    api_key=api_key,
                                )
                            st.markdown(f"**Sugestão adaptada:** {ctx.get('sugestao_contextualizada', '')}")
                            if ctx.get("exemplo_antes"):
                                st.markdown(f"**Antes:** {ctx['exemplo_antes']}")
                            if ctx.get("exemplo_depois"):
                                st.markdown(f"**Depois:** {ctx['exemplo_depois']}")

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
    filepath = report_handler.generate_report(
        results, rag_metadata=rag_metadata, score_ponderado=score_ponderado,
        suggestions_data=suggestions_map if suggestions_map else None,
    )
    with open(filepath, "rb") as f:
        st.download_button(
            label="Download Relatório Excel",
            data=f.read(),
            file_name=filepath.split("/")[-1].split("\\")[-1],
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
