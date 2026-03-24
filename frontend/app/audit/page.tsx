"use client";

import dynamic from "next/dynamic";
import { useAuditStore } from "@/lib/store";
import { SiteInputForm } from "@/components/site-input/SiteInputForm";
import { QuestionsForm } from "@/components/expert-answers/QuestionsForm";
import { EvaluationProgress } from "@/components/evaluation/EvaluationProgress";
import { WelcomeModal } from "@/components/WelcomeModal";

const ScoreCards = dynamic(
  () => import("@/components/results/ScoreCards").then((mod) => ({ default: mod.ScoreCards })),
  { ssr: false }
);
const ResultsTable = dynamic(
  () => import("@/components/results/ResultsTable").then((mod) => ({ default: mod.ResultsTable })),
  { ssr: false }
);
const ResultCard = dynamic(
  () => import("@/components/results/ResultCard").then((mod) => ({ default: mod.ResultCard })),
  { ssr: false }
);
const HealthPanel = dynamic(
  () => import("@/components/results/HealthPanel").then((mod) => ({ default: mod.HealthPanel })),
  { ssr: false }
);

export default function AuditPage() {
  const currentStep = useAuditStore((s) => s.currentStep);
  const results = useAuditStore((s) => s.results);
  const ragStats = useAuditStore((s) => s.ragStats);

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
      <WelcomeModal />
      <div>
        <h1 className="text-3xl font-bold text-kipiai-dark">
          Auditoria de Fidelidade
        </h1>
        <p className="text-kipiai-gray mt-1">
          Avalie a fidelidade das respostas de IA ao conteudo do seu site
        </p>
      </div>

      {/* Step 1: Site Input */}
      <section aria-label="URL do site">
        <SiteInputForm />
      </section>

      {/* RAG info after extraction */}
      {ragStats && currentStep >= 2 && (
        <div className="flex items-center gap-4 bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm">
          <span className="text-blue-700 font-medium">RAG ativo</span>
          <span className="text-blue-600">
            {ragStats.total_chunks} chunks | {ragStats.total_pages} paginas indexadas
          </span>
        </div>
      )}

      {/* Step 2: Expert Answers */}
      {currentStep >= 2 && (
        <section aria-label="Respostas do especialista">
          <QuestionsForm />
        </section>
      )}

      {/* Step 3: Evaluation Progress */}
      {currentStep >= 3 && (
        <section aria-label="Progresso da avaliacao">
          <EvaluationProgress />
        </section>
      )}

      {/* Step 4: Results */}
      {currentStep >= 4 && results.length > 0 && (
        <section className="space-y-6" aria-label="Resultados da auditoria">
          <ScoreCards />
          <HealthPanel />
          <ResultsTable />
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-kipiai-dark">
              Detalhamento por Pergunta
            </h2>
            {results.map((result, index) => (
              <ResultCard key={index} result={result} index={index} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
