"""CRUD de agentes + geração de prompt XML via LLM do tenant."""

import logging
import uuid
from typing import Annotated

import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import func, select

from app.core.crypto import decrypt
from app.core.db import TenantDB
from app.models.agent import Agent
from app.models.agent_log import AgentEventLog
from app.models.credentials import LLMCredentials
from app.schemas.agent import (
    AgentLogResponse,
    AgentSimulateRequest,
    AgentSimulateResponse,
    AgentCreate,
    AgentResponse,
    AgentUpdate,
    GeneratePromptRequest,
    GeneratePromptResponse,
)
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/agents", tags=["agents"])
logger = logging.getLogger(__name__)


async def _log_agent_event(
    db: TenantDB,
    *,
    tenant_id: uuid.UUID,
    agent_id: uuid.UUID,
    level: str,
    event_type: str,
    message: str,
    payload: dict | None = None,
) -> None:
    try:
        log_item = AgentEventLog(
            tenant_id=tenant_id,
            agent_id=agent_id,
            level=level,
            event_type=event_type,
            message=message,
            payload=payload,
        )
        db.add(log_item)
        await db.flush()
    except Exception:
        logger.exception("Falha ao registrar log do agente")


PROMPT_SPECIALIST_SYSTEM = """
Você é um especialista em engenharia de prompts para SDR de WhatsApp.
Sua saída DEVE ser estritamente XML válido, sem markdown e sem texto fora do XML.
Formato obrigatório:
<agent_prompt>
  <identity>...</identity>
  <objective>...</objective>
  <tone>...</tone>
  <language>...</language>
  <qualification_questions>
    <question>...</question>
  </qualification_questions>
  <qualification_criteria>...</qualification_criteria>
  <objection_handling>...</objection_handling>
  <forbidden_terms>...</forbidden_terms>
  <next_step>...</next_step>
  <handoff>...</handoff>
  <faq>...</faq>
  <objections>...</objections>
  <style_examples>...</style_examples>
  <rules>
    <rule>...</rule>
  </rules>
</agent_prompt>
""".strip()


def _build_user_prompt(data: GeneratePromptRequest) -> str:
    raw = f"""
Crie um prompt de SDR em XML usando estes dados:

Empresa: {data.company_name}
Descrição: {data.company_description}
ICP: {data.icp}
Perguntas de qualificação:
{data.qualification_questions}
Critérios de qualificação:
{data.qualification_criteria}
Objeções:
{data.objections}
Tom: {data.tone}
Idioma: {data.language}
Termos proibidos: {data.forbidden_terms or "Nenhum"}
Próximo passo: {data.next_step}

Bloco 1 - Identidade do Agente:
{data.agent_identity or "não informado"}

Personalidade e Tom:
{data.personality_tone or "não informado"}

Bloco 2 - Contexto da Empresa:
{data.company_context or "não informado"}

Público-alvo e personas:
{data.audience_personas or "não informado"}

Bloco 3 - Fluxo e Scripts:
Mensagem de abertura:
{data.opening_script or "não informado"}
Fluxo bom de qualificação:
{data.qualification_flow_good or "não informado"}
Cenários e scripts:
{data.scenarios_scripts or "não informado"}
FAQ:
{data.faq_scripts or "não informado"}
Objeções:
{data.objections_scripts or "não informado"}

Bloco 4 - Encaminhamento para humano:
{data.handoff_rules or "não informado"}

Bloco 5 - Funcionalidades técnicas (áudio, botões, mídia, links, reações):
{data.technical_features or "não informado"}

Bloco 6 - Regras e comportamentos:
Sempre fazer:
{data.always_rules or "não informado"}
Nunca fazer:
{data.never_rules or "não informado"}
Casos especiais:
{data.special_cases or "não informado"}
Formatação/estilo:
{data.formatting_style or "não informado"}

Bloco 7 - Exemplos reais:
Conversas de sucesso:
{data.success_examples or "não informado"}
Conversas problemáticas e correção:
{data.problematic_examples or "não informado"}
""".strip()
    # Remove surrogates/caracteres inválidos que podem quebrar encode em clientes HTTP.
    return raw.encode("utf-8", errors="replace").decode("utf-8")


