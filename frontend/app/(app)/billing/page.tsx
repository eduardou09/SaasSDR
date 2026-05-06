import type { Metadata } from "next";

export const metadata: Metadata = { title: "Plano" };

export default function BillingPage() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold tracking-tight">Plano</h1>
      <p className="text-sm text-muted-foreground">
        Gerenciamento de assinatura — Sprint 7.
      </p>
    </div>
  );
}
