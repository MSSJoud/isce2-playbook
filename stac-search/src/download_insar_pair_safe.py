import argparse
import asyncio

import pystac
from download_utils import download_item, replace_href
from settings import DATA_SAFE_ZIP_DIR, DATA_STAC_DIR


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--first_id", required=True)
    parser.add_argument("--second_id", required=True)
    args = parser.parse_args()

    for id in [args.first_id, args.second_id]:
        item = pystac.read_file(DATA_STAC_DIR / f"{id}.json")
        assert isinstance(item, pystac.Item)
        item = replace_href(item)
        asyncio.run(download_item(item, DATA_SAFE_ZIP_DIR))


if __name__ == "__main__":
    main()
