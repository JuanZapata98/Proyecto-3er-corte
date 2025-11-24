FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copiar e instalar dependencias python
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copiar código
COPY scraper.py /app/scraper.py
COPY run.sh /app/run.sh

# Crear carpetas para persistencia (opcional)
RUN mkdir -p /app/imagenes

# Comando por defecto
CMD ["bash", "-lc", "python scraper.py"]
