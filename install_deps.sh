#!/bin/bash
# Script de instalación de dependencias para Render
# Resuelve problemas de compatibilidad numpy/pandas

echo "🔧 Instalando dependencias para Manus Trading Bot..."

# Actualizar pip y herramientas base
pip install --upgrade pip setuptools wheel

# Instalar numpy primero (versión específica)
echo "📦 Instalando numpy..."
pip install numpy==1.24.3

# Instalar pandas (compatible con numpy)
echo "📦 Instalando pandas..."
pip install pandas==2.0.3

# Instalar pandas-ta
echo "📦 Instalando pandas-ta..."
pip install pandas-ta==0.3.14b0

# Instalar python-binance
echo "📦 Instalando python-binance..."
pip install python-binance==1.0.19

# Instalar utilidades
echo "📦 Instalando utilidades..."
pip install python-dotenv==1.0.0
pip install requests==2.31.0
pip install aiohttp==3.8.5
pip install websockets==11.0.3

echo "✅ Instalación completada!"
echo "🚀 Listo para ejecutar el bot de trading"
