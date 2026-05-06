"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle, CircleNotch, Trash } from "@phosphor-icons/react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useApi } from "@/lib/api";

// ---- Types ----
type LLMProvider = "openai" | "anthropic" | "google";
type WhatsAppStatus = "connected" | "disconnected" | "qr_pending";

interface LLMSettings {
  id: string;
  provider: LLMProvider;
  api_key_masked: string;
  default_model: string;
  is_active: boolean;
  updated_at: string;
}

interface WhatsAppSettings {
  id: string;
  instance_id: string;
  instance_token: string;
  has_client_token: boolean;
  phone_number: string | null;
  status: WhatsAppStatus;
  webhook_url: string;
  updated_at: string;
}

// ---- Constants ----
const PROVIDER_LABELS: Record<LLMProvider, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  google: "Google",
};

const PROVIDER_MODELS: Record<LLMProvider, string[]> = {
  openai: [
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "gpt-4o",
    "gpt-4o-mini",
    "o3",
    "o3-mini",
    "o4-mini",
    "o1",
    "o1-mini",
  ],
  anthropic: [
    "claude-opus-4-5",
    "claude-sonnet-4-5",
    "claude-haiku-4-5",
    "claude-3-7-sonnet-20250219",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
  ],
  google: [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
  ],
};

const WA_STATUS_LABELS: Record<WhatsAppStatus, string> = {
  connected: "Conectado",
  disconnected: "Desconectado",
  qr_pending: "QR Code pendente",
};

const WA_STATUS_VARIANT: Record<
  WhatsAppStatus,
  "success" | "secondary" | "warning"
> = {
  connected: "success",
  disconnected: "secondary",
  qr_pending: "warning",
};

