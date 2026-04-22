from datetime import datetime, timezone as dt_timezone

from django.utils import timezone

from .models import Wallet, SyncLog
from .realtime import notify_dashboard_update, notify_wallet_update
from .realtime import notify_dashboard_update, notify_wallet_update
from .services import EtherscanService


def unix_to_aware_datetime(timestamp_str):
    timestamp_int = int(timestamp_str)
    return datetime.fromtimestamp(timestamp_int, tz=dt_timezone.utc)


def sync_wallet(wallet, source="celery"):
    service = EtherscanService()

    balance_wei, balance_eth = service.get_wallet_balance(wallet.address)
    transactions = service.get_normal_transactions(wallet.address, offset=20)

    wallet.balance_snapshots.create(
        balance_wei=balance_wei,
        balance_eth=balance_eth,
        fetched_at=timezone.now(),
    )
    notify_dashboard_update({"wallet_id": wallet.id, "source": source})
    notify_wallet_update(wallet.id, {"wallet_id": wallet.id, "source": source})

    for tx in transactions:
        wallet.transaction_snapshots.update_or_create(
            tx_hash=tx["hash"],
            defaults={
                "from_address": tx["from"],
                "to_address": tx.get("to") or "",
                "value_wei": tx["value"],
                "value_eth": service.wei_to_eth(tx["value"]),
                "block_number": int(tx["blockNumber"]),
                "tx_timestamp": unix_to_aware_datetime(tx["timeStamp"]),
                "is_error": str(tx.get("isError", "0")) == "1",
                "fetched_at": timezone.now(),
            },
        )

    wallet.last_synced_at = timezone.now()
    wallet.save(update_fields=["last_synced_at"])

    notify_dashboard_update({"wallet_id": wallet.id, "source": source})
    notify_wallet_update(wallet.id, {"wallet_id": wallet.id, "source": source})


def sync_all_active_wallets(source="celery"):
    wallets = Wallet.objects.filter(is_active=True)

    for wallet in wallets:
        started_at = timezone.now()

        try:
            sync_wallet(wallet, source=source)

            SyncLog.objects.create(
                wallet=wallet,
                status="success",
                started_at=started_at,
                finished_at=timezone.now(),
                message="Wallet synced successfully.",
                source=source,
            )

            print(f"[SYNC OK] wallet_id={wallet.id} label={wallet.label or '-'}")

        except Exception as exc:
            SyncLog.objects.create(
                wallet=wallet,
                status="failed",
                started_at=started_at,
                finished_at=timezone.now(),
                message=str(exc),
                source=source,
            )

            print(f"[SYNC FAILED] wallet_id={wallet.id} label={wallet.label or '-'} error={exc}")