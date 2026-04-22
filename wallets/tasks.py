from celery import shared_task

from .sync import sync_all_active_wallets


@shared_task(
    bind=True,
    name="wallets.tasks.sync_active_wallets_task",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 30},
    retry_backoff=True,
    retry_jitter=True,
)
def sync_active_wallets_task(self):
    sync_all_active_wallets(source="celery")
    return "ok"