# Imagen base
FROM python:3.10-slim

# Establecer directorio
WORKDIR /app

# Copiar dependencias e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer puerto
EXPOSE 10000

# Comando para lanzar el bot
CMD ["python", "main.py"]



