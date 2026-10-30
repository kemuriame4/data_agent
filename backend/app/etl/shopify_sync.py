from datetime import datetime
from typing import List, Dict
import httpx

from app.config import get_settings

settings = get_settings()


class ShopifySync:
    def __init__(self, shop: str, access_token: str):
        self.shop = shop
        self.access_token = access_token
        self.base_url = f"https://{shop}.myshopify.com/admin/api/2024-04"

    def _headers(self):
        return {"X-Shopify-Access-Token": self.access_token}

    def fetch_orders(self, since: datetime) -> List[Dict]:
        url = f"{self.base_url}/orders.json"
        params = {"status": "any", "created_at_min": since.isoformat(), "limit": 250}
        with httpx.Client() as client:
            resp = client.get(url, headers=self._headers(), params=params)
            resp.raise_for_status()
            return resp.json().get("orders", [])


def run_shopify_sync():
    print("Shopify sync placeholder")
