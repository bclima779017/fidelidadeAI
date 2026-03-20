# Auditoria de Fidelidade RAG/GEO — Kípiai

## Visão Geral
Aplicação web Streamlit para auditoria automatizada de fidelidade de respostas RAG/GEO.
O usuário informa a URL de um site (contexto via scraping), preenche 5 respostas do especialista,
e a IA compara as respostas extraídas do site com as do especialista, gerando um Score de Fidelidade (0-100).

## Arquitetura

```
app.py               → Interface web Streamlit (entrada/saída principal)
main.py              → CLI alternativo (loop de auditoria via terminal)
config.py            → Carrega variáveis de ambiente (.env)
scraper.py           → Extração de texto visível (página única + multi-página)
sitemap.py           → Descoberta de URLs via sitemap.xml ou crawling de links
rag.py               → Pipeline RAG: chunking + embedding + retrieval semântico
ai_handler.py        → Prompt de auditoria + chamada Gemini 2.0 Flash (temp=0)
report_handler.py    → Geração de relatório .xlsx com formatação condicional + aba RAG
```

## Fluxo de Execução (Streamlit)

### Modo Página Única (legado)
1. Usuário informa URL do site → scraper extrai texto visível
2. Usuário preenche respostas do especialista para 5 perguntas fixas
3. Para cada pergunta, envia prompt de auditoria ao Gemini
4. IA retorna JSON com `resposta_ia`, `score` (0-100), `justificativa`
5. Resultados exibidos na interface com score cards e tabela
6. Download de relatório Excel (.xlsx)

### Modo Site Completo (RAG)
1. Usuário informa URL → sitemap.py descobre páginas (sitemap.xml ou links)
2. Usuário seleciona páginas em tabela com checkboxes
3. scraper.py extrai conteúdo de cada página (com título/URL)
4. rag.py chunka (~500 tokens) e embeda via Gemini text-embedding-004
5. Para cada pergunta: retrieval híbrido (keyword + semântico) → top-10 chunks
6. ai_handler.py envia contexto focado ao Gemini com atribuição de fonte
7. Resultados com source attribution + relatório Excel com aba de metadados RAG

## 5 Perguntas Fixas
1. Qual é a proposta de valor da marca?
2. Quais são os principais diferenciais competitivos?
3. Qual é o público-alvo da marca?
4. Qual problema a marca resolve para seus clientes?
5. Quais são os principais produtos e/ou serviços?

## Premissas GEO (Manifesto Kípiai)
1. **Compreensibilidade**: Resposta clara sem distorcer conteúdo original
2. **Citação de Autoridade**: Claims técnicos, certificações, prêmios e dados preservados
3. **Preservação de Claims**: Nenhuma afirmação omitida, inventada ou alterada

## Escala de Score
- **90-100**: Semanticamente idêntica, todos os claims preservados
- **70-89**: Correta no essencial, detalhes secundários omitidos
- **50-69**: Parcialmente correta, omissões significativas
- **30-49**: Erros factuais ou claims inventados
- **0-29**: Incorreta, contraditória ou alucinada

## Configuração
- Copiar `.env.example` → `.env` e preencher `GEMINI_API_KEY` (ou informar na interface)
- Instalar dependências: `pip install -r requirements.txt`
- Executar Streamlit: `streamlit run app.py`
- Executar CLI: `python main.py`

## Modelo de IA
- **Gemini 2.0 Flash** com `temperature=0`, `top_p=1.0`, `top_k=1`
- **Gemini text-embedding-004** para embeddings no pipeline RAG
- Prompt retorna JSON estruturado, com fallback de parsing via regex

## Pipeline RAG
- **Chunking**: ~500 tokens (~2000 chars) com overlap de ~100 tokens, respeitando sentenças
- **Embedding**: text-embedding-004 em batches de até 100 chunks
- **Storage**: numpy arrays em memória (leve, efêmero por sessão)
- **Retrieval**: Híbrido (keywords por pergunta + similaridade cosseno) com boost por tipo de página
- **Deduplicação**: Chunks com cosseno > 0.92 removidos
- **Orçamento**: ~10 chunks x ~500 tokens = ~5k tokens de contexto focado por pergunta

## Convenções
- Linguagem do código: Python 3.10+
- Comentários e prints em português (PT-BR)
- Módulos independentes com responsabilidade única
- Retries com backoff exponencial para API Gemini
- Contexto truncado a 100k caracteres para respeitar limites do modelo (modo legado)
