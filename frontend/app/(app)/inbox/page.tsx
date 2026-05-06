import type { Metadata } from "next";

export const metadata: Metadata = { title: "Inbox" };

export default function InboxPage() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold tracking-tight">Inbox</h1>
      <p className="text-sm text-muted-foreground">
        Conversas em tempo real — Sprint 3.
      </p>
    </div>
  );
}
