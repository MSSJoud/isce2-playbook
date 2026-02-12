import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pystac
import stac_asset
from aiohttp_oauth2_client.models.grant import GrantType
from settings import PASSWORD, USERNAME


def replace_href(item: pystac.Item) -> pystac.Item:
    url = item.assets["product"].href
    parsed_url = urlparse(url)
    new_netloc = "zipper.dataspace.copernicus.eu"
    new_url = urlunparse(parsed_url._replace(netloc=new_netloc))
    item.assets["product"].href = new_url
    return item


async def download_item(item: pystac.Item, output_dir: Path) -> None:
    config = stac_asset.Config()
    config.oauth2_grant = GrantType.RESOURCE_OWNER_PASSWORD_CREDENTIALS
    config.oauth2_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    config.oauth2_username = USERNAME
    config.oauth2_password = PASSWORD
    config.oauth2_client_id = "cdse-public"
    config.http_client_timeout = 3600
    client = await stac_asset.HttpClient.from_config(config=config)
    try:
        # prefer 'product' asset, fallback to first asset
        asset_key = "product" if "product" in item.assets else next(iter(item.assets))
        asset = item.assets[asset_key]

        # choose href to download (use replaced href already set by replace_href)
        href = getattr(asset, "href", None) or asset.to_dict().get("href")

        # try to get a stable filename from alternate.s3.href if present
        asset_dict = asset.to_dict()
        alt_s3 = asset_dict.get("alternate", {}).get("s3", {}).get("href")
        if alt_s3:
            filename = os.path.basename(alt_s3)
        elif href:
            filename = os.path.basename(href.split("?")[0]) or f"{item.id}.zip"
        else:
            filename = f"{item.id}.zip"

        outpath = output_dir / filename

        await client.download_href(href=href, path=outpath)
    finally:
        await client.close()
