"use client";

import { useAuditStore } from "@/lib/store";
import { SiteInputForm } from "@/components/site-input/SiteInputForm";
import { QuestionsForm } from "@/components/expert-answers/QuestionsForm";
import { EvaluationProgress } from "@/components/evaluation/EvaluationProgress";
import { ScoreCards } from "@/components/results/ScoreCards";
import { ResultsTable } from "@/components/results/ResultsTable";
import { ResultCard } from "@/components/results/ResultCard";

export default function AuditPage() {
  const { currentStep, results, extractedContent } = useAuditStore();

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-kipiai-dark">
          Auditoria de Fidelidade
        </h1>
        <p className="text-kipiai-gray mt-1">
          Avalie a fidelidade das respostas de IA ao conteudo do seu site
        </p>
      </div>

      {/* Step 1: Site Input */}
      <section>
        <SiteInputForm />
      </section>

      {/* Step 2: Expert Answers */}
      {currentStep >= 2 && (
        <section>
          <QuestionsForm />
        </section>
      )}

      {/* Step 3: Evaluation Progress */}
      {currentStep >= 3 && (
        <section>
          <EvaluationProgress />
        </section>
      )}

      {/* Step 4: Results */}
      {currentStep >= 4 && results.length > 0 && (
        <section className="space-y-6">
          <ScoreCards />
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
