# Proyecto-3er-corte
1. Resumen

La Universidad (Santoto) requiere automatizar la recolección y procesamiento de imágenes de equipos de laboratorio:

Objetivo principal: Crear una base de datos con imágenes de ≥10 elementos de laboratorio (~200 imágenes por elemento).

Pipeline: web scraping → pre-procesamiento/limpieza (ETL) → almacenamiento (disk/DB) → despliegue en Streamlit.

El repositorio de referencia usado: https://github.com/Sosa21-byte/Laboratorio-5.

2. Archivos relevantes

Scraper subido: /mnt/data/scraper.py
(mueve este archivo a src/scraper/scraper.py si deseas organizar el repo).

3. Requisitos e instalación rápida

Recomendado: crear y activar un entorno virtual.

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


Ejemplo requirements.txt sugerido:

requests
beautifulsoup4
selenium          # si usas páginas con JS
pillow
opencv-python
imagehash
sqlalchemy
psycopg2-binary   # opcional, si usas Postgres
streamlit
tqdm
