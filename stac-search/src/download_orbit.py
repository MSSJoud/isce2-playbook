import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import pystac
import pystac_client
from download_utils import download_item, replace_href
from settings import COLLECTION, DATA_ORBIT_DIR, DATA_STAC_DIR, STAC_API_URL


def get_stac_json_paths() -> List[Path]:
    return list(DATA_STAC_DIR.glob("*.json"))


def search_orbit_items(start_date: str, end_date: str) -> List[pystac.Item]:
    client = pystac_client.Client.open(STAC_API_URL)
    searched_items = client.search(
        collections=[COLLECTION],
        datetime=f"{start_date}/{end_date}",
    )

    orbit_items = set()
    for item in searched_items.items():
        if item.id.startswith("S1A_OPER_AUX_RESORB_OPOD") and item.id.endswith(".EOF"):
            orbit_items.add(item)

    orbit_items = list(orbit_items)
    orbit_items.sort(key=lambda item: item.datetime)
    return orbit_items


def shift_hours_in_date(date: str, hours: int) -> str:
    date: datetime = datetime.fromisoformat(date.replace("Z", "+00:00"))
    new_date = date + timedelta(hours=hours)
    return new_date.isoformat()


def main() -> None:
    for stac_json_path in get_stac_json_paths():
        item = pystac.read_file(stac_json_path)
        assert isinstance(item, pystac.Item)

        date = item.properties["datetime"]
        start_date = shift_hours_in_date(date, -1)
        end_date = shift_hours_in_date(date, 1)

        for item in search_orbit_items(start_date, end_date):
            item = replace_href(item)
            asyncio.run(download_item(item, DATA_ORBIT_DIR))


if __name__ == "__main__":
    main()
