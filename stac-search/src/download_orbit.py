import re
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Tuple

import pystac
import requests
from bs4 import BeautifulSoup
from settings import DATA_ORBIT_DIR, DATA_STAC_DIR

# ESA STEP auxiliary data server.
# Files are organised by year AND month of their validity start date:
#   https://step.esa.int/auxdata/orbits/Sentinel-1/POEORB/S1A/{year}/{month}/
# The year/ level only lists month subdirectories — never .EOF files.
BASE_URL_POEORB = {
    "S1A": "https://step.esa.int/auxdata/orbits/Sentinel-1/POEORB/S1A/",
    "S1B": "https://step.esa.int/auxdata/orbits/Sentinel-1/POEORB/S1B/",
}
BASE_URL_RESORB = {
    "S1A": "https://step.esa.int/auxdata/orbits/Sentinel-1/RESORB/S1A/",
    "S1B": "https://step.esa.int/auxdata/orbits/Sentinel-1/RESORB/S1B/",
}


def get_stac_json_paths() -> List[Path]:
    return list(DATA_STAC_DIR.glob("*.json"))


def get_platform_from_item(item: pystac.Item) -> Optional[str]:
    """Return 'S1A' or 'S1B' from a STAC item, or None if unrecognised."""
    platform_map = {
        "sentinel-1a": "S1A",
        "sentinel-1b": "S1B",
        "s1a": "S1A",
        "s1b": "S1B",
    }
    raw = item.properties.get("platform", "").lower()
    if raw:
        platform = platform_map.get(raw)
        if platform:
            return platform

    # Fallback: parse the item ID directly (e.g. S1A_IW_SLC_...)
    if item.id.startswith("S1A"):
        return "S1A"
    if item.id.startswith("S1B"):
        return "S1B"
    return None


