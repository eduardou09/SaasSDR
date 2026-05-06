"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, CircleNotch } from "@phosphor-icons/react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useApi } from "@/lib/api";

type AgentStatus = "draft" | "training" | "active" | "paused";

interface Agent {
  id: string;
  name: string;
  status: AgentStatus;
  system_prompt: string | null;
  qualification_schema: Record<string, unknown> | null;
  tone: string | null;
  language: string;
  llm_provider: string | null;
  llm_model: string | null;
  temperature: number;
}

interface AgentLog {
  id: string;
  level: string;
  event_type: string;
  message: string;
  payload: Record<string, unknown> | null;
  created_at: string;
}

const PROVIDERS = [
  { value: "", label: "Herdar das configurações" },
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
  { value: "google", label: "Google" },
];

export default function EditAgentPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { request } = useApi();
  const agentId = params.id;

  const { data, isLoading } = useQuery<Agent>({
    queryKey: ["agent", agentId],
    queryFn: () => request(`/api/v1/agents/${agentId}`),
    enabled: !!agentId,
  });

  const { data: logs = [], refetch: refetchLogs, isFetching: isFetchingLogs } = useQuery<
    AgentLog[]
  >({
    queryKey: ["agent-logs", agentId],
    queryFn: () => request(`/api/v1/agents/${agentId}/logs?limit=100`),
    enabled: !!agentId,
  });

  const [name, setName] = useState("");
  const [status, setStatus] = useState<AgentStatus>("draft");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [tone, setTone] = useState("");
  const [language, setLanguage] = useState("pt-BR");
  const [provider, setProvider] = useState("");
  const [model, setModel] = useState("");
  const [temperature, setTemperature] = useState(0.7);

  useEffect(() => {
    if (!data) return;
    setName(data.name);
    setStatus(data.status);
    setSystemPrompt(data.system_prompt ?? "");
    setTone(data.tone ?? "");
    setLanguage(data.language);
    setProvider(data.llm_provider ?? "");
    setModel(data.llm_model ?? "");
    setTemperature(data.temperature ?? 0.7);
  }, [data]);

  const update = useMutation({
    mutationFn: () =>
      request(`/api/v1/agents/${agentId}`, {
        method: "PUT",
        body: JSON.stringify({
          name,
          status,
          system_prompt: systemPrompt || undefined,
          tone: tone || undefined,
          language,
          llm_provider: provider || undefined,
          llm_model: model || undefined,
          temperature,
        }),
      }),
    onSuccess: () => router.push("/agents"),
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <Button asChild variant="ghost" size="icon">
          <Link href="/agents">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Editar agente</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Ajuste comportamento, prompt, treinamento e configurações do modelo
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <CircleNotch className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Configurações</CardTitle>
            <CardDescription>Alterações são aplicadas imediatamente</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <Label>Nome</Label>
                <Input value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label>Status</Label>
                <select value={status} onChange={(e) => setStatus(e.target.value as AgentStatus)} className="h-9 rounded-lg border border-input bg-background px-3 text-sm">
                  <option value="draft">Rascunho</option>
                  <option value="training">Treinando</option>
                  <option value="active">Ativo</option>
                  <option value="paused">Pausado</option>
                </select>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <Label>Tom</Label>
                <Input value={tone} onChange={(e) => setTone(e.target.value)} placeholder="professional/friendly..." />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label>Idioma</Label>
                <select value={language} onChange={(e) => setLanguage(e.target.value)} className="h-9 rounded-lg border border-input bg-background px-3 text-sm">
                  <option value="pt-BR">Português (BR)</option>
                  <option value="en-US">English (US)</option>
                  <option value="es">Español</option>
                </select>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <Label>Provedor LLM</Label>
                <select value={provider} onChange={(e) => setProvider(e.target.value)} className="h-9 rounded-lg border border-input bg-background px-3 text-sm">
                  {PROVIDERS.map((p) => (
                    <option key={p.value} value={p.value}>
                      {p.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex flex-col gap-1.5">
                <Label>Modelo LLM</Label>
                <Input value={model} onChange={(e) => setModel(e.target.value)} placeholder="ex: gpt-4.1-mini" />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <Label>Temperatura</Label>
                <span className="text-sm text-muted-foreground">{temperature.toFixed(1)}</span>
              </div>
              <input type="range" min={0} max={1} step={0.1} value={temperature} onChange={(e) => setTemperature(Number(e.target.value))} />
            </div>

            <div className="flex flex-col gap-1.5">
              <Label>System prompt</Label>
              <textarea rows={18} value={systemPrompt} onChange={(e) => setSystemPrompt(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
            </div>

            <div className="flex items-center gap-3">
              <Button onClick={() => update.mutate()} disabled={update.isPending || !name.trim()}>
                {update.isPending && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}
                Salvar alterações
              </Button>
              <Button asChild variant="secondary">
                <Link href={`/agents/${agentId}/test`}>Abrir simulador</Link>
              </Button>
              <Button asChild variant="outline">
                <Link href="/agents">Cancelar</Link>
              </Button>
              {update.isError && (
                <span className="text-sm text-destructive">
                  {(update.error as Error).message}
                </span>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {!isLoading && (
        <Card>
          <CardHeader>
            <CardTitle>Sessão de Treinamento</CardTitle>
            <CardDescription>
              Estrutura de qualificação e contexto de treino do agente
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3">
            <div className="text-sm text-muted-foreground">
              O conteúdo abaixo representa o schema de qualificação salvo para este agente.
            </div>
            <pre className="max-h-[320px] overflow-auto rounded bg-muted p-3 text-xs">
              {JSON.stringify(data?.qualification_schema ?? {}, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      {!isLoading && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Logs do agente</CardTitle>
                <CardDescription>Eventos, erros e mensagens de simulação</CardDescription>
              </div>
              <Button variant="outline" onClick={() => refetchLogs()} disabled={isFetchingLogs}>
                {isFetchingLogs && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}
                Atualizar
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="max-h-[420px] overflow-y-auto rounded-lg border border-border">
              {logs.length === 0 ? (
                <p className="p-4 text-sm text-muted-foreground">Nenhum log encontrado.</p>
              ) : (
                <div className="divide-y divide-border">
                  {logs.map((log) => (
                    <div key={log.id} className="space-y-1 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                          {log.event_type}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {new Date(log.created_at).toLocaleString("pt-BR")}
                        </span>
                      </div>
                      <p className="text-sm">{log.message}</p>
                      {log.payload && (
                        <pre className="overflow-x-auto rounded bg-muted p-2 text-xs">
                          {JSON.stringify(log.payload, null, 2)}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