def _sanitize_api_key(value: str) -> str:
    # Remove espaços invisíveis comuns em copy/paste.
    cleaned = (
        value.replace("\u200b", "")
        .replace("\u200c", "")
        .replace("\u200d", "")
        .replace("\ufeff", "")
        .strip()
    )
    try:
        cleaned.encode("ascii")
    except UnicodeEncodeError as e:
        raise HTTPException(
            status_code=400,
            detail="API key contém caracteres inválidos. Cole novamente a chave sem espaços extras.",
        ) from e
    return cleaned


async def _call_openai(api_key: str, model: str, user_prompt: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "temperature": 0.2,
                    "messages": [
                        {"role": "system", "content": PROMPT_SPECIALIST_SYSTEM},
                        {"role": "user", "content": user_prompt},
                    ],
                },
            )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Falha de rede OpenAI: {e}") from e
    if res.status_code >= 400:
        raise HTTPException(status_code=400, detail=f"Falha OpenAI: {res.text}")
    data = res.json()
    return data["choices"][0]["message"]["content"].strip()


async def _call_anthropic(api_key: str, model: str, user_prompt: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": model,
                    "max_tokens": 2000,
                    "temperature": 0.2,
                    "system": PROMPT_SPECIALIST_SYSTEM,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
            )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Falha de rede Anthropic: {e}") from e
    if res.status_code >= 400:
        raise HTTPException(status_code=400, detail=f"Falha Anthropic: {res.text}")
    data = res.json()
    parts = data.get("content", [])
    texts = [p.get("text", "") for p in parts if p.get("type") == "text"]
    return "\n".join(texts).strip()


async def _call_google(api_key: str, model: str, user_prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.post(
                url,
                json={
                    "generationConfig": {"temperature": 0.2},
                    "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                    "systemInstruction": {"parts": [{"text": PROMPT_SPECIALIST_SYSTEM}]},
                },
            )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Falha de rede Google: {e}") from e
    if res.status_code >= 400:
        raise HTTPException(status_code=400, detail=f"Falha Google: {res.text}")
    data = res.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise HTTPException(status_code=400, detail="Google não retornou conteúdo")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts if isinstance(p, dict)).strip()
    return text


async def _chat_openai(
    api_key: str, model: str, system_prompt: str, history: list[dict[str, str]]
) -> str:
    payload_messages = [{"role": "system", "content": system_prompt}] + history
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": model, "temperature": 0.4, "messages": payload_messages},
            )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Falha de rede OpenAI: {e}") from e
    if res.status_code >= 400:
        raise HTTPException(status_code=400, detail=f"Falha OpenAI: {res.text}")
    return res.json()["choices"][0]["message"]["content"].strip()


async def _chat_anthropic(
    api_key: str, model: str, system_prompt: str, history: list[dict[str, str]]
) -> str:
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
                json={
                    "model": model,
                    "max_tokens": 2000,
                    "temperature": 0.4,
                    "system": system_prompt,
                    "messages": history,
                },
            )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Falha de rede Anthropic: {e}") from e
    if res.status_code >= 400:
        raise HTTPException(status_code=400, detail=f"Falha Anthropic: {res.text}")
    parts = res.json().get("content", [])
    return "\n".join(p.get("text", "") for p in parts if p.get("type") == "text").strip()


async def _chat_google(
    api_key: str, model: str, system_prompt: str, history: list[dict[str, str]]
) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.post(
                url,
                json={
                    "generationConfig": {"temperature": 0.4},
                    "contents": contents,
                    "systemInstruction": {"parts": [{"text": system_prompt}]},
                },
            )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Falha de rede Google: {e}") from e
    if res.status_code >= 400:
        raise HTTPException(status_code=400, detail=f"Falha Google: {res.text}")
    candidates = res.json().get("candidates", [])
    if not candidates:
        raise HTTPException(status_code=400, detail="Google não retornou conteúdo")
    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts if isinstance(p, dict)).strip()


