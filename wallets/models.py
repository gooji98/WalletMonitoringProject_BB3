from django.conf import settings
from django.db import models


class Wallet(models.Model):
    address = models.CharField(max_length=42, unique=True)
    label = models.CharField(max_length=100, blank=True)
    network = models.CharField(max_length=50, default="Ethereum Mainnet")
    assigned_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_wallets",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        if self.label:
            return f"{self.label} ({self.address})"
        return self.address


class BalanceSnapshot(models.Model):
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="balance_snapshots"
    )
    balance_wei = models.CharField(max_length=100)
    balance_eth = models.DecimalField(max_digits=30, decimal_places=18)
    fetched_at = models.DateTimeField()

    def __str__(self):
        return f"{self.wallet.address} - {self.balance_eth} ETH @ {self.fetched_at}"


class TransactionSnapshot(models.Model):
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="transaction_snapshots"
    )
    tx_hash = models.CharField(max_length=66, unique=True)
    from_address = models.CharField(max_length=42)
    to_address = models.CharField(max_length=42, null=True, blank=True)
    value_wei = models.CharField(max_length=100)
    value_eth = models.DecimalField(max_digits=30, decimal_places=18)
    block_number = models.BigIntegerField()
    tx_timestamp = models.DateTimeField()
    is_error = models.BooleanField(default=False)
    fetched_at = models.DateTimeField()

    def __str__(self):
        return self.tx_hash