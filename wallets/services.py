from decimal import Decimal

import requests
from django.conf import settings
from django.core.cache import cache


class EtherscanService:
    def __init__(self):
        self.api_key = settings.ETHERSCAN_API_KEY
        self.base_url = settings.ETHERSCAN_BASE_URL
        self.chain_id = settings.ETHEREUM_CHAIN_ID
        self.session = requests.Session()

    def wei_to_eth(self, value_wei):
        return Decimal(value_wei) / Decimal("1000000000000000000")

    def get_wallet_balance(self, address):
        params = {
            "chainid": self.chain_id,
            "module": "account",
            "action": "balance",
            "address": address,
            "tag": "latest",
            "apikey": self.api_key,
        }

        response = self.session.get(self.base_url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        balance_wei = data["result"]
        balance_eth = self.wei_to_eth(balance_wei)
        return balance_wei, balance_eth

    def get_normal_transactions(self, address, offset=20):
        params = {
            "chainid": self.chain_id,
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": offset,
            "sort": "desc",
            "apikey": self.api_key,
        }

        response = self.session.get(self.base_url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        result = data.get("result", [])
        if isinstance(result, list):
            return result
        return []


class CoinGeckoService:
    CACHE_KEY = "eth_usd_price"
    CACHE_TIMEOUT = 60

    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()

    def get_eth_usd_price(self):
        cached_price = cache.get(self.CACHE_KEY)
        if cached_price is not None:
            return cached_price

        url = f"{self.base_url}/simple/price"
        params = {
            "ids": "ethereum",
            "vs_currencies": "usd",
        }

        response = self.session.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        price = data.get("ethereum", {}).get("usd")
        if price is None:
            fallback = Decimal(str(getattr(settings, "ETH_USD_RATE", 3000)))
            cache.set(self.CACHE_KEY, fallback, self.CACHE_TIMEOUT)
            return fallback

        eth_price = Decimal(str(price))
        cache.set(self.CACHE_KEY, eth_price, self.CACHE_TIMEOUT)
        return eth_price