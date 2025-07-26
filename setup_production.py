#!/usr/bin/env python3
"""
Script de configuración para producción
Prepara el bot para despliegue en Render
"""

import os
import sys
import json
from pathlib import Path

def create_env_template():
    """Crear archivo .env de ejemplo para producción"""
    env_content = """# Configuración de Producción - Manus Trading Bot
# IMPORTANTE: Configurar estas variables en Render, NO en este archivo

# API de Binance (OBLIGATORIO)
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

# Configuración del Bot (OPCIONAL - ya tienen valores por defecto)
SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT
MAX_RISK_PER_TRADE=0.01
MAX_CONCURRENT_TRADES=2
RISK_REWARD_RATIO=1.5
TRAILING_STOP_PERCENT=0.0075
LOG_LEVEL=INFO
BOT_RUN_INTERVAL=60

# Configuración de Producción
ENVIRONMENT=production
"""
    
    with open('.env.production', 'w') as f:
        f.write(env_content)
    
    print("✅ Archivo .env.production creado")

def create_startup_script():
    """Crear script de inicio robusto para producción"""
    startup_content = """#!/usr/bin/env python3
import os
import sys
import asyncio
import logging
from datetime import datetime

# Configurar logging para producción
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('trading_bot.log')
    ]
)

logger = logging.getLogger(__name__)

async def start_bot():
    \"\"\"Iniciar el bot con manejo de errores robusto\"\"\"
    try:
        logger.info("🤖 Iniciando Manus Trading Bot en modo producción...")
        logger.info(f"Timestamp: {datetime.now()}")
        
        # Importar y ejecutar el bot principal
        from main import main
        await main()
        
    except KeyboardInterrupt:
        logger.info("Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"Error crítico en el bot: {str(e)}")
        logger.error("Reiniciando en 30 segundos...")
        await asyncio.sleep(30)
        # Reiniciar automáticamente
        await start_bot()

if __name__ == "__main__":
    asyncio.run(start_bot())
"""
    
    with open('start_production.py', 'w') as f:
        f.write(startup_content)
    
    # Hacer ejecutable
    os.chmod('start_production.py', 0o755)
    print("✅ Script de inicio para producción creado")

def validate_project_structure():
    """Validar que todos los archivos necesarios estén presentes"""
    required_files = [
        'main.py',
        'trading_strategy.py',
        'risk_manager.py',
        'position_manager.py',
        'binance_client.py',
        'technical_analysis.py',
        'config.py',
        'logger.py',
        'requirements.txt',
        'Dockerfile',
        'render.yaml'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Archivos faltantes: {', '.join(missing_files)}")
        return False
    else:
        print("✅ Todos los archivos necesarios están presentes")
        return True

def create_deployment_checklist():
    """Crear checklist de despliegue"""
    checklist = """# 🚀 Checklist de Despliegue - Manus Trading Bot

## Antes del Despliegue
- [ ] API Keys de Binance configuradas y probadas
- [ ] Permisos de API correctos (solo trading, NO retiros)
- [ ] Balance inicial en la cuenta de futuros
- [ ] Todos los archivos del proyecto subidos a GitHub

## Configuración en Render
- [ ] Servicio creado como "Background Worker"
- [ ] Variables de entorno configuradas:
  - [ ] BINANCE_API_KEY
  - [ ] BINANCE_API_SECRET
  - [ ] SYMBOLS (opcional)
  - [ ] MAX_RISK_PER_TRADE (opcional)
  - [ ] Otras variables opcionales según necesidad

## Post-Despliegue
- [ ] Bot iniciado correctamente
- [ ] Logs muestran conexión exitosa a Binance
- [ ] Monitoreo activo durante las primeras 24 horas
- [ ] Verificar que se generan señales de trading
- [ ] Confirmar que las operaciones se ejecutan correctamente

## Monitoreo Continuo
- [ ] Revisar logs diariamente
- [ ] Monitorear balance de la cuenta
- [ ] Verificar rendimiento semanal
- [ ] Ajustar parámetros si es necesario

## Contactos de Emergencia
- Render Support: https://render.com/support
- Binance API Docs: https://binance-docs.github.io/apidocs/
"""
    
    with open('deployment_checklist.md', 'w') as f:
        f.write(checklist)
    
    print("✅ Checklist de despliegue creado")

def main():
    """Ejecutar configuración completa para producción"""
    print("🔧 Configurando Manus Trading Bot para Producción")
    print("=" * 60)
    
    # Validar estructura del proyecto
    if not validate_project_structure():
        print("❌ Faltan archivos necesarios. Revisar el proyecto.")
        sys.exit(1)
    
    # Crear archivos de configuración
    create_env_template()
    create_startup_script()
    create_deployment_checklist()
    
    print("\n" + "=" * 60)
    print("🎉 Configuración completada!")
    print("\nPróximos pasos:")
    print("1. Revisar deployment_checklist.md")
    print("2. Configurar API Keys de Binance")
    print("3. Subir código a GitHub")
    print("4. Crear servicio en Render")
    print("5. Configurar variables de entorno")
    print("6. Desplegar y monitorear")
    print("\n📖 Ver deploy_guide.md para instrucciones detalladas")

if __name__ == "__main__":
    main()
