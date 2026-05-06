import type { Metadata } from "next";

export const metadata: Metadata = { title: "Aprendizado" };

export default function LearningPage() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold tracking-tight">Aprendizado</h1>
      <p className="text-sm text-muted-foreground">
        Análise de conversas e melhoria contínua — Sprint 5.
      </p>
    </div>
  );
}
