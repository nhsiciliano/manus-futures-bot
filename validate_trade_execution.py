#!/usr/bin/env python3
"""
Script de validación para la ejecución de trades
Verifica que todos los métodos necesarios estén implementados
"""

import os
import sys
import inspect
from datetime import datetime

# Configurar variables de entorno de prueba
if not os.getenv('BINANCE_API_KEY'):
    os.environ['BINANCE_API_KEY'] = 'test_key'
if not os.getenv('BINANCE_API_SECRET'):
    os.environ['BINANCE_API_SECRET'] = 'test_secret'

def validate_binance_client():
    """Validar que BinanceAPIClient tiene todos los métodos necesarios"""
    try:
        from binance_client import BinanceAPIClient
        
        # Verificar métodos críticos
        required_methods = [
            'place_futures_order',
            'get_account_balance',
            'test_connection',
            'get_klines'
        ]
        
        print("🔍 Validando BinanceAPIClient...")
        
        for method_name in required_methods:
            if hasattr(BinanceAPIClient, method_name):
                method = getattr(BinanceAPIClient, method_name)
                if callable(method):
                    print(f"✅ {method_name}: Método disponible")
                else:
                    print(f"❌ {method_name}: No es callable")
                    return False
            else:
                print(f"❌ {method_name}: Método faltante")
                return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Error al importar BinanceAPIClient: {e}")
        return False

def validate_trading_bot():
    """Validar que RobustTradingBot tiene la lógica de ejecución"""
    try:
        from main import RobustTradingBot
        
        print("🔍 Validando RobustTradingBot...")
        
        # Verificar método de ejecución de trades
        if hasattr(RobustTradingBot, '_execute_real_trade'):
            method = getattr(RobustTradingBot, '_execute_real_trade')
            if callable(method):
                print("✅ _execute_real_trade: Método implementado")
                
                # Verificar signature del método
                sig = inspect.signature(method)
                if 'analysis' in sig.parameters:
                    print("✅ _execute_real_trade: Signature correcta")
                else:
                    print("❌ _execute_real_trade: Signature incorrecta")
                    return False
            else:
                print("❌ _execute_real_trade: No es callable")
                return False
        else:
            print("❌ _execute_real_trade: Método faltante")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Error al importar RobustTradingBot: {e}")
        return False

def validate_risk_manager():
    """Validar que RiskManager tiene todos los métodos necesarios"""
    try:
        from risk_manager import RiskManager
        
        print("🔍 Validando RiskManager...")
        
        required_methods = [
            'calculate_position_size',
            'calculate_stop_loss',
            'calculate_take_profit',
            'check_risk_limits',
            'validate_trade_parameters',
            'can_open_new_position'
        ]
        
        for method_name in required_methods:
            if hasattr(RiskManager, method_name):
                print(f"✅ {method_name}: Método disponible")
            else:
                print(f"❌ {method_name}: Método faltante")
                return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Error al importar RiskManager: {e}")
        return False

def validate_position_manager():
    """Validar que PositionManager tiene los métodos necesarios"""
    try:
        from position_manager import PositionManager
        
        print("🔍 Validando PositionManager...")
        
        required_methods = [
            'add_position',
            'get_position',
            'get_all_positions'
        ]
        
        for method_name in required_methods:
            if hasattr(PositionManager, method_name):
                print(f"✅ {method_name}: Método disponible")
            else:
                print(f"❌ {method_name}: Método faltante")
                return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Error al importar PositionManager: {e}")
        return False

def main():
    """Ejecutar todas las validaciones"""
    print("=" * 60)
    print("🧪 VALIDACIÓN DE EJECUCIÓN DE TRADES")
    print("=" * 60)
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    validations = [
        ("BinanceAPIClient", validate_binance_client),
        ("RobustTradingBot", validate_trading_bot),
        ("RiskManager", validate_risk_manager),
        ("PositionManager", validate_position_manager)
    ]
    
    passed = 0
    total = len(validations)
    
    for name, validator in validations:
        print(f"\n📋 Validando {name}...")
        if validator():
            print(f"✅ {name}: VÁLIDO")
            passed += 1
        else:
            print(f"❌ {name}: FALLÓ")
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTADOS: {passed}/{total} validaciones pasaron")
    
    if passed == total:
        print("🎉 TODAS LAS VALIDACIONES PASARON")
        print("🚀 El bot está listo para ejecutar operaciones reales")
        print("\n⚠️  IMPORTANTE:")
        print("   - Asegúrate de tener balance suficiente en Binance Futures")
        print("   - Verifica que las API keys tengan permisos de trading")
        print("   - Comienza con un balance pequeño para pruebas")
        return True
    else:
        print("⚠️  ALGUNAS VALIDACIONES FALLARON")
        print("🔧 Corrige los errores antes del despliegue")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
