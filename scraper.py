# -*- coding: utf-8 -*-
"""
Scraper de imágenes usando Bing (HTML), compatible con Docker y MySQL.
"""

import os
import re
import time
import argparse
import requests
import mysql.connector
from PIL import Image
from urllib.parse import urlencode
from bs4 import BeautifulSoup

# -------- CONFIG (sobrescribibles vía variables de entorno) ----------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121 Safari/537.36"
}

VALID_EXT = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")

DEFAULT_KEYWORDS = [
    "multimeter",
    "oscilloscope",
    "function generator",
    "dc power supply"
]

# --- Base de datos desde variables de entorno (Docker-friendly)
DB_HOST = os.getenv("DB_HOST", "host.docker.internal")
DB_USER = os.getenv("DB_USER", "etl_user")
DB_PASS = os.getenv("DB_PASS", "12345")
DB_NAME = os.getenv("DB_NAME", "etl_imagenes")

# -------- Helpers -------------------------------------------------------
def ensure_folder(folder):
    os.makedirs(folder, exist_ok=True)

def _log(*args):
    print(*args)

# -------- BING SCRAPER ---------------------------------------------------
def bing_search_images(query, max_results=200, session=None):
    """
    Scraper de imágenes de Bing vía HTML.
    No requiere API, no tiene límite inferior, funciona perfecto en Docker.
    """
    session = session or requests.Session()
    session.headers.update(HEADERS)

    search_url = "https://www.bing.com/images/search"
    params = {"q": query, "form": "HDRSC2"}

    try:
        r = session.get(search_url, params=params, timeout=20)
        r.raise_for_status()
    except Exception as e:
        _log("[ERROR] Bing request failed:", e)
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    urls = []

    # "iusc" contiene JSON con murl/turl
    for tag in soup.find_all("a", class_="iusc"):
        try:
            m_json = tag.get("m")
            if not m_json:
                continue

            # Bing envía string estilo dict, lo convertimos
            data = eval(m_json)  # seguro para este caso específico
            url = data.get("murl")

            if url and url.startswith("http"):
                urls.append(url)
                if len(urls) >= max_results:
                    break
        except Exception:
            continue

    return urls

# -------- DB helper ----------------------------------------------------
def save_metadata_to_mysql(keyword, url, local_path):
    """
    Inserta metadatos de imágenes en MySQL.
    """
    try:
        width = height = size_bytes = None

        try:
            img = Image.open(local_path)
            width, height = img.size
            size_bytes = os.path.getsize(local_path)
        except Exception as e:
            _log("[WARN] No se pudo leer metadatos de imagen:", e)

        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", DB_HOST),
            user=os.getenv("DB_USER", DB_USER),
            password=os.getenv("DB_PASS", DB_PASS),
            database=os.getenv("DB_NAME", DB_NAME),
            connection_timeout=10
        )
        cur = conn.cursor()

        sql = """
            INSERT INTO imagenes (keyword, url, local_path, width, height, size_bytes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        cur.execute(sql, (keyword, url, local_path, width, height, size_bytes))
        conn.commit()
        cur.close()
        conn.close()

        _log(f"   [BD] Metadatos guardados → {local_path}")

    except mysql.connector.Error as e:
        _log("[BD] Error MySQL:", e)
    except Exception as e:
        _log("[BD] Error general:", e)

# -------- DOWNLOAD ------------------------------------------------------
def download_image(url, folder, keyword, session=None):
    """
    Descarga imagen con validación y la guarda.
    Retorna (True, path) o (False, error)
    """
    session = session or requests.Session()
    ensure_folder(folder)

    for attempt in range(1, 4):
        try:
            r = session.get(url, headers=HEADERS, timeout=12, stream=True)
            r.raise_for_status()

            ctype = r.headers.get("Content-Type", "")
            if not ctype.startswith("image/"):
                return False, f"No es imagen (Content-Type={ctype})"

            # Detectar extensión
            ext = ".jpg"
            lower = url.lower().split("?")[0]
            for e in VALID_EXT:
                if lower.endswith(e):
                    ext = e
                    break

            fname = f"{int(time.time()*1000)}_{abs(hash(url))%999999}{ext}"
            path = os.path.join(folder, fname)

            with open(path, "wb") as f:
                for chunk in r.iter_content(1024*8):
                    if chunk:
                        f.write(chunk)

            save_metadata_to_mysql(keyword, url, path)

            return True, path
        except Exception as e:
            _log(f"[WARN] Reintento {attempt} falló para {url}: {e}")
            time.sleep(0.5 * attempt)

    return False, "Falló tras 3 intentos"

# -------- Orchestrator --------------------------------------------------
def gather_and_download(keywords, per_kw=200, folder="imagenes"):
    ensure_folder(folder)
    seen = set()
    total = 0

    session = requests.Session()
    session.headers.update(HEADERS)

    for kw in keywords:
        _log(f"\n=== BING: Buscando '{kw}' ===")
        urls = bing_search_images(kw, max_results=per_kw, session=session)
        _log(f"Encontradas {len(urls)} URLs")

        count_kw = 0

        for u in urls:
            if u in seen:
                continue
            seen.add(u)

            ok, info = download_image(u, folder, kw, session=session)
            if ok:
                _log(" + descargada:", info)
                total += 1
                count_kw += 1
            else:
                _log("   error:", info)

            time.sleep(0.10)

        _log(f"Descargadas para '{kw}': {count_kw}")

    _log(f"\nTOTAL descargadas: {total}")

# -------- CLI -----------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", "-k", nargs="+", help="Keywords a buscar")
    parser.add_argument("--per", "-p", type=int, default=200, help="Imágenes por keyword")
    parser.add_argument("--out", "-o", default="imagenes", help="Carpeta de salida")
    args = parser.parse_args()

    kws = args.keywords if args.keywords else DEFAULT_KEYWORDS
    gather_and_download(kws, per_kw=args.per, folder=args.out)
