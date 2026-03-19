import streamlit as st
import pandas as pd
import ai_handler
import report_handler
import scraper
import config
import time
import io

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

# --- Sidebar: API Key ---
with st.sidebar:
    st.header("Configuração")
    api_key = st.text_input(
        "Gemini API Key",
        value=config.GEMINI_API_KEY or "",
        type="password",
        help="Informe sua chave da API Gemini. Também pode ser definida no .env",
    )

# --- Seção 1: URL do site ---
st.header("1. Contexto do Site")
col_url, col_btn = st.columns([4, 1])
with col_url:
    url = st.text_input("URL do site para análise", placeholder="https://www.exemplo.com.br")
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    extrair = st.button("Extrair Contexto")

if "contexto" not in st.session_state:
    st.session_state.contexto = ""

if extrair and url:
    with st.spinner("Extraindo conteúdo do site..."):
        try:
            st.session_state.contexto = scraper.extract_site_content(url)
            st.success(f"Contexto extraído: {len(st.session_state.contexto):,} caracteres")
        except Exception as e:
            st.error(f"Erro ao acessar o site: {e}")

if st.session_state.contexto:
    with st.expander("Ver contexto extraído"):
        st.text(st.session_state.contexto[:5000] + ("..." if len(st.session_state.contexto) > 5000 else ""))

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

avaliar = st.button("Avaliar Fidelidade", type="primary", use_container_width=True)

if avaliar:
    # Validações
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

    # Processar
    results = []
    progress = st.progress(0, text="Avaliando...")

    for idx, (i, pergunta, resposta_oficial) in enumerate(perguntas_preenchidas):
        progress.progress(
            (idx) / len(perguntas_preenchidas),
            text=f"Avaliando pergunta {idx + 1}/{len(perguntas_preenchidas)}...",
        )

        result = ai_handler.evaluate_question(
            context=st.session_state.contexto,
            question=pergunta,
            official_answer=resposta_oficial,
            api_key=api_key,
        )

        results.append({
            "Pergunta": pergunta,
            "Resposta Oficial": resposta_oficial,
            "Resposta IA": result.get("resposta_ia", ""),
            "Score": result.get("score", -1),
            "Justificativa": result.get("justificativa", ""),
        })

        if idx < len(perguntas_preenchidas) - 1:
            time.sleep(2)

    progress.progress(1.0, text="Concluído!")

    st.session_state.results = results

# --- Seção 4: Resultados ---
if "results" in st.session_state and st.session_state.results:
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
    st.dataframe(
        df,
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

    # Download Excel
    filepath = report_handler.generate_report(results)
    with open(filepath, "rb") as f:
        st.download_button(
            label="Download Relatório Excel",
            data=f.read(),
            file_name=filepath.split("/")[-1].split("\\")[-1],
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
