import logging
import time
from typing import Dict, List, Optional, Any
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import pandas as pd

class BinanceAPIClient:
    """Cliente para interactuar con la API de Binance Futures"""
    
    def __init__(self, api_key: str, api_secret: str):
        """
        Inicializar el cliente de Binance
        
        Args:
            api_key: Clave API de Binance
            api_secret: Clave secreta de Binance
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = None
        self.logger = logging.getLogger(__name__)
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializar la conexión con Binance"""
        try:
            self.client = Client(self.api_key, self.api_secret)
            # Configurar apalancamiento seguro para todos los símbolos
            self._set_leverage_for_symbols()
            self.logger.info("Cliente de Binance inicializado correctamente")
        except Exception as e:
            self.logger.error(f"Error al inicializar cliente de Binance: {e}")
            raise
    
    def _set_leverage_for_symbols(self):
        """Configurar apalancamiento para todos los símbolos de trading"""
        try:
            import config
            leverage = config.LEVERAGE
            
            for symbol in config.SYMBOLS:
                try:
                    self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
                    self.logger.info(f"🔧 Apalancamiento configurado: {symbol} = {leverage}x")
                except Exception as e:
                    self.logger.warning(f"⚠️ No se pudo configurar apalancamiento para {symbol}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error al configurar apalancamiento: {e}")
    
    def get_account_balance(self) -> float:
        """
        Obtener el balance de la cuenta de futuros
        
        Returns:
            Balance total en USDT
        """
        try:
            account_info = self.client.futures_account()
            total_balance = float(account_info["totalWalletBalance"])
            self.logger.debug(f"Balance de cuenta: {total_balance} USDT")
            return total_balance
        except BinanceAPIException as e:
            self.logger.error(f"Error al obtener balance: {e}")
            return 0.0
    
    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
        """
        Obtener datos de velas (klines)
        
        Args:
            symbol: Par de trading (ej. 'BTCUSDT')
            interval: Intervalo de tiempo (ej. '15m', '4h')
            limit: Número de velas a obtener
            
        Returns:
            DataFrame con datos de velas
        """
        try:
            klines = self.client.futures_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convertir a tipos numéricos
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            self.logger.debug(f"Obtenidas {len(df)} velas para {symbol} en {interval}")
            return df
            
        except BinanceAPIException as e:
            self.logger.error(f"Error al obtener klines para {symbol}: {e}")
            return pd.DataFrame() # Asegurarse de devolver un DataFrame vacío en caso de error
    
    def get_current_price(self, symbol: str) -> float:
        """
        Obtener el precio actual de un símbolo
        
        Args:
            symbol: Par de trading
            
        Returns:
            Precio actual
        """
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            price = float(ticker["price"])
            self.logger.debug(f"Precio actual de {symbol}: {price}")
            return price
        except BinanceAPIException as e:
            self.logger.error(f"Error al obtener precio de {symbol}: {e}")
            return 0.0
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict:
        """
        Colocar una orden de mercado
        
        Args:
            symbol: Par de trading
            side: 'BUY' o 'SELL'
            quantity: Cantidad a operar
            
        Returns:
            Información de la orden
        """
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            self.logger.info(f"Orden de mercado colocada: {side} {quantity} {symbol}")
            return order
        except BinanceOrderException as e:
            self.logger.error(f"Error al colocar orden de mercado: {e}")
            return {}
    
    def place_stop_loss_order(self, symbol: str, side: str, quantity: float, stop_price: float) -> Dict:
        """
        Colocar una orden de stop loss
        
        Args:
            symbol: Par de trading
            side: 'BUY' o 'SELL'
            quantity: Cantidad
            stop_price: Precio de activación del stop
            
        Returns:
            Información de la orden
        """
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='STOP_MARKET',
                quantity=quantity,
                stopPrice=stop_price
            )
            self.logger.info(f"Stop loss colocado: {side} {quantity} {symbol} @ {stop_price}")
            return order
        except BinanceOrderException as e:
            self.logger.error(f"Error al colocar stop loss: {e}")
            return {}
    
    def place_take_profit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict:
        """
        Colocar una orden de take profit
        
        Args:
            symbol: Par de trading
            side: 'BUY' o 'SELL'
            quantity: Cantidad
            price: Precio objetivo
            
        Returns:
            Información de la orden
        """
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='TAKE_PROFIT_MARKET',
                quantity=quantity,
                stopPrice=price
            )
            self.logger.info(f"Take profit colocado: {side} {quantity} {symbol} @ {price}")
            return order
        except BinanceOrderException as e:
            self.logger.error(f"Error al colocar take profit: {e}")
            return {}
    
    def place_futures_order(self, symbol: str, side: str, quantity: float, order_type: str = 'MARKET') -> Dict:
        """
        Colocar una orden de futuros en Binance
        
        Args:
            symbol: Par de trading (ej. 'BTCUSDT')
            side: 'BUY' o 'SELL'
            quantity: Cantidad a operar
            order_type: Tipo de orden ('MARKET', 'LIMIT', etc.)
            
        Returns:
            Información de la orden ejecutada
        """
        try:
            self.logger.info(f"🔄 Ejecutando orden {side} {order_type} para {quantity:.6f} {symbol}")
            
            # Crear la orden en Binance Futures
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity
            )
            
            self.logger.info(f"✅ Orden ejecutada exitosamente:")
            self.logger.info(f"   📋 Order ID: {order.get('orderId')}")
            self.logger.info(f"   💰 Cantidad: {order.get('executedQty', quantity)}")
            self.logger.info(f"   💵 Precio promedio: {order.get('avgPrice', 'N/A')}")
            
            return order
            
        except BinanceOrderException as e:
            self.logger.error(f"❌ Error al ejecutar orden {side} para {symbol}: {e}")
            self.handle_api_error(e)
            return {}
        except BinanceAPIException as e:
            self.logger.error(f"❌ Error de API al ejecutar orden: {e}")
            self.handle_api_error(e)
            return {}
        except Exception as e:
            self.logger.error(f"❌ Error inesperado al ejecutar orden: {e}")
            return {}
    
    def cancel_order(self, symbol: str, order_id: int) -> bool:
        """
        Cancelar una orden
        
        Args:
            symbol: Par de trading
            order_id: ID de la orden
            
        Returns:
            True si se canceló exitosamente
        """
        try:
            self.client.futures_cancel_order(symbol=symbol, orderId=order_id)
            self.logger.info(f"Orden {order_id} cancelada para {symbol}")
            return True
        except BinanceOrderException as e:
            self.logger.error(f"Error al cancelar orden {order_id}: {e}")
            return False
    
    def get_open_positions(self) -> List[Dict]:
        """
        Obtener posiciones abiertas
        
        Returns:
            Lista de posiciones abiertas
        """
        try:
            positions = self.client.futures_position_information()
            open_positions = [
                pos for pos in positions 
                if float(pos["positionAmt"]) != 0
            ]
            self.logger.debug(f"Posiciones abiertas: {len(open_positions)}")
            return open_positions
        except BinanceAPIException as e:
            self.logger.error(f"Error al obtener posiciones: {e}")
            return []
    
    def handle_api_error(self, error: Exception) -> None:
        """
        Manejar errores de la API
        
        Args:
            error: Excepción capturada
        """
        if isinstance(error, BinanceAPIException):
            if error.code == -1021:  # Timestamp out of sync
                self.logger.warning("Timestamp fuera de sincronización, reintentando...")
                time.sleep(1)
            elif error.code == -1003:  # Rate limit
                self.logger.warning("Límite de velocidad alcanzado, esperando...")
                time.sleep(60)
            else:
                self.logger.error(f"Error de API de Binance: {error.code} - {error.message}")
        else:
            self.logger.error(f"Error inesperado: {error}")
    
    def test_connection(self) -> bool:
        """
        Probar la conexión con Binance
        
        Returns:
            True si la conexión es exitosa
        """
        try:
            self.client.futures_ping()
            self.logger.info("Conexión con Binance exitosa")
            return True
        except Exception as e:
            self.logger.error(f"Error de conexión con Binance: {e}")
            return False
