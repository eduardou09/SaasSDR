"""
Tasks Celery para o loop de aprendizado (sub-módulo 8.2).
Implementado no Sprint 6.
"""

from app.core.celery_app import celery_app


@celery_app.task(name="app.tasks.learning.classify_bad_conversations")
def classify_bad_conversations() -> None:  # type: ignore[misc]
    """Analisa conversas ruins e cria entradas no learning_inbox. Sprint 6."""
    raise NotImplementedError("Sprint 6")
