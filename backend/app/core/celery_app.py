from celery import Celery

from app.config import settings

celery_app = Celery(
    "convo",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=[
        "app.tasks.messages",
        "app.tasks.learning",
        "app.tasks.supervisor",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Retry automático em falhas temporárias
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Dead letter queue via Redis
    task_routes={
        "app.tasks.messages.*": {"queue": "messages"},
        "app.tasks.learning.*": {"queue": "learning"},
        "app.tasks.supervisor.*": {"queue": "supervisor"},
    },
    # Beat schedule (jobs periódicos)
    beat_schedule={
        "learning-classifier-every-6h": {
            "task": "app.tasks.learning.classify_bad_conversations",
            "schedule": 6 * 60 * 60,  # 6 horas em segundos
        },
        "supervisor-weekly-monday": {
            "task": "app.tasks.supervisor.run_weekly_supervisor",
            "schedule": {
                "type": "crontab",
                "minute": "0",
                "hour": "6",
                "day_of_week": "1",  # Segunda-feira
            },
        },
    },
)
