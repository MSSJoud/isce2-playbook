import asyncio
import re
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

import pystac
import requests
from bs4 import BeautifulSoup
from settings import DATA_ORBIT_DIR, DATA_STAC_DIR
from datetime import datetime, timedelta, timezone

# URLs base da ESA (POEORB e RESORB)
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


def get_platform_and_orbit_from_item(item: pystac.Item) -> Tuple[Optional[str], Optional[int]]:
    """
    Extrai plataforma (S1A, S1B) e número da órbita relativa do item.
    Normaliza diferentes formas de escrita.
    """
    platform = None
    # Mapeamento de possíveis valores para o código padrão S1A/S1B
    platform_map = {
        "sentinel-1a": "S1A",
        "sentinel-1b": "S1B",
        "s1a": "S1A",
        "s1b": "S1B",
        "S1A": "S1A",
        "S1B": "S1B",
        "SENTINEL-1A": "S1A",
        "SENTINEL-1B": "S1B",
    }

    # Tenta obter a plataforma da propriedade 'platform'
    raw_platform = item.properties.get('platform', '').lower()
    if raw_platform:
        platform = platform_map.get(raw_platform)
        if platform:
            print(f"Plataforma identificada via properties: {raw_platform} -> {platform}")
        else:
            print(f"Valor não mapeado em properties: {raw_platform}")

    # Se não conseguiu, tenta pelo ID (ex: S1A_IW_SLC...)
    if not platform:
        if item.id.startswith('S1A'):
            platform = "S1A"
        elif item.id.startswith('S1B'):
            platform = "S1B"
        if platform:
            print(f"Plataforma identificada via ID: {platform}")

    # Número da órbita relativa
    orbit = item.properties.get('sat:relative_orbit')

    return platform, orbit


