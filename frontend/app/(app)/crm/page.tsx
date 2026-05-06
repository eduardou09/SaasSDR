import type { Metadata } from "next";

export const metadata: Metadata = { title: "CRM" };

export default function CRMPage() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold tracking-tight">CRM</h1>
      <p className="text-sm text-muted-foreground">
        Gestão de leads e pipeline — Sprint 4.
      </p>
    </div>
  );
}