def _to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Normalise a datetime to UTC-aware. Treats naive datetimes as UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_scene_window(item: pystac.Item) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Return (scene_start, scene_end) as UTC-aware datetimes.

    ISCE2's fetchOrbit.py validates orbit coverage against BOTH the start
    and stop times of the acquisition:
        orbit_valid_start <= scene_start  AND  orbit_valid_end >= scene_stop

    STAC common_metadata carries start_datetime / end_datetime when present.
    If missing, item.datetime (usually scene start) is used for both bounds.
    """
    start = _to_utc(item.common_metadata.start_datetime)
    end = _to_utc(item.common_metadata.end_datetime)

    if start is None or end is None:
        fallback = _to_utc(item.datetime)
        start = start or fallback
        end = end or fallback

    return start, end


def parse_orbit_filename(filename: str) -> Optional[Tuple[datetime, datetime]]:
    """
    Parse the validity window from an orbit filename.

    Example:
        S1A_OPER_AUX_POEORB_OPOD_20210304T120252_V20210211T225942_20210213T005942.EOF
        → valid_start = 2021-02-11T22:59:42Z
        → valid_end   = 2021-02-13T00:59:42Z

    Returns (valid_start, valid_end) as UTC-aware datetimes, or None.
    """
    base = filename[:-4] if filename.endswith(".zip") else filename
    m = re.search(r"_V(\d{8}T\d{6})_(\d{8}T\d{6})\.EOF$", base)
    if not m:
        return None
    try:
        valid_start = datetime.strptime(m.group(1), "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
        valid_end = datetime.strptime(m.group(2), "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
        return valid_start, valid_end
    except ValueError:
        return None


def orbit_covers_scene(
    orbit_start: datetime,
    orbit_end: datetime,
    scene_start: datetime,
    scene_end: datetime,
) -> bool:
    """
    Replicates ISCE2 fetchOrbit.py bracketing logic (line 153):
        (orbit_start <= scene_start) AND (orbit_end >= scene_end)

    The orbit file must cover the FULL acquisition window, not just the
    centre or start time of the scene.
    """
    return orbit_start <= scene_start and orbit_end >= scene_end


def unzip_file(zip_path: Path, delete_zip: bool = True) -> Optional[Path]:
    """Extract the .EOF from a .EOF.zip and optionally remove the zip.

    The ESA STEP ZIPs nest the .EOF inside a full server path tree:
        var/www/auxdata/orbits/Sentinel-1/POEORB/S1A/YYYY/MM/<name>.EOF
    Using z.extract() would recreate that tree on disk.  Instead, read the
    file content directly and write it flat next to the zip.
    """
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            eof_entries = [f for f in z.namelist() if f.endswith(".EOF")]
            if not eof_entries:
                print(f"No .EOF found inside {zip_path.name}")
                return None
            # Write the .EOF directly into the target directory (no subdirs)
            eof_name = Path(eof_entries[0]).name
            target = zip_path.parent / eof_name
            target.write_bytes(z.read(eof_entries[0]))
            print(f"Extracted: {eof_name}")
            if delete_zip:
                zip_path.unlink()
                print(f"Removed zip: {zip_path.name}")
            return target
    except Exception as e:
        print(f"Failed to extract {zip_path}: {e}")
        return None


def _list_orbit_dir(dir_url: str) -> List[str]:
    """Return .EOF / .EOF.zip hrefs from an ESA STEP directory listing."""
    try:
        resp = requests.get(dir_url, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to list {dir_url}: {e}")
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    return [
        a.get("href", "")
        for a in soup.find_all("a")
        if a.get("href", "").endswith((".EOF", ".EOF.zip"))
    ]


def download_orbit_esa(
    scene_start: datetime,
    scene_end: datetime,
    platform: str,
    orbit_type: str = "POEORB",
) -> Optional[Path]:
    """
    Download the orbit file that brackets [scene_start, scene_end] from
    the ESA STEP auxiliary data server.

    Selection logic mirrors ISCE2's fetchOrbit.py:
        orbit_valid_start <= scene_start  AND  orbit_valid_end >= scene_end

    The ESA STEP server organises files by year/month of their VALIDITY START
    date — NOT year alone. The year/ level only lists month subdirectories.

    Edge case: for scenes early in a month the orbit validity may start in the
    previous month, so both the scene month and the previous month are checked.

    A deduplication check skips the download when the file already exists.
    """
    base_urls = BASE_URL_POEORB if orbit_type == "POEORB" else BASE_URL_RESORB
    base_url = base_urls.get(platform)
    if not base_url:
        print(f"Unsupported platform '{platform}' for {orbit_type}")
        return None

    # Candidate directories: scene month first, then the previous month.
    # The orbit validity start date is typically 1 day before the scene,
    # so a scene on the 1st of a month will need the prior month's directory.
    prev_month = scene_start.replace(day=1) - timedelta(days=1)
    candidate_dirs = [
        f"{base_url}{scene_start.year}/{scene_start.month:02d}/",
        f"{base_url}{prev_month.year}/{prev_month.month:02d}/",
    ]

    matched_filename: Optional[str] = None
    matched_dir: Optional[str] = None

    for dir_url in candidate_dirs:
        links = _list_orbit_dir(dir_url)
        for link in links:
            filename = link.split("/")[-1]
            validity = parse_orbit_filename(filename)
            if validity is None:
                continue
            orbit_start, orbit_end = validity
            if orbit_covers_scene(orbit_start, orbit_end, scene_start, scene_end):
                matched_filename = filename
                matched_dir = dir_url
                break
        if matched_filename:
            break

    if matched_filename is None:
        print(
            f"No {orbit_type} covers [{scene_start.isoformat()} – {scene_end.isoformat()}]"
            f" for {platform}"
        )
        return None

    # The final file on disk is always a plain .EOF (zip is extracted on arrival).
    eof_name = matched_filename[:-4] if matched_filename.endswith(".zip") else matched_filename
    eof_path = DATA_ORBIT_DIR / eof_name
    if eof_path.exists():
        print(f"Already exists: {eof_name}")
        return eof_path

    file_url = f"{matched_dir}{matched_filename}"
    out_path = DATA_ORBIT_DIR / matched_filename
    print(f"Downloading {matched_filename} ...")
    try:
        with requests.get(file_url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Saved: {out_path.name}")
    except Exception as e:
        print(f"Failed to download {file_url}: {e}")
        out_path.unlink(missing_ok=True)
        return None

    if out_path.suffix == ".zip":
        return unzip_file(out_path, delete_zip=True)
    return out_path


def download_orbit_for_item(item: pystac.Item) -> None:
    """
    Resolve and download the orbit file for a single STAC item.
    Tries POEORB (precise, ~15-20 day lag) first, falls back to RESORB.
    """
    scene_start, scene_end = get_scene_window(item)
    if scene_start is None:
        print(f"[{item.id}] No datetime available, skipping.")
        return

    platform = get_platform_from_item(item)
    if not platform:
        print(f"[{item.id}] Cannot determine platform, skipping.")
        return

    print(f"[{item.id}] {platform} | {scene_start.isoformat()} → {scene_end.isoformat()}")

    out = download_orbit_esa(scene_start, scene_end, platform, "POEORB")
    if not out:
        out = download_orbit_esa(scene_start, scene_end, platform, "RESORB")

    if out:
        print(f"[{item.id}] Orbit ready: {out.name}")
    else:
        print(f"[{item.id}] No orbit found.")


def main() -> None:
    json_paths = get_stac_json_paths()
    if not json_paths:
        print("No STAC JSON files found.")
        return

    DATA_ORBIT_DIR.mkdir(parents=True, exist_ok=True)

    items: List[pystac.Item] = []
    for json_path in json_paths:
        try:
            item = pystac.read_file(json_path)
            assert isinstance(item, pystac.Item)
            items.append(item)
        except Exception as e:
            print(f"Failed to read {json_path.name}: {e}")

    # ThreadPoolExecutor provides real parallelism for blocking HTTP I/O.
    # asyncio + requests was wrong: async functions with synchronous requests
    # calls block the event loop — there is no actual concurrency.
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(download_orbit_for_item, item): item for item in items}
        for future in as_completed(futures):
            item = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"[{item.id}] Unhandled error: {e}")


if __name__ == "__main__":
    main()
