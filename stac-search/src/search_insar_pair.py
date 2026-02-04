import argparse
from typing import List, Optional

import pandas as pd
import pystac
import pystac_client
from settings import BBOX, COLLECTION, DATA_STAC_DIR, INSAR_CSV_PATH, STAC_API_URL


class InSARPair:
    def __init__(
        self, first: pystac.Item, second: pystac.Item, bbox_threshold: float = 1e-2
    ) -> None:
        self.first = first
        self.second = second
        self.bbox_threshold = bbox_threshold

    def diffDatetime(self) -> int:
        delta = abs((self.first.datetime - self.second.datetime).days)
        return delta

    def isInSARPair(self) -> bool:
        for key in [
            "relativeOrbitNumber",
            "orbitDirection",
            "productType",
            "operationalMode",
        ]:
            if self.first.properties[key] != self.second.properties[key]:
                return False

        for i in range(4):
            if abs(self.first.bbox[i] - self.second.bbox[i]) > self.bbox_threshold:
                return False

        return True


def search_slc_items(start_date: str, end_date: str) -> List[pystac.Item]:
    client = pystac_client.Client.open(STAC_API_URL)
    searched_items = client.search(
        collections=[COLLECTION],
        bbox=BBOX,
        datetime=f"{start_date}/{end_date}",
    )

    slc_items = set()
    for item in searched_items.items():
        if item.id.startswith("S1A_IW_SLC__1SDV"):
            slc_items.add(item)

    slc_items = list(slc_items)
    slc_items.sort(key=lambda item: item.datetime)
    return slc_items


def save_stac_json(insar_pairs: List[InSARPair]) -> None:
    for insar_pair in insar_pairs:
        first_stac_path = DATA_STAC_DIR / f"{insar_pair.first.id}.json"
        second_stac_path = DATA_STAC_DIR / f"{insar_pair.second.id}.json"

        insar_pair.first.set_self_href(str(first_stac_path.resolve()))
        insar_pair.first.save_object()

        insar_pair.second.set_self_href(str(second_stac_path.resolve()))
        insar_pair.second.save_object()


def save_insar_csv(insar_pairs: List[InSARPair]) -> None:
    data = {
        "first_id": [insar_pair.first.id for insar_pair in insar_pairs],
        "second_id": [insar_pair.second.id for insar_pair in insar_pairs],
    }
    df = pd.DataFrame(data)
    df.to_csv(str(INSAR_CSV_PATH.resolve()), index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_date", required=True)
    parser.add_argument("--end_date", required=True)
    args = parser.parse_args()

    start_date = args.start_date
    end_date = args.end_date

    slc_items = search_slc_items(start_date, end_date)
    insar_pairs: List[InSARPair] = []

    for i in range(len(slc_items)):
        insar_pair: Optional[InSARPair] = None

        for j in range(i + 1, len(slc_items)):
            tmp = InSARPair(
                first=slc_items[i].full_copy(), second=slc_items[j].full_copy()
            )

            if tmp.isInSARPair():
                if insar_pair is None:
                    insar_pair = tmp
                elif tmp.diffDatetime() < insar_pair.diffDatetime():
                    insar_pair = tmp

        if insar_pair is not None:
            insar_pairs.append(insar_pair)

    save_stac_json(insar_pairs)
    save_insar_csv(insar_pairs)


if __name__ == "__main__":
    main()