@router.post("/generate-prompt", response_model=GeneratePromptResponse)
async def generate_prompt(
    body: GeneratePromptRequest, request: Request, db: TenantDB
) -> GeneratePromptResponse:
    try:
        tid = request.state.tenant_id
        creds = (
            await db.execute(
                select(LLMCredentials)
                .where(LLMCredentials.tenant_id == tid, LLMCredentials.is_active.is_(True))
                .order_by(LLMCredentials.updated_at.desc())
            )
        ).scalars().all()
        if not creds:
            raise HTTPException(status_code=400, detail="Nenhuma credencial LLM ativa encontrada")

        selected = None
        if body.llm_provider:
            selected = next((c for c in creds if c.provider.value == body.llm_provider), None)
            if not selected:
                raise HTTPException(
                    status_code=400,
                    detail=f"Credencial do provider '{body.llm_provider}' não encontrada",
                )
        else:
            selected = creds[0]

        model = body.llm_model or selected.default_model
        try:
            api_key = _sanitize_api_key(decrypt(selected.api_key_encrypted))
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail="Não foi possível ler a API key do provedor. Re-salve a credencial em Configurações > LLM.",
            ) from e
        user_prompt = _build_user_prompt(body)

        provider = selected.provider.value
        if provider == "openai":
            xml = await _call_openai(api_key, model, user_prompt)
        elif provider == "anthropic":
            xml = await _call_anthropic(api_key, model, user_prompt)
        elif provider == "google":
            xml = await _call_google(api_key, model, user_prompt)
        else:
            raise HTTPException(status_code=400, detail=f"Provider não suportado: {provider}")

        if "<agent_prompt>" not in xml:
            raise HTTPException(status_code=400, detail="LLM não retornou XML no formato esperado")

        return GeneratePromptResponse(prompt_xml=xml, provider=provider, model=model)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro inesperado ao gerar prompt XML")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao gerar prompt XML: {type(e).__name__}",
        ) from e



