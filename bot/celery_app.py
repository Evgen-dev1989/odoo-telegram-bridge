from celery import Celery
from celery.schedules import crontab
from os import getenv

REDIS_URL = getenv("REDIS_URL", "redis://127.0.0.1:6373/0")

app = Celery(
    "stock_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

app.conf.update(
    timezone="Europe/Kyiv",
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)

app.conf.beat_schedule = {
    "check-minimum-stock-every-morning": {
        "task": "bot.celery_app.check_stock_limits_task",
        "schedule":60.0#(hour=9, minute=0)
    },
}

app.autodiscover_tasks(["bot.celery_app"], force=True)