def parse_orbit_filename(filename: str) -> Optional[Tuple[datetime, datetime]]:
    """
    Extrai do nome do arquivo .EOF os timestamps de início e fim de validade.
    Exemplo: S1A_OPER_AUX_POEORB_OPOD_20210304T120252_V20210211T225942_20210213T005942.EOF
    Retorna (start_valid, end_valid) como datetime com timezone UTC ou None.
    """
    # Remove extensão .zip se existir
    if filename.endswith('.zip'):
        filename = filename[:-4]
    # Padrão: _V(YYYYMMDDTHHMMSS)_(YYYYMMDDTHHMMSS).EOF
    match = re.search(r'_V(\d{8}T\d{6})_(\d{8}T\d{6})\.EOF$', filename)
    if not match:
        return None
    start_str, end_str = match.groups()
    try:
        # Adiciona timezone UTC
        start = datetime.strptime(start_str, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
        end = datetime.strptime(end_str, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
        return start, end
    except ValueError:
        return None


def unzip_file(zip_path: Path, delete_zip: bool = True) -> Optional[Path]:
    """
    Descompacta um arquivo .EOF.zip e retorna o caminho do .EOF extraído.
    Se delete_zip=True, remove o zip após extração.
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            # Assume que há apenas um arquivo .EOF dentro
            eof_files = [f for f in z.namelist() if f.endswith('.EOF')]
            if not eof_files:
                print(f"Nenhum arquivo .EOF encontrado dentro de {zip_path.name}")
                return None
            # Extrai para o mesmo diretório
            z.extract(eof_files[0], path=zip_path.parent)
            extracted = zip_path.parent / eof_files[0]
            print(f"Extraído: {extracted}")
            if delete_zip:
                zip_path.unlink()
                print(f"Zip removido: {zip_path.name}")
            return extracted
    except Exception as e:
        print(f"Erro ao descompactar {zip_path}: {e}")
        return None


async def download_orbit_esa(date: datetime, platform: str, orbit_type: str = "POEORB") -> Optional[Path]:
    """
    Baixa a órbita para uma data específica do repositório ESA.
    Retorna o caminho do arquivo .EOF final (já descompactado) ou None.
    """
    # Escolhe a URL base conforme plataforma e tipo
    if orbit_type == "POEORB":
        base_url = BASE_URL_POEORB.get(platform)
    else:
        base_url = BASE_URL_RESORB.get(platform)

    if not base_url:
        print(f"Plataforma {platform} não suportada para {orbit_type}")
        return None

    # Ano da data (as órbitas estão organizadas por ano)
    year = date.year
    # Mês (opcional, mas pode ajudar a reduzir a lista de links)
    month = f"{date.month:02d}"
    # Tenta primeiro acessar a subpasta do mês (se existir)
    possible_urls = [f"{base_url}{year}/{month}/", f"{base_url}{year}/"]

    all_links = []
    for url in possible_urls:
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Busca links que terminam com .EOF ou .EOF.zip
            links = [a.get('href') for a in soup.find_all('a') 
                     if a.get('href', '').endswith(('.EOF', '.EOF.zip'))]
            all_links.extend(links)
            if links:
                break  # Se encontrou links, não precisa tentar a próxima URL
        except Exception as e:
            print(f"Erro ao acessar {url}: {e}")
            continue

    if not all_links:
        print(f"Nenhum link encontrado para {platform} {year}")
        return None

    best_file = None
    best_diff = timedelta.max

    for link in all_links:
        filename = link.split('/')[-1]  # extrai só o nome do arquivo
        validity = parse_orbit_filename(filename)
        if not validity:
            continue
        start, end = validity

        # Verifica se a data da cena está dentro do intervalo de validade
        if start <= date <= end:
            # Se houver vários, escolhe o que tem o centro mais próximo da data
            mid = start + (end - start) / 2
            diff = abs(mid - date)
            if diff < best_diff:
                best_diff = diff
                best_file = filename

    if best_file:
        # Determina a URL correta (pode estar no mês ou no ano)
        # Para simplificar, tenta o mesmo URL de onde veio o link
        # (mas o link pode ser relativo, então precisamos construir a URL completa)
        file_url = None
        for url in possible_urls:
            test_url = url + best_file
            try:
                head = requests.head(test_url, timeout=10)
                if head.status_code == 200:
                    file_url = test_url
                    break
            except:
                continue
        if not file_url:
            print(f"Não foi possível encontrar URL para {best_file}")
            return None

        # Caminho de saída (inicialmente .EOF.zip, depois será extraído)
        out_path = DATA_ORBIT_DIR / best_file
        try:
            print(f"Baixando {best_file} de {file_url} ...")
            with requests.get(file_url, stream=True) as r:
                r.raise_for_status()
                with open(out_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"Download concluído: {out_path}")

            # Se for um zip, descompacta
            if out_path.suffix == '.zip':
                eof_path = unzip_file(out_path, delete_zip=True)
                return eof_path
            else:
                return out_path
        except Exception as e:
            print(f"Erro ao baixar {file_url}: {e}")
            return None
    else:
        print(f"Nenhuma órbita {orbit_type} encontrada para {date.date()}")
        return None


async def download_orbit_for_item(item: pystac.Item) -> None:
    date = item.datetime
    if date is None:
        print(f"Item {item.id} sem datetime, pulando.")
        return

    platform, orbit = get_platform_and_orbit_from_item(item)
    if not platform:
        print(f"Plataforma não identificada para {item.id}")
        return

    print(f"Processando {platform} - data {date}")

    # Tenta POEORB (precisa) primeiro
    out = await download_orbit_esa(date, platform, "POEORB")
    if not out:
        # Se não achar, tenta RESORB (restituída)
        out = await download_orbit_esa(date, platform, "RESORB")

    if out:
        print(f"Órbita salva em {out}")
    else:
        print(f"Nenhuma órbita encontrada para {item.id}")


async def main_async():
    json_paths = get_stac_json_paths()
    if not json_paths:
        print("Nenhum arquivo JSON encontrado.")
        return

    DATA_ORBIT_DIR.mkdir(parents=True, exist_ok=True)

    tasks = []
    for json_path in json_paths:
        try:
            item = pystac.read_file(json_path)
            assert isinstance(item, pystac.Item)
            tasks.append(download_orbit_for_item(item))
        except Exception as e:
            print(f"Erro ao ler {json_path}: {e}")

    await asyncio.gather(*tasks)


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()