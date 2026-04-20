from datetime import datetime, timezone as py_timezone
from decimal import Decimal

from django.utils import timezone

from .models import Wallet, BalanceSnapshot, TransactionSnapshot
from .services import EtherscanService


def unix_to_aware_datetime(timestamp_str: str):
    timestamp_int = int(timestamp_str)
    return datetime.fromtimestamp(timestamp_int, tz=py_timezone.utc)


def sync_wallet(wallet: Wallet):
    service = EtherscanService()
    now = timezone.now()

    balance_data = service.get_native_balance(wallet.address)

    BalanceSnapshot.objects.create(
        wallet=wallet,
        balance_wei=balance_data["balance_wei"],
        balance_eth=balance_data["balance_eth"],
        fetched_at=now,
    )

    transactions = service.get_normal_transactions(wallet.address, offset=20)

    for tx in transactions:
        tx_hash = tx["hash"]

        if TransactionSnapshot.objects.filter(tx_hash=tx_hash).exists():
            continue

        value_wei = tx["value"]
        value_eth = Decimal(value_wei) / Decimal("10000000000000000000000")

        TransactionSnapshot.objects.create(
            wallet=wallet,
            tx_hash=tx_hash,
            from_address=tx["from"],
            to_address=tx.get("to") or None,
            value_wei=value_wei,
            value_eth=value_eth,
            block_number=int(tx["blockNumber"]),
            tx_timestamp=unix_to_aware_datetime(tx["timeStamp"]),
            is_error=(tx.get("isError") == "1"),
            fetched_at=now,
        )

    wallet.last_synced_at = now
    wallet.save(update_fields=["last_synced_at"])


def sync_all_active_wallets():
    wallets = Wallet.objects.filter(is_active=True)

    for wallet in wallets:
        sync_wallet(wallet)