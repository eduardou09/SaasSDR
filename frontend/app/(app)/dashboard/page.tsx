"use client";

import Link from "next/link";
import { Robot, GearSix, Lightning } from "@phosphor-icons/react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";


const metrics = [
  { label: "Conversas (7d)", value: "—" },
  { label: "Taxa de qualificação", value: "—" },
  { label: "Leads qualificados", value: "—" },
  { label: "Custo por lead", value: "—" },
];

const setup = [
  {
    step: "1",
    icon: GearSix,
    title: "Configure o LLM",
    description: "Conecte sua chave da OpenAI, Anthropic ou Google",
    href: "/settings",
    label: "Configurar",
  },
  {
    step: "2",
    icon: Lightning,
    title: "Conecte o WhatsApp",
    description: "Configure sua instância Z-API para envio de mensagens",
    href: "/settings",
    label: "Configurar",
  },
  {
    step: "3",
    icon: Robot,
    title: "Crie um agente",
    description: "Defina prompt, tom e critérios de qualificação do SDR",
    href: "/agents/new",
    label: "Criar agente",
  },
];

export default function DashboardPage() {
  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Configure o Convo em 3 passos e ative seu agente SDR
        </p>
      </div>

      {/* Setup steps */}
      <div className="grid gap-4 sm:grid-cols-3">
        {setup.map(({ step, icon: Icon, title, description, href, label }) => (
          <Card key={step}>
            <CardHeader className="pb-3">
              <div className="mb-1 flex h-8 w-8 items-center justify-center rounded-lg bg-secondary text-xs font-bold">
                {step}
              </div>
              <CardTitle className="text-base">{title}</CardTitle>
              <CardDescription>{description}</CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild size="sm" variant="outline">
                <Link href={href}>{label}</Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Metrics */}
      <div>
        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">
          Métricas — disponíveis após ativar um agente
        </p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {metrics.map(({ label, value }) => (
            <div
              key={label}
              className="rounded-xl border border-border bg-card p-5"
            >
              <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                {label}
              </p>
              <p className="mt-2 text-3xl font-bold">{value}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
