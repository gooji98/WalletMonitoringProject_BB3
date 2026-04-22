from django.urls import re_path

from wallets.consumers import DashboardConsumer, WalletConsumer

websocket_urlpatterns = [
    re_path(r"ws/dashboard/$", DashboardConsumer.as_asgi()),
    re_path(r"ws/wallet/(?P<wallet_id>\d+)/$", WalletConsumer.as_asgi()),
]