#!/usr/bin/env python3
"""
Health Check Script para el Trading Bot
Verifica que todos los componentes estén funcionando correctamente
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Importar componentes del bot
from binance_client import BinanceAPIClient
from config import BINANCE_API_KEY, BINANCE_API_SECRET, SYMBOLS

async def check_binance_connection():
    """Verificar conexión con Binance API"""
    try:
        client = BinanceAPIClient()
        await client.initialize()
        
        # Verificar que podemos obtener información de la cuenta
        account_info = await client.get_account_info()
        if account_info:
            print("✅ Conexión con Binance API: OK")
            print(f"   Balance USDT: {account_info.get('totalWalletBalance', 'N/A')}")
            return True
        else:
            print("❌ Error: No se pudo obtener información de la cuenta")
            return False
            
    except Exception as e:
        print(f"❌ Error de conexión con Binance: {str(e)}")
        return False

def check_environment_variables():
    """Verificar que todas las variables de entorno estén configuradas"""
    required_vars = ['BINANCE_API_KEY', 'BINANCE_API_SECRET']
    optional_vars = ['SYMBOLS', 'MAX_RISK_PER_TRADE', 'BOT_RUN_INTERVAL']
    
    print("🔍 Verificando variables de entorno...")
    
    all_good = True
    for var in required_vars:
        if not os.getenv(var):
            print(f"❌ Variable requerida faltante: {var}")
            all_good = False
        else:
            print(f"✅ {var}: Configurada")
    
    for var in optional_vars:
        value = os.getenv(var, 'Usando valor por defecto')
        print(f"ℹ️  {var}: {value}")
    
    return all_good

def check_market_data():
    """Verificar que podemos obtener datos de mercado"""
    try:
        from binance_client import BinanceAPIClient
        client = BinanceAPIClient()
        
        print("📊 Verificando datos de mercado...")
        for symbol in SYMBOLS[:2]:  # Solo verificar los primeros 2 símbolos
            klines = client.get_klines(symbol, '15m', 10)
            if klines is not None and not klines.empty:
                print(f"✅ Datos de {symbol}: OK ({len(klines)} velas)")
            else:
                print(f"❌ Error obteniendo datos de {symbol}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando datos de mercado: {str(e)}")
        return False

async def main():
    """Ejecutar todos los checks de salud"""
    print("🤖 Manus Trading Bot - Health Check")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    checks = []
    
    # Check 1: Variables de entorno
    env_ok = check_environment_variables()
    checks.append(env_ok)
    print()
    
    # Check 2: Conexión con Binance
    binance_ok = await check_binance_connection()
    checks.append(binance_ok)
    print()
    
    # Check 3: Datos de mercado
    market_ok = check_market_data()
    checks.append(market_ok)
    print()
    
    # Resultado final
    print("=" * 50)
    if all(checks):
        print("🎉 Todos los checks pasaron exitosamente!")
        print("El bot está listo para operar en producción.")
        sys.exit(0)
    else:
        print("⚠️  Algunos checks fallaron. Revisar configuración.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
