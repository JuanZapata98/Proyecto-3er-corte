# Proyecto-3er-corte

## **1. Introducción**
En este proyecto se desarrolla un sistema para la recolección, validación y procesamiento de imágenes correspondientes a elementos presentes en los laboratorios de la Universidad Santo Tomás.  
El objetivo principal es crear una base de datos confiable que permita su uso en aplicaciones posteriores como inventarios, catálogos digitales o modelos de visión por computadora.

El proyecto integra conceptos de:
- Web Scraping  
- Procesos ETL (Extracción – Transformación – Carga)  
- Validación automática de imágenes  
- Concurrencia (hilos, semáforos, mutex)  
- Buenas prácticas éticas en recolección de datos

---

## **2. Objetivos**

### **2.1 Objetivo general**
Implementar un sistema automatizado capaz de obtener, filtrar y procesar imágenes de equipos de laboratorio, garantizando su calidad y clasificación adecuada.

### **2.2 Objetivos específicos**
1. Desarrollar un **scraper** configurable para recolectar imágenes desde diversas fuentes web.  
2. Implementar un pipeline **ETL** que valide, limpie y transforme las imágenes obtenidas.  
3. Organizar las imágenes en un dataset estructurado por categoría.  
4. Aplicar **métodos de concurrencia** para optimizar el rendimiento del scraping y procesamiento.  
5. Documentar el proceso siguiendo el formato de un laboratorio académico.

---

## **3. Materiales y Herramientas**

### **Software**
- Python 3.11
- Bibliotecas:
  - `requests`, `beautifulsoup4`
  - `pillow` y `opencv-python`
  - `imagehash`
  - `sqlalchemy`
  - `streamlit`
  - `tqdm`

### **Hardware**
- Equipo con conexión a Internet  
- Almacenamiento suficiente para el dataset (1–3 GB recomendado)

---

## **4. Instalación del Entorno (Uso de Docker)**

En este proyecto no se utiliza un entorno virtual local, ya que todo el procesamiento se ejecutará dentro de un contenedor Docker especialmente configurado para el scraper y el pipeline ETL.

### **4.1 Requisitos previos**
- Docker instalado (Docker Engine o Docker Desktop)

### **4.2 Construcción de la imagen**
Ejecutar desde la raíz del proyecto:

```bash
docker build -t laboratorio-imagenes .
```

### **4.3 Ejecutar el contenedor**

Incluyendo persistencia sobre `data/` y `src/`:

``` bash
docker run -it --name laboratorio   -v $(pwd)/data:/app/data   -v $(pwd)/src:/app/src   laboratorio-imagenes
```

### **4.4 Ejecutar el scraper dentro del contenedor**

``` bash
python src/scraper/scraper.py -k "oscilloscope" "multimeter" "function generator" "dc power supply" "raspberry pi" "ac power supply" "breadboard" "transformer" "breaker""function generator",
    "dc power supply",
    "raspberry pi",
    "ac power supply",
    "breadboard",
    "transformer",
    "breaker",
    "arduino" "arduino" -p 200 -o data/raw
```

### **4.5 Ejecutar procesos ETL**

``` bash
python src/etl/transform.py --input data/raw --out data/processed --workers 8
```

------------------------------------------------------------------------

## **5. Estructura del Proyecto**

    /
    ├─ data/
    │  ├─ raw/            # Imágenes descargadas
    │  └─ processed/      # Imágenes transformadas
    ├─ images/            # Imágenes usadas en documentación
    ├─ src/
    │  ├─ scraper/
    │  │  └─ scraper.py
    │  ├─ etl/
    │  │  ├─ extract.py
    │  │  ├─ transform.py
    │  │  └─ load.py
    │  └─ app/
    │     └─ streamlit_app.py
    ├─ configs/
    │  └─ scraper_config.yml
    ├─ Dockerfile
    ├─ README.md
    └─ LICENSE

------------------------------------------------------------------------

## **6. Procedimiento Experimental**

### **6.1 Actividad 1 --- Web Scraping**

#### **Descripción**

Se implementa un scraper que recolecta imágenes mediante búsquedas
basadas en palabras clave.\
Las imágenes corresponden a elementos típicos de laboratorio: fuentes de
poder, multímetros, protoboards, osciloscopios, entre otros.

#### **Ejecución del scraper**

``` bash
python src/scraper/scraper.py -k "oscilloscope" "multimeter" -p 100 -o data/raw
```

#### **Criterios de recolección**

-   Al menos **10 categorías de elementos**\
-   Aproximadamente **200 imágenes por categoría**\
-   Respetar políticas `robots.txt`\
-   Evitar páginas con restricciones de scraping

#### **Observaciones importantes del scraper**

-   El uso de `hash()` para nombres no es estable → reemplazar por
    `hashlib.md5`\
-   Deducción de extensión basada en URL → debe hacerse desde
    `Content-Type`\
-   Falta validación con PIL (`Image.verify()`)\
-   Falta registro estructurado de metadatos\
-   No implementa reintentos automáticos ni backoff\
-   No usa semáforos para limitar descargas simultáneas

------------------------------------------------------------------------

### **6.2 Actividad 2 --- Proceso ETL**

#### **Extracción**

-   Lectura de imágenes descargadas\
-   Lectura y parseo de metadatos (si aplica)

#### **Transformación**

-   Apertura y validación con PIL\
-   Conversión a RGB\
-   Redimensionamiento (ej. 256×256)\
-   Eliminación de duplicados con pHash\
-   Eliminación de imágenes dañadas o irrelevantes

#### **Carga**

-   Guardar imágenes limpias en `data/processed/`\
-   Registrar metadatos en CSV, JSONL o base de datos

Ejemplo:

``` bash
python src/etl/transform.py --input data/raw --out data/processed --workers 8
```

------------------------------------------------------------------------

## **7. Manejo de Concurrencia**

El sistema recomienda usar un modelo **producer--consumer**.

### **Componentes**

-   **Queue** → almacena URLs por procesar\
-   **Semaphore** → limita descargas concurrentes\
-   **Lock (mutex)** → protege escritura de metadatos

### **Pseudocódigo**

``` python
url_queue = Queue()
db_lock = Lock()
download_sem = Semaphore(5)

def producer():
    descubrir_urls()
    url_queue.put(url)

def consumer():
    with download_sem:
        descargar_imagen()
    with db_lock:
        escribir_metadatos()
```

------------------------------------------------------------------------

## **8. Resultados Esperados**

-   Dataset organizado por categoría\
-   Imágenes validadas, limpias, sin duplicados\
-   Metadatos completos para cada imagen\
-   Pipeline reproducible dentro de Docker\
-   Base funcional para entrenamiento de modelos o visualización en
    Streamlit

------------------------------------------------------------------------

## **9. Conclusiones**

-   El scraping facilita la construcción de datasets grandes, pero
    requiere control ético y técnico.\
-   La fase ETL garantiza la **calidad** del dataset final.\
-   La concurrencia acelera el proceso, pero exige sincronización
    adecuada.\
-   Docker proporciona un entorno reproducible y portable.\
-   El scraper inicial requiere mejoras para uso en producción.

------------------------------------------------------------------------