@router.get("", response_model=PaginatedResponse[AgentResponse])
async def list_agents(
    request: Request,
    db: TenantDB,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[AgentResponse]:
    tid = request.state.tenant_id
    total = (
        await db.execute(select(func.count(Agent.id)).where(Agent.tenant_id == tid))
    ).scalar_one()
    agents = (
        await db.execute(
            select(Agent)
            .where(Agent.tenant_id == tid)
            .order_by(Agent.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return PaginatedResponse(
        items=list(agents),
        total=total,
        page=page,
        page_size=page_size,
        has_next=total > page * page_size,
    )


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(body: AgentCreate, request: Request, db: TenantDB) -> Agent:
    agent = Agent(tenant_id=request.state.tenant_id, **body.model_dump(exclude_none=True))
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    await _log_agent_event(
        db,
        tenant_id=request.state.tenant_id,
        agent_id=agent.id,
        level="info",
        event_type="agent.created",
        message="Agente criado com sucesso",
        payload={"status": agent.status.value, "name": agent.name},
    )
    return agent


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: uuid.UUID, request: Request, db: TenantDB) -> Agent:
    agent = (
        await db.execute(
            select(Agent).where(Agent.id == agent_id, Agent.tenant_id == request.state.tenant_id)
        )
    ).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    return agent


@router.get("/{agent_id}/logs", response_model=list[AgentLogResponse])
async def list_agent_logs(
    agent_id: uuid.UUID,
    request: Request,
    db: TenantDB,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[AgentEventLog]:
    logs = (
        await db.execute(
            select(AgentEventLog)
            .where(
                AgentEventLog.agent_id == agent_id,
                AgentEventLog.tenant_id == request.state.tenant_id,
            )
            .order_by(AgentEventLog.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return list(logs)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: uuid.UUID, body: AgentUpdate, request: Request, db: TenantDB
) -> Agent:
    agent = (
        await db.execute(
            select(Agent).where(Agent.id == agent_id, Agent.tenant_id == request.state.tenant_id)
        )
    ).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    before_status = agent.status.value
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(agent, k, v)
    await db.flush()
    await db.refresh(agent)
    await _log_agent_event(
        db,
        tenant_id=request.state.tenant_id,
        agent_id=agent.id,
        level="info",
        event_type="agent.updated",
        message="Configurações do agente atualizadas",
        payload={
            "before_status": before_status,
            "after_status": agent.status.value,
        },
    )
    return agent


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: uuid.UUID, request: Request, db: TenantDB) -> None:
    agent = (
        await db.execute(
            select(Agent).where(Agent.id == agent_id, Agent.tenant_id == request.state.tenant_id)
        )
    ).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    await db.delete(agent)


@router.post("/{agent_id}/simulate", response_model=AgentSimulateResponse)
async def simulate_agent(
    agent_id: uuid.UUID, body: AgentSimulateRequest, request: Request, db: TenantDB
) -> AgentSimulateResponse:
    agent = (
        await db.execute(
            select(Agent).where(Agent.id == agent_id, Agent.tenant_id == request.state.tenant_id)
        )
    ).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado")

    creds = (
        await db.execute(
            select(LLMCredentials)
            .where(
                LLMCredentials.tenant_id == request.state.tenant_id,
                LLMCredentials.is_active.is_(True),
            )
            .order_by(LLMCredentials.updated_at.desc())
        )
    ).scalars().all()
    if not creds:
        raise HTTPException(status_code=400, detail="Nenhuma credencial LLM ativa encontrada")

    selected = None
    if agent.llm_provider:
        selected = next((c for c in creds if c.provider.value == agent.llm_provider), None)
        if not selected:
            raise HTTPException(
                status_code=400,
                detail=f"Credencial para provider '{agent.llm_provider}' não encontrada",
            )
    else:
        selected = creds[0]

    model = agent.llm_model or selected.default_model
    api_key = _sanitize_api_key(decrypt(selected.api_key_encrypted))
    history = [{"role": m.role, "content": m.content} for m in body.history] + [
        {"role": "user", "content": body.message}
    ]
    system_prompt = agent.system_prompt or "Você é um agente SDR prestativo."

    provider = selected.provider.value
    try:
        if provider == "openai":
            reply = await _chat_openai(api_key, model, system_prompt, history)
        elif provider == "anthropic":
            reply = await _chat_anthropic(api_key, model, system_prompt, history)
        elif provider == "google":
            reply = await _chat_google(api_key, model, system_prompt, history)
        else:
            raise HTTPException(status_code=400, detail=f"Provider não suportado: {provider}")
    except HTTPException as e:
        await _log_agent_event(
            db,
            tenant_id=request.state.tenant_id,
            agent_id=agent.id,
            level="error",
            event_type="simulation.error",
            message="Erro ao simular resposta do agente",
            payload={"detail": str(e.detail), "provider": provider, "model": model},
        )
        raise

    await _log_agent_event(
        db,
        tenant_id=request.state.tenant_id,
        agent_id=agent.id,
        level="info",
        event_type="simulation.reply_generated",
        message="Resposta gerada no simulador",
        payload={"provider": provider, "model": model, "reply_preview": reply[:250]},
    )
    return AgentSimulateResponse(reply=reply, provider=provider, model=model)
    await _log_agent_event(
        db,
        tenant_id=request.state.tenant_id,
        agent_id=agent.id,
        level="info",
        event_type="simulation.message_received",
        message="Mensagem recebida no simulador",
        payload={"message_preview": body.message[:200]},
    )
