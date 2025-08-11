# Usar Python 3.11 slim como imagen base
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Actualizar pip y setuptools
RUN pip install --upgrade pip setuptools wheel

# Copiar requirements y instalar dependencias de Python
COPY requirements.txt .

# Instalar numpy primero para evitar conflictos binarios
RUN pip install --no-cache-dir numpy==1.24.3

# Instalar el resto de dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Crear directorio para logs
RUN mkdir -p /app/logs

# Exponer puerto (aunque no es necesario para este bot)
EXPOSE 8000

# Comando para ejecutar el bot
CMD ["python", "main_robust.py"]
