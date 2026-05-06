"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Robot,
  CircleNotch,
  Plus,
  Trash,
  PencilSimple,
  Play,
  Pause,
  ChatCircle,
} from "@phosphor-icons/react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useApi } from "@/lib/api";

type AgentStatus = "draft" | "training" | "active" | "paused";

interface Agent {
  id: string;
  name: string;
  status: AgentStatus;
  llm_provider: string | null;
  llm_model: string | null;
  language: string;
  created_at: string;
}

interface PaginatedAgents {
  items: Agent[];
  total: number;
}

const STATUS_LABELS: Record<AgentStatus, string> = {
  draft: "Rascunho",
  training: "Treinando",
  active: "Ativo",
  paused: "Pausado",
};

const STATUS_VARIANT: Record<
  AgentStatus,
  "secondary" | "outline" | "success" | "warning"
> = {
  draft: "secondary",
  training: "outline",
  active: "success",
  paused: "warning",
};

export default function AgentsPage() {
  const { request } = useApi();
  const qc = useQueryClient();

  const { data, isLoading } = useQuery<PaginatedAgents>({
    queryKey: ["agents"],
    queryFn: () => request("/api/v1/agents"),
  });

  const remove = useMutation({
    mutationFn: (id: string) =>
      request(`/api/v1/agents/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agents"] }),
  });

  const toggleStatus = useMutation({
    mutationFn: (agent: Agent) =>
      request(`/api/v1/agents/${agent.id}`, {
        method: "PUT",
        body: JSON.stringify({
          status: agent.status === "active" ? "paused" : "active",
        }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agents"] }),
  });

  const agents = data?.items ?? [];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Agentes</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {data?.total ?? 0} agente{data?.total !== 1 ? "s" : ""} configurado
            {data?.total !== 1 ? "s" : ""}
          </p>
        </div>
        <Button asChild>
          <Link href="/agents/new">
            <Plus className="mr-2 h-4 w-4" />
            Novo agente
          </Link>
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <CircleNotch className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : agents.length === 0 ? (
        <div className="flex flex-col items-center gap-4 rounded-xl border border-dashed border-border py-16 text-center">
          <Robot className="h-10 w-10 text-muted-foreground" />
          <div>
            <p className="font-medium">Nenhum agente criado</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Crie seu primeiro agente SDR para começar
            </p>
          </div>
          <Button asChild>
            <Link href="/agents/new">
              <Plus className="mr-2 h-4 w-4" />
              Criar agente
            </Link>
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {agents.map((agent) => (
            <Card key={agent.id} className="relative">
              <Link href={`/agents/${agent.id}`} className="absolute inset-0 z-0" aria-label={`Abrir agente ${agent.name}`} />
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-base">{agent.name}</CardTitle>
                  <Badge variant={STATUS_VARIANT[agent.status]}>
                    {STATUS_LABELS[agent.status]}
                  </Badge>
                </div>
                <CardDescription>
                  {agent.llm_provider
                    ? `${agent.llm_provider} · ${agent.llm_model ?? "—"}`
                    : "LLM não configurado"}
                </CardDescription>
              </CardHeader>
              <CardContent className="relative z-10 flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  {agent.language}
                </span>
                <div className="flex items-center gap-1">
                  <Button asChild variant="ghost" size="icon">
                    <Link href={`/agents/${agent.id}/test`}>
                      <ChatCircle className="h-4 w-4 text-muted-foreground" />
                    </Link>
                  </Button>
                  <Button asChild variant="ghost" size="icon">
                    <Link href={`/agents/${agent.id}`}>
                      <PencilSimple className="h-4 w-4 text-muted-foreground" />
                    </Link>
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => toggleStatus.mutate(agent)}
                    disabled={toggleStatus.isPending}
                  >
                    {agent.status === "active" ? (
                      <Pause className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <Play className="h-4 w-4 text-muted-foreground" />
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => remove.mutate(agent.id)}
                    disabled={remove.isPending}
                  >
                    <Trash className="h-4 w-4 text-muted-foreground" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
