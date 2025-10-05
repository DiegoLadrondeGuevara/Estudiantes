FROM python:3.11-slim

WORKDIR /app

COPY . .

# Instalar dependencias del sistema necesarias para psycopg2 y compilación
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Instala las dependencias usando el requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
