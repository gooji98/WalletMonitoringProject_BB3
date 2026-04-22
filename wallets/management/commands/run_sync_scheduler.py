import time
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.core.management.base import BaseCommand

from wallets.sync import sync_all_active_wallets


def scheduled_sync():
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{started_at}] Starting wallet sync...")

    try:
        sync_all_active_wallets()
        finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{finished_at}] Wallet sync completed successfully.")
    except Exception as exc:
        failed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{failed_at}] Wallet sync failed: {exc}")


class Command(BaseCommand):
    help = "Run wallet sync scheduler every 2 minutes"

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone="UTC")

        scheduler.add_job(
            scheduled_sync,
            trigger=IntervalTrigger(minutes=2),
            id="wallet_sync_job",
            max_instances=1,
            replace_existing=True,
            coalesce=True,
        )

        self.stdout.write(self.style.SUCCESS("Wallet sync scheduler started. Running every 2 minutes."))

        try:
            scheduler.start()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Wallet sync scheduler stopped."))
            scheduler.shutdown()