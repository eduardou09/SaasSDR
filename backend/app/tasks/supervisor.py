"""
Tasks Celery para o supervisor semanal (sub-módulo 8.3).
Implementado no Sprint 6.
"""

from app.core.celery_app import celery_app


@celery_app.task(name="app.tasks.supervisor.run_weekly_supervisor")
def run_weekly_supervisor() -> None:  # type: ignore[misc]
    """Roda o supervisor semanal para todos os tenants ativos. Sprint 6."""
    raise NotImplementedError("Sprint 6")
