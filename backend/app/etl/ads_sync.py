from datetime import datetime, timedelta
from typing import List, Dict


class MetaAdsSync:
    def __init__(self, access_token: str, ad_account_id: str):
        self.access_token = access_token
        self.ad_account_id = ad_account_id

    def fetch_insights(self, since: datetime, until: datetime) -> List[Dict]:
        return []


class GoogleAdsSync:
    def __init__(self, developer_token: str, customer_id: str):
        self.developer_token = developer_token
        self.customer_id = customer_id

    def fetch_insights(self, since: datetime, until: datetime) -> List[Dict]:
        return []


def run_ads_sync():
    print("Ads sync placeholder")
