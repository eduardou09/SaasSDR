"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, CircleNotch, PaperPlaneRight } from "@phosphor-icons/react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useApi } from "@/lib/api";

type ChatMessage = { role: "user" | "assistant"; content: string };

interface Agent {
  id: string;
  name: string;
  status: "draft" | "training" | "active" | "paused";
}

export default function AgentTestPage() {
  const params = useParams<{ id: string }>();
  const { request } = useApi();
  const agentId = params.id;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");

  const { data: agent } = useQuery<Agent>({
    queryKey: ["agent", agentId],
    queryFn: () => request(`/api/v1/agents/${agentId}`),
    enabled: !!agentId,
  });

  const simulate = useMutation({
    mutationFn: (text: string) =>
      request<{ reply: string; provider: string; model: string }>(
        `/api/v1/agents/${agentId}/simulate`,
        {
          method: "POST",
          body: JSON.stringify({ message: text, history: messages }),
        },
      ),
    onSuccess: (data, text) => {
      setMessages((prev) => [
        ...prev,
        { role: "user", content: text },
        { role: "assistant", content: data.reply },
      ]);
      setInput("");
    },
  });

  const onSend = () => {
    const text = input.trim();
    if (!text || simulate.isPending) return;
    simulate.mutate(text);
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <Button asChild variant="ghost" size="icon">
          <Link href="/agents">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Teste do agente</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {agent ? `${agent.name} · status: ${agent.status}` : "Carregando agente..."}
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Simulador</CardTitle>
          <CardDescription>Conversa de teste sem enviar para WhatsApp real</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="max-h-[480px] min-h-[320px] space-y-3 overflow-y-auto rounded-lg border border-border p-4">
            {messages.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                Digite uma mensagem para iniciar o teste.
              </p>
            ) : (
              messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                    msg.role === "user"
                      ? "ml-auto bg-foreground text-background"
                      : "bg-muted text-foreground"
                  }`}
                >
                  {msg.content}
                </div>
              ))
            )}
            {simulate.isPending && (
              <div className="max-w-[85%] rounded-lg bg-muted px-3 py-2 text-sm text-foreground">
                <CircleNotch className="mr-2 inline h-4 w-4 animate-spin" />
                Agente pensando...
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              rows={2}
              placeholder="Digite a mensagem do lead..."
              className="flex-1 resize-none rounded-lg border border-input bg-background px-3 py-2 text-sm"
            />
            <Button onClick={onSend} disabled={simulate.isPending || !input.trim()}>
              <PaperPlaneRight className="h-4 w-4" />
            </Button>
          </div>

          {simulate.isError && (
            <p className="text-sm text-destructive">
              {(simulate.error as Error).message}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
