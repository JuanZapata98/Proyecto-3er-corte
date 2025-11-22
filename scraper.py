# -*- coding: utf-8 -*-

import os
import re
import time
import json
import argparse
import requests
from urllib.parse import urlencode
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36"
}

VALID_EXT = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")

DEFAULT_KEYWORDS = [
    "multimeter",
    "oscilloscope",
    "function generator",
    "dc power supply"
]


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def ensure_folder(folder):
    os.makedirs(folder, exist_ok=True)


def get_vqd_token(query):
    """Obtiene el token necesario para la API no oficial de DuckDuckGo."""
    params = {"q": query}
    url = "https://duckduckgo.com/?" + urlencode(params)
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    # buscar token vqd
    m = re.search(r"vqd='([\d-]+)'", resp.text)
    if not m:
        m = re.search(r'vqd="([\d-]+)"', resp.text)
    if not m:
        m = re.search(r'vqd=([\d-]+)&', resp.text)
    return m.group(1) if m else None


def duckduckgo_search_images(query, max_results=30):
    """Obtiene URLs de imágenes usando el endpoint no oficial de DDG."""
    urls = []

    vqd = get_vqd_token(query)
    if not vqd:
        print(" No se pudo obtener token vqd. Intentando método simple…")
        return fallback_search_ddg(query, max_results)

    session = requests.Session()
    session.headers.update(HEADERS)

    params = {
        "l": "us-en",
        "o": "json",
        "q": query,
        "vqd": vqd
    }
    endpoint = "https://duckduckgo.com/i.js"

    while len(urls) < max_results:
        try:
            r = session.get(endpoint, params=params, timeout=15)
            r.raise_for_status()

            data = r.json()
            results = data.get("results", [])

            if not results:
                break

            for item in results:
                img = item.get("image") or item.get("thumbnail")
                if img:
                    urls.append(img)
                    if len(urls) >= max_results:
                        break

            if "next" in data:
                endpoint = "https://duckduckgo.com" + data["next"]
            else:
                break

            time.sleep(0.3)

        except Exception:
            break

    return urls[:max_results]


def fallback_search_ddg(query, max_results=30):
    """Método muy simple: scrapea el HTML del buscador (menos imágenes)."""
    urls = []
    url = "https://duckduckgo.com/?q=" + urlencode({"q": query})

    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    for img in soup.select("img"):
        src = img.get("src") or img.get("data-src")
        if src and src.startswith("http"):
            urls.append(src)
            if len(urls) >= max_results:
                break

    return urls[:max_results]


def download_image(url, folder):
    """Descarga una imagen y valida el content-type."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.raise_for_status()
    except Exception as e:
        return False, f"Request error: {e}"

    ct = r.headers.get("Content-Type", "")
    if not ct.startswith("image/"):
        return False, f"Not image: {ct}"

    ext = ".jpg"
    for e in VALID_EXT:
        if url.lower().endswith(e):
            ext = e
            break

    fname = f"{int(time.time()*1000)}_{abs(hash(url))%999999}{ext}"
    path = os.path.join(folder, fname)

    with open(path, "wb") as f:
        f.write(r.content)

    return True, path


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def gather_and_download(keywords, per_kw=20, folder="imagenes"):
    ensure_folder(folder)
    seen = set()
    total = 0

    for kw in keywords:
        print(f"\n=== Buscando '{kw}' ===")
        urls = duckduckgo_search_images(kw, max_results=per_kw)
        print(f"Encontradas {len(urls)} URLs")

        count_kw = 0
        for u in urls:
            if u in seen:
                continue
            seen.add(u)

            ok, info = download_image(u, folder)
            if ok:
                print(" + descargada:", info)
                total += 1
                count_kw += 1
            else:
                print("   error:", info)

            time.sleep(0.15)

        print(f"Descargadas para '{kw}': {count_kw}")

    print(f"\nTotal descargadas: {total}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", "-k", nargs="+", help="Keywords a buscar")
    parser.add_argument("--per", "-p", type=int, default=20, help="Imágenes por keyword")
    parser.add_argument("--out", "-o", default="imagenes", help="Carpeta salida")

    args = parser.parse_args()

    kws = args.keywords if args.keywords else DEFAULT_KEYWORDS

    gather_and_download(kws, per_kw=args.per, folder=args.out)
