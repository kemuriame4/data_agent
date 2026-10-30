from typing import List, Dict


class WMSSync:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key

    def fetch_inventory(self) -> List[Dict]:
        return []

    def fetch_shipments(self) -> List[Dict]:
        return []


def run_wms_sync():
    print("WMS sync placeholder")
