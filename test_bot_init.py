import os
import sys
import asyncio
from unittest.mock import MagicMock, patch
import pandas as pd

# Añadir el directorio actual al path para que Python encuentre los módulos
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Mockear las variables de entorno para la prueba
os.environ["BINANCE_API_KEY"] = "TEST_API_KEY"
os.environ["BINANCE_API_SECRET"] = "TEST_API_SECRET"

# Importar el módulo config después de mockear las variables de entorno
import config

# Asegurarse de que config.py usa os.getenv correctamente
config.BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
config.BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")

from main import TradingBot
from binance_client import BinanceAPIClient
from trading_strategy import TradingStrategy
from risk_manager import RiskManager
from position_manager import PositionManager
from logger import TradingLogger

async def test_bot_initialization():
    print("\n--- Iniciando prueba de inicialización del bot ---")
    
    # Crear DataFrames simulados para klines de diferentes intervalos
    def create_mock_klines_df(rows=6):
        # Datos simulados para klines
        base_time = 1678886400000
        base_price = 20000.0
        mock_klines_data = []
        for i in range(rows):
            timestamp = base_time + i * 3600 * 1000
            price = base_price + i * 50
            mock_klines_data.append(
                [timestamp, price, price + 50, price - 50, price + 25, 100.0, 0,0,0,0,0,0]
            )

        df = pd.DataFrame(mock_klines_data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        # Convertir a tipos numéricos
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col])
        return df

    mock_klines_4h = create_mock_klines_df(200)
    mock_klines_15m = create_mock_klines_df(100)
    
    # Mockear la clase BinanceAPIClient directamente
    with patch('main.BinanceAPIClient') as MockBinanceAPIClientClass:
        mock_binance_client_instance = MagicMock(spec=BinanceAPIClient)
        mock_binance_client_instance.test_connection.return_value = True
        
        # Configurar get_klines para devolver el DataFrame correcto según el intervalo
        def mock_get_klines(symbol, interval, limit):
            if interval == config.INTERVAL_4H:
                return mock_klines_4h.copy()
            elif interval == config.INTERVAL_15M:
                return mock_klines_15m.copy()
            # Asegurarse de que siempre se devuelve un DataFrame, incluso si está vacío
            return pd.DataFrame() 

        mock_binance_client_instance.get_klines.side_effect = mock_get_klines
        mock_binance_client_instance.get_current_price.return_value = 20300.0
        mock_binance_client_instance.get_account_balance.return_value = 1000.0
        mock_binance_client_instance.get_open_positions.return_value = []
        mock_binance_client_instance.place_market_order.return_value = {'orderId': '12345'}
        mock_binance_client_instance.place_stop_loss_order.return_value = {'orderId': '12346'}
        mock_binance_client_instance.place_take_profit_order.return_value = {'orderId': '12347'}
        mock_binance_client_instance.cancel_order.return_value = True

        MockBinanceAPIClientClass.return_value = mock_binance_client_instance

        bot = TradingBot()
        
        # Desactivar el logger real para no escribir en archivo durante la prueba
        with patch.object(bot, 'logger', new=MagicMock()):
            bot.logger.log_bot_status = print
            bot.logger.log_error = print
            bot.logger.debug = print
            bot.logger.info = print

            if bot.initialize_components():
                print("✅ Bot inicializado correctamente (simulado).")
                
                # Verificar que los componentes se hayan asignado
                assert bot.binance_client is not None
                assert isinstance(bot.trading_strategy, TradingStrategy)
                assert isinstance(bot.risk_manager, RiskManager)
                assert isinstance(bot.position_manager, PositionManager)
                print("✅ Componentes del bot verificados.")
                
                # Simular un ciclo de análisis (sin ejecución de trades reales)
                print("Simulando un ciclo de análisis de mercado...")
                analysis_results = await bot.analyze_markets()
                print(f"Análisis completado para {len(analysis_results)} símbolos.")
                print("✅ Ciclo de análisis simulado con éxito.")
                
                # Simular monitoreo de posiciones (sin trades reales)
                print("Simulando monitoreo de posiciones...")
                await bot.monitor_positions()
                print("✅ Monitoreo de posiciones simulado con éxito.")
                
            else:
                print("❌ Fallo en la inicialización del bot.")
            
            print("--- Prueba de inicialización del bot finalizada ---")

if __name__ == "__main__":
    asyncio.run(test_bot_initialization())

