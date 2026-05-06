import type { Metadata } from "next";

export const metadata: Metadata = { title: "Base de conhecimento" };

export default function KnowledgePage() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold tracking-tight">Base de conhecimento</h1>
      <p className="text-sm text-muted-foreground">
        Documentos e FAQs do agente — Sprint 5.
      </p>
    </div>
  );
}
