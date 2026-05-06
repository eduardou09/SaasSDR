"""Schemas Pydantic para agentes."""

import uuid
from datetime import datetime

from pydantic import Field

from app.models.agent import AgentStatus
from app.schemas.common import APIModel


class AgentCreate(APIModel):
    name: str
    system_prompt: str | None = None
    tone: str | None = None
    language: str = "pt-BR"
    llm_provider: str | None = None
    llm_model: str | None = None
    temperature: float = 0.7
    qualification_schema: dict | None = None


class AgentUpdate(APIModel):
    name: str | None = None
    status: AgentStatus | None = None
    system_prompt: str | None = None
    tone: str | None = None
    language: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    temperature: float | None = None
    qualification_schema: dict | None = None


class AgentResponse(APIModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    status: AgentStatus
    system_prompt: str | None = None
    tone: str | None = None
    language: str
    llm_provider: str | None = None
    llm_model: str | None = None
    temperature: float
    version: int
    created_at: datetime
    updated_at: datetime


class GeneratePromptRequest(APIModel):
    company_name: str
    company_description: str
    icp: str
    qualification_questions: str
    qualification_criteria: str
    objections: str
    tone: str = "professional"
    language: str = "pt-BR"
    forbidden_terms: str | None = None
    next_step: str
    agent_identity: str | None = None
    personality_tone: str | None = None
    company_context: str | None = None
    audience_personas: str | None = None
    opening_script: str | None = None
    qualification_flow_good: str | None = None
    scenarios_scripts: str | None = None
    faq_scripts: str | None = None
    objections_scripts: str | None = None
    handoff_rules: str | None = None
    technical_features: str | None = None
    always_rules: str | None = None
    never_rules: str | None = None
    special_cases: str | None = None
    formatting_style: str | None = None
    success_examples: str | None = None
    problematic_examples: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None


class GeneratePromptResponse(APIModel):
    prompt_xml: str
    provider: str
    model: str


class SimulationMessage(APIModel):
    role: str  # "user" | "assistant"
    content: str


class AgentSimulateRequest(APIModel):
    message: str
    history: list[SimulationMessage] = Field(default_factory=list)


class AgentSimulateResponse(APIModel):
    reply: str
    provider: str
    model: str


class AgentLogResponse(APIModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    level: str
    event_type: str
    message: str
    payload: dict | None = None
    created_at: datetime
