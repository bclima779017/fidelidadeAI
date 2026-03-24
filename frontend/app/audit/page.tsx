"use client";

import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "motion/react";
import { useAuditStore } from "@/lib/store";
import { SiteInputForm } from "@/components/site-input/SiteInputForm";
import { QuestionsForm } from "@/components/expert-answers/QuestionsForm";
import { EvaluationProgress } from "@/components/evaluation/EvaluationProgress";
import { WelcomeModal } from "@/components/WelcomeModal";
import { ScoreCardSkeleton, ResultCardSkeleton } from "@/components/ui/Skeleton";

const ScoreCards = dynamic(
  () => import("@/components/results/ScoreCards").then((mod) => ({ default: mod.ScoreCards })),
  { ssr: false, loading: () => (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <ScoreCardSkeleton /><ScoreCardSkeleton /><ScoreCardSkeleton />
    </div>
  ) }
);
const ResultsTable = dynamic(
  () => import("@/components/results/ResultsTable").then((mod) => ({ default: mod.ResultsTable })),
  { ssr: false }
);
const ResultCard = dynamic(
  () => import("@/components/results/ResultCard").then((mod) => ({ default: mod.ResultCard })),
  { ssr: false, loading: () => <ResultCardSkeleton /> }
);
const HealthPanel = dynamic(
  () => import("@/components/results/HealthPanel").then((mod) => ({ default: mod.HealthPanel })),
  { ssr: false }
);

const sectionVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

export default function AuditPage() {
  const currentStep = useAuditStore((s) => s.currentStep);
  const results = useAuditStore((s) => s.results);
  const ragStats = useAuditStore((s) => s.ragStats);

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
      <WelcomeModal />

      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
        <h1 className="text-3xl font-bold text-kipiai-dark dark:text-white">
          Auditoria de Fidelidade
        </h1>
        <p className="text-kipiai-gray dark:text-gray-400 mt-1">
          Avalie a fidelidade das respostas de IA ao conteudo do seu site
        </p>
      </motion.div>

      {/* Step 1 */}
      <motion.section variants={sectionVariants} initial="hidden" animate="visible" aria-label="URL do site">
        <SiteInputForm />
      </motion.section>

      {/* RAG info */}
      <AnimatePresence>
        {ragStats && currentStep >= 2 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="flex items-center gap-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 text-sm overflow-hidden"
          >
            <span className="text-blue-700 dark:text-blue-400 font-medium">RAG ativo</span>
            <span className="text-blue-600 dark:text-blue-300">
              {ragStats.total_chunks} chunks | {ragStats.total_pages} paginas indexadas
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Step 2 */}
      <AnimatePresence>
        {currentStep >= 2 && (
          <motion.section variants={sectionVariants} initial="hidden" animate="visible" exit="hidden" aria-label="Respostas do especialista">
            <QuestionsForm />
          </motion.section>
        )}
      </AnimatePresence>

      {/* Step 3 */}
      <AnimatePresence>
        {currentStep >= 3 && (
          <motion.section variants={sectionVariants} initial="hidden" animate="visible" exit="hidden" aria-label="Progresso da avaliacao">
            <EvaluationProgress />
          </motion.section>
        )}
      </AnimatePresence>

      {/* Step 4 */}
      <AnimatePresence>
        {currentStep >= 4 && results.length > 0 && (
          <motion.section
            variants={sectionVariants}
            initial="hidden"
            animate="visible"
            className="space-y-6"
            aria-label="Resultados da auditoria"
          >
            <ScoreCards />
            <HealthPanel />
            <ResultsTable />
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-kipiai-dark dark:text-white">
                Detalhamento por Pergunta
              </h2>
              {results.map((result, index) => (
                <ResultCard key={index} result={result} index={index} />
              ))}
            </div>
          </motion.section>
        )}
      </AnimatePresence>
    </div>
  );
}
