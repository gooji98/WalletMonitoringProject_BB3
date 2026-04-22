from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def notify_dashboard_update(payload=None):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    async_to_sync(channel_layer.group_send)(
        "dashboard",
        {
            "type": "dashboard.update",
            "payload": payload or {},
        },
    )


def notify_wallet_update(wallet_id, payload=None):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    async_to_sync(channel_layer.group_send)(
        f"wallet_{wallet_id}",
        {
            "type": "wallet.update",
            "payload": payload or {},
        },
    )