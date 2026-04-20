from decimal import Decimal
import requests
from django.conf import settings


class EtherscanService:
    def __init__(self):
        self.api_key = settings.ETHERSCAN_API_KEY
        self.base_url = settings.ETHERSCAN_BASE_URL
        self.chain_id = settings.ETHEREUM_CHAIN_ID

    def get_native_balance(self, address: str) -> dict:
        params = {
            "chainid": self.chain_id,
            "module": "account",
            "action": "balance",
            "address": address,
            "tag": "latest",
            "apikey": self.api_key,
        }

        response = requests.get(self.base_url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "1":
            raise ValueError(f"Etherscan balance error: {data}")

        balance_wei = data["result"]
        balance_eth = Decimal(balance_wei) / Decimal("1000000000000000000")

        return {
            "address": address,
            "balance_wei": balance_wei,
            "balance_eth": balance_eth,
        }

    def get_normal_transactions(
        self,
        address: str,
        start_block: int = 0,
        end_block: int = 99999999,
        page: int = 1,
        offset: int = 20,
        sort: str = "desc",
    ) -> list[dict]:
        params = {
            "chainid": self.chain_id,
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": start_block,
            "endblock": end_block,
            "page": page,
            "offset": offset,
            "sort": sort,
            "apikey": self.api_key,
        }

        response = requests.get(self.base_url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        status = data.get("status")
        message = data.get("message")
        result = data.get("result", [])

        if status == "0" and message != "No transactions found":
            raise ValueError(f"Etherscan txlist error: {data}")

        return result