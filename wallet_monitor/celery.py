import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wallet_monitor.settings")

app = Celery("wallet_monitor")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "sync-active-wallets-every-1-minutes": {
        "task": "wallets.tasks.sync_active_wallets_task",
        "schedule": 60.0,
    },
}