# Usar una imagen base de Python oficial (más estable)
FROM python:3.11-slim

# Instalar Chromium y dependencias necesarias para Selenium
# Usamos --fix-missing y forzamos la instalación
RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    wget \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configurar variables de entorno para Chromium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PYTHONUNBUFFERED=1

# Establecer directorio de trabajo
WORKDIR /app

# Copiar el archivo de requisitos primero (mejor para caché)
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el script
COPY gps_scraper.py .

# Crear directorio para resultados
RUN mkdir -p /app/resultados /app/logs

# Ejecutar el script
CMD ["python", "gps_scraper.py"]
