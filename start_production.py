#!/usr/bin/env python3
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
    """Iniciar el bot con manejo de errores robusto"""
    try:
        logger.info("🤖 Iniciando Manus Trading Bot en modo producción...")
        logger.info(f"Timestamp: {datetime.now()}")
        
        # Importar y ejecutar el bot principal
        from main_robust import main_with_retry as main
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
