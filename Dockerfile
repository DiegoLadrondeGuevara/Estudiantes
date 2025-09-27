# Usa imagen base con Python
FROM python:3.11-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de la app
COPY . .

# Instala dependencias
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy pydantic email-validator

# Expone el puerto donde corre FastAPI
EXPOSE 8000

# Comando para iniciar la app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