// ---- LLM Section ----
function LLMSection() {
  const { request } = useApi();
  const qc = useQueryClient();
  const [provider, setProvider] = useState<LLMProvider>("openai");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState(PROVIDER_MODELS.openai[0]);
  const [saved, setSaved] = useState(false);

  const { data: creds = [], isLoading } = useQuery<LLMSettings[]>({
    queryKey: ["settings", "llm"],
    queryFn: () => request("/api/v1/settings/llm"),
  });

  const save = useMutation({
    mutationFn: () =>
      request("/api/v1/settings/llm", {
        method: "POST",
        body: JSON.stringify({ provider, api_key: apiKey, default_model: model }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["settings", "llm"] });
      setApiKey("");
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    },
  });

  const remove = useMutation({
    mutationFn: (id: string) =>
      request(`/api/v1/settings/llm/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settings", "llm"] }),
  });

  const handleProviderChange = (p: LLMProvider) => {
    setProvider(p);
    setModel(PROVIDER_MODELS[p][0]);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Provedor de LLM</CardTitle>
        <CardDescription>
          Conecte a chave de API do modelo que o agente usará para gerar
          respostas
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-6">
        {/* Existing credentials */}
        {isLoading ? (
          <CircleNotch className="h-4 w-4 animate-spin text-muted-foreground" />
        ) : creds.length > 0 ? (
          <div className="flex flex-col gap-2">
            {creds.map((c) => (
              <div
                key={c.id}
                className="flex items-center justify-between rounded-lg border border-border px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <div>
                    <p className="text-sm font-medium">
                      {PROVIDER_LABELS[c.provider]}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {c.api_key_masked} · {c.default_model}
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => remove.mutate(c.id)}
                  disabled={remove.isPending}
                >
                  <Trash className="h-4 w-4 text-muted-foreground" />
                </Button>
              </div>
            ))}
          </div>
        ) : null}

        {/* Add form */}
        <div className="flex flex-col gap-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <Label>Provedor</Label>
              <select
                value={provider}
                onChange={(e) =>
                  handleProviderChange(e.target.value as LLMProvider)
                }
                className="flex h-9 w-full rounded-lg border border-input bg-background px-3 py-1 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {(Object.keys(PROVIDER_LABELS) as LLMProvider[]).map((p) => (
                  <option key={p} value={p}>
                    {PROVIDER_LABELS[p]}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <Label>Modelo padrão</Label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="flex h-9 w-full rounded-lg border border-input bg-background px-3 py-1 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {PROVIDER_MODELS[provider].map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>Chave de API</Label>
            <Input
              type="password"
              placeholder="sk-..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
          </div>

          <div className="flex items-center gap-3">
            <Button
              onClick={() => save.mutate()}
              disabled={save.isPending || !apiKey.trim()}
            >
              {save.isPending && (
                <CircleNotch className="mr-2 h-4 w-4 animate-spin" />
              )}
              Salvar
            </Button>
            {saved && (
              <span className="flex items-center gap-1 text-sm text-green-600">
                <CheckCircle className="h-4 w-4" />
                Salvo
              </span>
            )}
            {save.isError && (
              <span className="text-sm text-destructive">
                {(save.error as Error).message}
              </span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ---- WhatsApp Section ----
function WhatsAppSection() {
  const { request } = useApi();
  const qc = useQueryClient();
  const [instanceId, setInstanceId] = useState("");
  const [instanceToken, setInstanceToken] = useState("");
  const [clientToken, setClientToken] = useState("");
  const [phone, setPhone] = useState("");
  const [saved, setSaved] = useState(false);

  const { data: wa, isLoading } = useQuery<WhatsAppSettings | null>({
    queryKey: ["settings", "whatsapp"],
    queryFn: () => request("/api/v1/settings/whatsapp"),
  });

  useEffect(() => {
    if (!wa) return;
    setInstanceId(wa.instance_id);
    setInstanceToken(wa.instance_token ?? "");
    setPhone(wa.phone_number ?? "");
  }, [wa]);

  const save = useMutation({
    mutationFn: () =>
      request("/api/v1/settings/whatsapp", {
        method: "POST",
        body: JSON.stringify({
          instance_id: instanceId,
          instance_token: instanceToken,
          client_token: clientToken,
          phone_number: phone || null,
        }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["settings", "whatsapp"] });
      setClientToken("");
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    },
  });

  const syncWebhook = useMutation({
    mutationFn: () =>
      request<{ success: boolean; detail: string }>(
        "/api/v1/settings/whatsapp/sync-webhook",
        { method: "POST" },
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settings", "whatsapp"] }),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>WhatsApp (Z-API)</CardTitle>
        <CardDescription>
          Configure sua instância Z-API para o agente enviar e receber mensagens
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-6">
        {/* Current status */}
        {isLoading ? (
          <CircleNotch className="h-4 w-4 animate-spin text-muted-foreground" />
        ) : wa ? (
          <div className="flex items-center justify-between rounded-lg border border-border px-4 py-3">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <div>
                <p className="text-sm font-medium">
                  Instância: {wa.instance_id}
                </p>
                <p className="text-xs text-muted-foreground">
                  {wa.phone_number ?? "Número não informado"}
                </p>
              </div>
            </div>
            <Badge variant={WA_STATUS_VARIANT[wa.status]}>
              {WA_STATUS_LABELS[wa.status]}
            </Badge>
          </div>
        ) : null}

        {/* Form */}
        <div className="flex flex-col gap-4">
          {wa?.webhook_url && (
            <div className="flex flex-col gap-1.5">
              <Label>Webhook URL (Z-API)</Label>
              <div className="flex gap-2">
                <Input readOnly value={wa.webhook_url} />
                <Button
                  type="button"
                  variant="outline"
                  onClick={async () => {
                    await navigator.clipboard.writeText(wa.webhook_url);
                  }}
                >
                  Copiar
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => syncWebhook.mutate()}
                  disabled={syncWebhook.isPending}
                >
                  {syncWebhook.isPending && (
                    <CircleNotch className="mr-2 h-4 w-4 animate-spin" />
                  )}
                  Sincronizar na Z-API
                </Button>
              </div>
              {(wa.webhook_url.includes("localhost") ||
                wa.webhook_url.includes("127.0.0.1")) && (
                <p className="text-xs text-amber-600">
                  URL local detectada. Configure `API_PUBLIC_BASE_URL` com domínio público HTTPS.
                </p>
              )}
              {syncWebhook.isError && (
                <p className="text-xs text-destructive">
                  {(syncWebhook.error as Error).message}
                </p>
              )}
              {syncWebhook.isSuccess && (
                <p className="text-xs text-green-600">
                  Webhook sincronizado na Z-API.
                </p>
              )}
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <Label>Instance ID</Label>
              <Input
                placeholder="ex: 3D123ABC..."
                value={instanceId}
                onChange={(e) => setInstanceId(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Número (opcional)</Label>
              <Input
                placeholder="+55 11 99999-9999"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>Instance Token</Label>
            <Input
              placeholder="Token público da instância"
              value={instanceToken}
              onChange={(e) => setInstanceToken(e.target.value)}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>Client Token</Label>
            <Input
              type="password"
              placeholder={
                wa?.has_client_token
                  ? "Já configurado (preencha apenas para trocar)"
                  : "Token secreto do cliente"
              }
              value={clientToken}
              onChange={(e) => setClientToken(e.target.value)}
            />
          </div>

          <div className="flex items-center gap-3">
            <Button
              onClick={() => save.mutate()}
              disabled={
                save.isPending ||
                !instanceId.trim() ||
                !instanceToken.trim() ||
                (!wa && !clientToken.trim())
              }
            >
              {save.isPending && (
                <CircleNotch className="mr-2 h-4 w-4 animate-spin" />
              )}
              {wa ? "Atualizar" : "Conectar"}
            </Button>
            {saved && (
              <span className="flex items-center gap-1 text-sm text-green-600">
                <CheckCircle className="h-4 w-4" />
                Salvo
              </span>
            )}
            {save.isError && (
              <span className="text-sm text-destructive">
                {(save.error as Error).message}
              </span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ---- Page ----
type Tab = "llm" | "whatsapp";

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>("llm");

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Configurações</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Configure as integrações do seu agente
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-border">
        {(["llm", "whatsapp"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 pb-3 pt-2 text-sm font-medium transition-colors ${
              tab === t
                ? "border-b-2 border-foreground text-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {t === "llm" ? "LLM" : "WhatsApp"}
          </button>
        ))}
      </div>

      {tab === "llm" && <LLMSection />}
      {tab === "whatsapp" && <WhatsAppSection />}
    </div>
  );
}
