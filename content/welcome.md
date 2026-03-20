# Bem-vindo à Auditoria de Fidelidade RAG/GEO

Esta ferramenta avalia se as respostas geradas por IA preservam fielmente as informações do site da sua marca.

## Como funciona

### Passo 1 — Seleção do site
Informe a URL do site que deseja auditar. Você pode analisar uma única página ou o site completo.

### Passo 2 — Seleção de páginas
No modo **Site Completo**, a ferramenta descobre as páginas automaticamente (via sitemap ou links). Selecione quais páginas incluir na análise.

### Passo 3 — Interpretação das páginas
O conteúdo visível de cada página é extraído e processado para leitura pela IA.

### Passo 4 — Preparo da base (chunking)
O conteúdo é dividido em trechos menores e indexado semanticamente (RAG), permitindo que cada pergunta consulte os trechos mais relevantes.

### Passo 5 — Respostas do especialista
Preencha as respostas oficiais da marca para 5 perguntas estratégicas. A IA vai comparar o que encontra no site com o que você informou.

### Passo 6 — Relatório final
A IA avalia cada resposta com um **Score de Fidelidade (0-100)** e gera um relatório Excel detalhado.

## Escala de avaliação

| Score | Significado |
|-------|-------------|
| 95-100 | Todos os claims preservados literalmente |
| 85-94 | Claims principais corretos, reformulações mínimas |
| 70-84 | Essencial presente, detalhes secundários omitidos |
| 50-69 | Omissões significativas ou generalizações |
| 30-49 | Erros factuais ou claims inventados |
| 0-29 | Resposta incorreta ou alucinada |
