import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pystac
import stac_asset
from aiohttp_oauth2_client.models.grant import GrantType
from settings import PASSWORD, USERNAME


def replace_href(item: pystac.Item) -> pystac.Item:
    url = item.assets["PRODUCT"].href
    parsed_url = urlparse(url)
    new_netloc = "zipper.dataspace.copernicus.eu"
    new_url = urlunparse(parsed_url._replace(netloc=new_netloc))
    item.assets["PRODUCT"].href = new_url
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
    await client.download_href(
        href=item.assets["PRODUCT"].href,
        path=output_dir
        / os.path.basename(
            item.to_dict()["assets"]["PRODUCT"]["alternate"]["s3"]["href"]
        ),
    )
    await client.close()
