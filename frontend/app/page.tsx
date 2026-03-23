import Link from "next/link";

export default function HomePage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-6 py-12">
      <div className="max-w-2xl text-center">
        <h1 className="text-5xl font-bold text-kipiai-dark mb-2">
          <span className="text-kipiai-blue">Kipiai</span>
        </h1>
        <p className="text-lg text-kipiai-gray mb-4">
          Auditoria de Fidelidade GEO
        </p>

        <div className="bg-white rounded-xl shadow-md p-8 mb-8 text-left">
          <h2 className="text-2xl font-semibold text-kipiai-dark mb-4">
            O que esta ferramenta faz?
          </h2>
          <p className="text-kipiai-gray mb-4">
            A Auditoria de Fidelidade GEO verifica se as respostas geradas por IA
            (RAG/GEO) preservam fielmente o conteudo original do seu site. O
            processo envolve:
          </p>
          <ul className="space-y-3 text-kipiai-gray mb-6">
            <li className="flex items-start gap-3">
              <span className="text-kipiai-blue font-bold mt-0.5">1.</span>
              <span>
                <strong>Extracao de contexto</strong> — o conteudo do site e
                extraido automaticamente
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-kipiai-blue font-bold mt-0.5">2.</span>
              <span>
                <strong>Respostas do especialista</strong> — voce informa as
                respostas oficiais para 5 perguntas-chave
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-kipiai-blue font-bold mt-0.5">3.</span>
              <span>
                <strong>Avaliacao por IA</strong> — o Gemini compara as respostas
                e gera um Score de Fidelidade (0-100)
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-kipiai-blue font-bold mt-0.5">4.</span>
              <span>
                <strong>Relatorio detalhado</strong> — resultados com claims
                analisados, sugestoes e metricas
              </span>
            </li>
          </ul>

          <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
            <h3 className="text-sm font-semibold text-kipiai-dark mb-2">
              Escala de Score
            </h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-kipiai-green" />
                <span>90-100: Fidelidade excelente</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-kipiai-green opacity-70" />
                <span>70-89: Essencialmente correta</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-kipiai-yellow" />
                <span>50-69: Parcialmente correta</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-kipiai-red" />
                <span>0-49: Problemas significativos</span>
              </div>
            </div>
          </div>
        </div>

        <Link
          href="/audit"
          className="inline-flex items-center gap-2 bg-kipiai-blue hover:bg-kipiai-blue-hover text-white font-semibold py-3 px-8 rounded-xl transition-colors text-lg shadow-md"
        >
          Iniciar Auditoria
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M5 12h14" />
            <path d="m12 5 7 7-7 7" />
          </svg>
        </Link>
      </div>
    </div>
  );
}
