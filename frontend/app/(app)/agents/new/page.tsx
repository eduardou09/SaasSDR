"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { ArrowLeft, CircleNotch } from "@phosphor-icons/react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useApi } from "@/lib/api";

const PROVIDERS = [
  { value: "", label: "Herdar das configurações" },
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
  { value: "google", label: "Google" },
];

const MODELS: Record<string, string[]> = {
  openai: ["gpt-4.1", "gpt-4.1-mini", "gpt-4o", "gpt-4o-mini", "o3", "o4-mini"],
  anthropic: ["claude-sonnet-4-5", "claude-haiku-4-5", "claude-opus-4-5"],
  google: ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"],
};

const TONES = [
  { value: "professional", label: "Profissional" },
  { value: "friendly", label: "Amigável" },
  { value: "assertive", label: "Assertivo" },
  { value: "consultative", label: "Consultivo" },
];

function buildQualificationSchema(rawQuestions: string) {
  const lines = rawQuestions
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const fields = lines.map((question, idx) => ({
    key: `q_${idx + 1}`,
    label: question.replace(/^[\-\d\.\)\s]+/, ""),
    type: "string",
    required: true,
  }));

  return { fields };
}

export default function NewAgentPage() {
  const router = useRouter();
  const { request } = useApi();

  const [name, setName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [companyDescription, setCompanyDescription] = useState("");
  const [icp, setIcp] = useState("");
  const [qualificationQuestions, setQualificationQuestions] = useState("");
  const [qualificationCriteria, setQualificationCriteria] = useState("");
  const [objections, setObjections] = useState("");
  const [forbiddenTerms, setForbiddenTerms] = useState("");
  const [nextStep, setNextStep] = useState("");
  const [agentIdentity, setAgentIdentity] = useState("");
  const [personalityTone, setPersonalityTone] = useState("");
  const [companyContext, setCompanyContext] = useState("");
  const [audiencePersonas, setAudiencePersonas] = useState("");
  const [openingScript, setOpeningScript] = useState("");
  const [qualificationFlowGood, setQualificationFlowGood] = useState("");
  const [scenariosScripts, setScenariosScripts] = useState("");
  const [faqScripts, setFaqScripts] = useState("");
  const [objectionsScripts, setObjectionsScripts] = useState("");
  const [handoffRules, setHandoffRules] = useState("");
  const [technicalFeatures, setTechnicalFeatures] = useState("");
  const [alwaysRules, setAlwaysRules] = useState("");
  const [neverRules, setNeverRules] = useState("");
  const [specialCases, setSpecialCases] = useState("");
  const [formattingStyle, setFormattingStyle] = useState("");
  const [successExamples, setSuccessExamples] = useState("");
  const [problematicExamples, setProblematicExamples] = useState("");
  const [tone, setTone] = useState("professional");
  const [language, setLanguage] = useState("pt-BR");

  const [provider, setProvider] = useState("");
  const [model, setModel] = useState("");
  const [temperature, setTemperature] = useState(0.7);

  const [generatedPrompt, setGeneratedPrompt] = useState("");

  const generatePrompt = useMutation({
    mutationFn: () =>
      request<{ prompt_xml: string; provider: string; model: string }>(
        "/api/v1/agents/generate-prompt",
        {
          method: "POST",
          body: JSON.stringify({
            company_name: companyName,
            company_description: companyDescription,
            icp,
            qualification_questions: qualificationQuestions,
            qualification_criteria: qualificationCriteria,
            objections,
            tone,
            language,
            forbidden_terms: forbiddenTerms || null,
            next_step: nextStep,
            agent_identity: agentIdentity || null,
            personality_tone: personalityTone || null,
            company_context: companyContext || null,
            audience_personas: audiencePersonas || null,
            opening_script: openingScript || null,
            qualification_flow_good: qualificationFlowGood || null,
            scenarios_scripts: scenariosScripts || null,
            faq_scripts: faqScripts || null,
            objections_scripts: objectionsScripts || null,
            handoff_rules: handoffRules || null,
            technical_features: technicalFeatures || null,
            always_rules: alwaysRules || null,
            never_rules: neverRules || null,
            special_cases: specialCases || null,
            formatting_style: formattingStyle || null,
            success_examples: successExamples || null,
            problematic_examples: problematicExamples || null,
            llm_provider: provider || null,
            llm_model: model || null,
          }),
        },
      ),
    onSuccess: (data) => setGeneratedPrompt(data.prompt_xml),
  });

  const create = useMutation({
    mutationFn: () =>
      request("/api/v1/agents", {
        method: "POST",
        body: JSON.stringify({
          name,
          system_prompt: generatedPrompt,
          qualification_schema: buildQualificationSchema(qualificationQuestions),
          tone,
          language,
          llm_provider: provider || undefined,
          llm_model: model || undefined,
          temperature,
        }),
      }),
    onSuccess: () => router.push("/agents"),
  });

  const handleProviderChange = (p: string) => {
    setProvider(p);
    setModel(p ? MODELS[p]?.[0] ?? "" : "");
  };

  const isFormValid =
    !!name.trim() &&
    !!companyName.trim() &&
    !!companyDescription.trim() &&
    !!icp.trim() &&
    !!qualificationQuestions.trim() &&
    !!qualificationCriteria.trim() &&
    !!objections.trim() &&
    !!nextStep.trim() &&
    !!generatedPrompt.trim();

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <Button asChild variant="ghost" size="icon">
          <Link href="/agents">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Novo agente por onboarding</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Preencha o onboarding e o sistema gera o prompt automaticamente
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Dados do agente e negócio</CardTitle>
          <CardDescription>Essas respostas geram o prompt inicial do SDR</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <Label>Nome do agente</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="ex: SDR Convo" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Nome da empresa</Label>
              <Input value={companyName} onChange={(e) => setCompanyName(e.target.value)} placeholder="ex: Convo" />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>O que sua empresa faz?</Label>
            <textarea rows={3} value={companyDescription} onChange={(e) => setCompanyDescription(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>Cliente ideal (ICP)</Label>
            <textarea rows={3} value={icp} onChange={(e) => setIcp(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>Perguntas de qualificação (uma por linha)</Label>
            <textarea rows={5} value={qualificationQuestions} onChange={(e) => setQualificationQuestions(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>Critérios de lead qualificado</Label>
            <textarea rows={3} value={qualificationCriteria} onChange={(e) => setQualificationCriteria(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>Objeções comuns e como responder</Label>
            <textarea rows={4} value={objections} onChange={(e) => setObjections(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <Label>Tom</Label>
              <select value={tone} onChange={(e) => setTone(e.target.value)} className="h-9 rounded-lg border border-input bg-background px-3 text-sm">
                {TONES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
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

          <div className="flex flex-col gap-1.5">
            <Label>Termos proibidos (opcional)</Label>
            <textarea rows={2} value={forbiddenTerms} onChange={(e) => setForbiddenTerms(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>Próximo passo após qualificação</Label>
            <textarea rows={2} value={nextStep} onChange={(e) => setNextStep(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Playbook SDR (Blocos 1 a 7)</CardTitle>
          <CardDescription>Preencha os blocos principais para treinar o agente</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="flex flex-col gap-1.5">
            <Label>Bloco 1: Identidade do agente</Label>
            <textarea rows={3} value={agentIdentity} onChange={(e) => setAgentIdentity(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" placeholder="Nome, gênero, papel/função, representa quem" />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Bloco 1: Personalidade e tom</Label>
            <textarea rows={3} value={personalityTone} onChange={(e) => setPersonalityTone(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" placeholder="Tom principal, formalidade, emojis, palavras permitidas/proibidas" />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Bloco 2: Contexto da empresa</Label>
            <textarea rows={3} value={companyContext} onChange={(e) => setCompanyContext(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" placeholder="Descrição, produtos/serviços, diferenciais, proposta de valor" />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Bloco 2: Público-alvo e personas</Label>
            <textarea rows={3} value={audiencePersonas} onChange={(e) => setAudiencePersonas(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Bloco 3: Mensagem de abertura</Label>
            <textarea rows={3} value={openingScript} onChange={(e) => setOpeningScript(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Bloco 3: Fluxo BOM de qualificação</Label>
            <textarea rows={4} value={qualificationFlowGood} onChange={(e) => setQualificationFlowGood(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Bloco 3: Cenários e scripts</Label>
            <textarea rows={4} value={scenariosScripts} onChange={(e) => setScenariosScripts(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" placeholder="Lead qualificado, indeciso, sumiu e voltou, etc." />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Bloco 3: FAQ (perguntas e respostas padrão)</Label>
            <textarea rows={4} value={faqScripts} onChange={(e) => setFaqScripts(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Bloco 3: Tratamento de objeções</Label>
            <textarea rows={4} value={objectionsScripts} onChange={(e) => setObjectionsScripts(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Bloco 4: Regras de encaminhamento para humano</Label>
            <textarea rows={3} value={handoffRules} onChange={(e) => setHandoffRules(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Bloco 5: Funcionalidades técnicas</Label>
            <textarea rows={3} value={technicalFeatures} onChange={(e) => setTechnicalFeatures(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" placeholder="Áudio, botões, vídeos, imagens, docs, links, contact card, reações" />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <Label>Bloco 6: Sempre fazer</Label>
              <textarea rows={3} value={alwaysRules} onChange={(e) => setAlwaysRules(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Bloco 6: Nunca fazer</Label>
              <textarea rows={3} value={neverRules} onChange={(e) => setNeverRules(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Bloco 6: Casos especiais</Label>
            <textarea rows={3} value={specialCases} onChange={(e) => setSpecialCases(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Bloco 6: Formatação e estilo</Label>
            <textarea rows={3} value={formattingStyle} onChange={(e) => setFormattingStyle(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Bloco 7: Conversas de sucesso (exemplos)</Label>
            <textarea rows={4} value={successExamples} onChange={(e) => setSuccessExamples(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Bloco 7: Conversas problemáticas e correções</Label>
            <textarea rows={4} value={problematicExamples} onChange={(e) => setProblematicExamples(e.target.value)} className="rounded-lg border border-input bg-background px-3 py-2 text-sm" />
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center gap-3">
        <Button onClick={() => generatePrompt.mutate()} disabled={generatePrompt.isPending}>
          {generatePrompt.isPending && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}
          Gerar prompt XML com IA
        </Button>
        {generatePrompt.isError && (
          <span className="text-sm text-destructive">
            {(generatePrompt.error as Error).message}
          </span>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>LLM do agente</CardTitle>
          <CardDescription>Opcional: sobrescreve a configuração global do tenant</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <Label>Provedor</Label>
              <select value={provider} onChange={(e) => handleProviderChange(e.target.value)} className="h-9 rounded-lg border border-input bg-background px-3 text-sm">
                {PROVIDERS.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>
            {provider && (
              <div className="flex flex-col gap-1.5">
                <Label>Modelo</Label>
                <select value={model} onChange={(e) => setModel(e.target.value)} className="h-9 rounded-lg border border-input bg-background px-3 text-sm">
                  {MODELS[provider]?.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between">
              <Label>Temperatura</Label>
              <span className="text-sm text-muted-foreground">{temperature.toFixed(1)}</span>
            </div>
            <input type="range" min={0} max={1} step={0.1} value={temperature} onChange={(e) => setTemperature(Number(e.target.value))} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Preview do prompt gerado</CardTitle>
          <CardDescription>Esse texto será salvo como system prompt inicial do agente</CardDescription>
        </CardHeader>
        <CardContent>
          <textarea value={generatedPrompt} readOnly rows={18} className="w-full rounded-lg border border-input bg-muted/20 px-3 py-2 text-xs" />
        </CardContent>
      </Card>

      <div className="flex items-center gap-3">
        <Button onClick={() => create.mutate()} disabled={create.isPending || !isFormValid}>
          {create.isPending && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}
          Criar agente com onboarding
        </Button>
        <Button asChild variant="outline">
          <Link href="/agents">Cancelar</Link>
        </Button>
        {create.isError && <span className="text-sm text-destructive">{(create.error as Error).message}</span>}
      </div>
    </div>
  );
}
