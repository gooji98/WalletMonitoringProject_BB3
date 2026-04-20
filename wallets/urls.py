from django.urls import path
from .views import (
    dashboard,
    dashboard_wallets_partial,
    dashboard_transactions_partial,
    sync_now,
    wallet_detail,
    wallet_snapshots_partial,
    wallet_transactions_partial,
    sync_single_wallet,
    export_wallet_transactions_csv,
    export_wallet_snapshots_csv,
    export_dashboard_summary_xlsx,
)

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("sync-now/", sync_now, name="sync_now"),
    path("export-summary-xlsx/", export_dashboard_summary_xlsx, name="export_dashboard_summary_xlsx"),

    path("partials/dashboard-wallets/", dashboard_wallets_partial, name="dashboard_wallets_partial"),
    path("partials/dashboard-transactions/", dashboard_transactions_partial, name="dashboard_transactions_partial"),

    path("wallets/<int:wallet_id>/", wallet_detail, name="wallet_detail"),
    path("wallets/<int:wallet_id>/sync/", sync_single_wallet, name="sync_single_wallet"),
    path("wallets/<int:wallet_id>/snapshots/", wallet_snapshots_partial, name="wallet_snapshots_partial"),
    path("wallets/<int:wallet_id>/transactions/", wallet_transactions_partial, name="wallet_transactions_partial"),
    path("wallets/<int:wallet_id>/transactions/export-csv/", export_wallet_transactions_csv, name="export_wallet_transactions_csv"),
    path("wallets/<int:wallet_id>/snapshots/export-csv/", export_wallet_snapshots_csv, name="export_wallet_snapshots_csv"),
]