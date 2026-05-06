"""
Tasks Celery para processamento de mensagens inbound.
Implementado no Sprint 4.
"""

from app.core.celery_app import celery_app


@celery_app.task(
    name="app.tasks.messages.process_inbound_message",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def process_inbound_message(self, tenant_id: str, payload: dict) -> None:  # type: ignore[misc]
    """Processa uma mensagem inbound do Z-API. Implementado no Sprint 4."""
    raise NotImplementedError("Sprint 4")
