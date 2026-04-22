from decimal import Decimal

from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html

from .models import Wallet, BalanceSnapshot, TransactionSnapshot, SyncLog
from .sync import sync_wallet


class BalanceSnapshotInline(admin.TabularInline):
    model = BalanceSnapshot
    extra = 0
    fields = ("balance_eth", "fetched_at")
    readonly_fields = ("balance_eth", "fetched_at")
    ordering = ("-fetched_at",)
    show_change_link = True
    max_num = 10
    verbose_name = "Recent Balance Snapshot"
    verbose_name_plural = "Recent Balance Snapshots"


class TransactionSnapshotInline(admin.TabularInline):
    model = TransactionSnapshot
    extra = 0
    fields = ("tx_hash", "to_address", "value_eth", "is_error", "tx_timestamp")
    readonly_fields = ("tx_hash", "to_address", "value_eth", "is_error", "tx_timestamp")
    ordering = ("-tx_timestamp",)
    show_change_link = True
    max_num = 10
    verbose_name = "Recent Transaction"
    verbose_name_plural = "Recent Transactions"


@admin.action(description="Mark selected wallets as active")
def mark_wallets_active(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description="Mark selected wallets as inactive")
def mark_wallets_inactive(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.action(description="Sync selected wallets now")
def sync_selected_wallets(modeladmin, request, queryset):
    count = 0
    for wallet in queryset:
        sync_wallet(wallet)
        count += 1

    modeladmin.message_user(request, f"{count} wallet(s) synced successfully.")


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "label",
        "short_address",
        "network",
        "assigned_admin",
        "latest_balance_display",
        "latest_balance_usd_display",
        "status_badge",
        "last_synced_at",
        "created_at",
    )
    list_filter = (
        "is_active",
        "network",
        "assigned_admin",
        "created_at",
        "last_synced_at",
    )
    search_fields = (
        "label",
        "address",
        "network",
        "assigned_admin__username",
        "assigned_admin__email",
        "assigned_admin__first_name",
        "assigned_admin__last_name",
    )
    ordering = ("-created_at",)
    autocomplete_fields = ("assigned_admin",)
    readonly_fields = (
        "created_at",
        "last_synced_at",
        "latest_balance_display",
        "latest_balance_usd_display",
    )
    actions = (
        mark_wallets_active,
        mark_wallets_inactive,
        sync_selected_wallets,
    )
    inlines = (BalanceSnapshotInline, TransactionSnapshotInline)

    fieldsets = (
        ("Wallet Identity", {
            "fields": (
                "label",
                "address",
                "network",
            )
        }),
        ("Ownership & Operations", {
            "fields": (
                "assigned_admin",
                "is_active",
            )
        }),
        ("Live Status", {
            "fields": (
                "latest_balance_display",
                "latest_balance_usd_display",
                "last_synced_at",
            )
        }),
        ("Audit", {
            "fields": (
                "created_at",
            )
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("assigned_admin")
        if request.user.is_superuser:
            return qs
        return qs.filter(assigned_admin=request.user)

    def get_readonly_fields(self, request, obj=None):
        base_readonly = [
            "created_at",
            "last_synced_at",
            "latest_balance_display",
            "latest_balance_usd_display",
        ]

        if request.user.is_superuser:
            return base_readonly

        return base_readonly + [
            "label",
            "address",
            "network",
            "assigned_admin",
            "is_active",
        ]

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True

        if obj is None:
            return request.user.is_staff

        return obj.assigned_admin == request.user

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True

        if obj is None:
            return request.user.is_staff

        return obj.assigned_admin == request.user

    def get_actions(self, request):
        actions = super().get_actions(request)

        if not request.user.is_superuser:
            actions.pop("sync_selected_wallets", None)

        return actions

    def short_address(self, obj):
        return f"{obj.address[:8]}...{obj.address[-6:]}"
    short_address.short_description = "Address"

    def latest_balance(self, obj):
        return obj.balance_snapshots.order_by("-fetched_at").first()

    def latest_balance_display(self, obj):
        latest = self.latest_balance(obj)
        if not latest:
            return "-"
        return f"{latest.balance_eth.normalize()} ETH"
    latest_balance_display.short_description = "Latest Balance"

    def latest_balance_usd_display(self, obj):
        latest = self.latest_balance(obj)
        if not latest:
            return "-"

        rate = Decimal(str(getattr(settings, "ETH_USD_RATE", 3000)))
        usd_value = latest.balance_eth * rate
        return f"{usd_value.quantize(Decimal('0.01'))} USD"
    latest_balance_usd_display.short_description = "Balance USD"

    def status_badge(self, obj):
        if obj.is_active:
            color = "#198754"
            label = "Active"
        else:
            color = "#6c757d"
            label = "Inactive"

        return format_html(
            '<span style="color: white; background: {}; padding: 3px 8px; border-radius: 999px;">{}</span>',
            color,
            label,
        )
    status_badge.short_description = "Status"


@admin.register(BalanceSnapshot)
class BalanceSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "wallet",
        "balance_eth",
        "fetched_at",
    )
    search_fields = (
        "wallet__label",
        "wallet__address",
    )
    list_filter = (
        "wallet__network",
        "wallet__assigned_admin",
        "fetched_at",
    )
    ordering = ("-fetched_at",)
    autocomplete_fields = ("wallet",)
    date_hierarchy = "fetched_at"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(wallet__assigned_admin=request.user)


@admin.register(TransactionSnapshot)
class TransactionSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "wallet",
        "short_tx_hash",
        "to_address",
        "value_eth",
        "is_error",
        "tx_timestamp",
        "fetched_at",
    )
    search_fields = (
        "tx_hash",
        "from_address",
        "to_address",
        "wallet__label",
        "wallet__address",
    )
    list_filter = (
        "is_error",
        "wallet__network",
        "wallet__assigned_admin",
        "tx_timestamp",
        "fetched_at",
    )
    ordering = ("-tx_timestamp",)
    autocomplete_fields = ("wallet",)
    date_hierarchy = "tx_timestamp"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(wallet__assigned_admin=request.user)

    def short_tx_hash(self, obj):
        return f"{obj.tx_hash[:12]}...{obj.tx_hash[-6:]}"
    short_tx_hash.short_description = "Tx Hash"


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "wallet",
        "status",
        "source",
        "started_at",
        "finished_at",
        "short_message",
    )
    list_filter = (
        "status",
        "source",
        "started_at",
        "finished_at",
        "wallet__network",
        "wallet__assigned_admin",
    )
    search_fields = (
        "wallet__label",
        "wallet__address",
        "message",
    )
    ordering = ("-started_at",)
    autocomplete_fields = ("wallet",)
    date_hierarchy = "started_at"
    readonly_fields = (
        "wallet",
        "status",
        "source",
        "started_at",
        "finished_at",
        "message",
        "created_at",
    )

    def short_message(self, obj):
        if not obj.message:
            return "-"
        if len(obj.message) > 80:
            return obj.message[:80] + "..."
        return obj.message
    short_message.short_description = "Message"

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("wallet", "wallet__assigned_admin")
        if request.user.is_superuser:
            return qs
        return qs.filter(wallet__assigned_admin=request.user)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser