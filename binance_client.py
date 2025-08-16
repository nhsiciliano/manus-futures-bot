import logging
import time
import asyncio
from threading import Thread, Lock
from typing import Dict, List, Optional, Any
from binance import AsyncClient
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from binance import BinanceSocketManager
import pandas as pd
import config

class KlineDataStreamer:
    """Gestiona el stream de datos de klines a través de websockets"""
    
    def __init__(self, client: AsyncClient):
        self.client = client
        self.bsm = BinanceSocketManager(self.client)
        self.klines: Dict[str, pd.DataFrame] = {}
        self.current_prices: Dict[str, float] = {}
        self.lock = Lock()
        self.logger = logging.getLogger(__name__)
        self.streams = {}
        self.is_running = False

    async def _process_message(self, msg: Dict):
        """Procesa un mensaje del websocket de klines"""
        try:
            if not isinstance(msg, dict) or 'stream' not in msg or 'data' not in msg:
                self.logger.warning(f"Mensaje de stream inválido o incompleto: {msg}")
                return

            stream = msg['stream']
            data = msg['data']

            if data.get('e') == 'error':
                self.logger.error(f"Error en websocket stream {stream}: {data.get('m')}")
                return

            if 'k' not in data:
                return

            symbol = data['s']
            kline_data = data['k']
            interval = kline_data['i']
            
            df_new_row = pd.DataFrame([{
                'timestamp': pd.to_datetime(kline_data['t'], unit='ms'),
                'open': float(kline_data['o']),
                'high': float(kline_data['h']),
                'low': float(kline_data['l']),
                'close': float(kline_data['c']),
                'volume': float(kline_data['v']),
                'close_time': kline_data['T'],
                'quote_asset_volume': float(kline_data['q']),
                'number_of_trades': kline_data['n'],
                'taker_buy_base_asset_volume': float(kline_data['V']),
                'taker_buy_quote_asset_volume': float(kline_data['Q']),
                'ignore': 0
            }]).set_index('timestamp')

            stream_name = f"{symbol.lower()}@kline_{interval}"

            with self.lock:
                self.current_prices[symbol] = float(kline_data['c'])
                
                if stream_name not in self.klines:
                    self.klines[stream_name] = df_new_row
                else:
                    if df_new_row.index[0] > self.klines[stream_name].index[-1]:
                        self.klines[stream_name] = pd.concat([self.klines[stream_name], df_new_row])
                        self.klines[stream_name] = self.klines[stream_name].tail(1000) 
                    else:
                        self.klines[stream_name].iloc[-1] = df_new_row.iloc[0]

        except Exception as e:
            self.logger.error(f"Error procesando mensaje de kline: {e} - Mensaje: {msg}", exc_info=True)

    async def prefill_historical_data(self, client: 'BinanceAPIClient'):
        self.logger.info("Prefilling historical kline data...")
        for symbol in config.SYMBOLS:
            for interval in [config.INTERVAL_4H, config.INTERVAL_15M]:
                try:
                    self.logger.info(f"Fetching historical data for {symbol} - {interval}")
                    historical_klines = client.get_klines(symbol, interval, limit=1000)
                    if not historical_klines.empty:
                        stream_name = f"{symbol.lower()}@kline_{interval}"
                        with self.lock:
                            self.klines[stream_name] = historical_klines
                        self.logger.info(f"Prefilled {len(historical_klines)} klines for {symbol} - {interval}")
                    else:
                        self.logger.warning(f"Could not prefill historical data for {symbol} - {interval}")
                except Exception as e:
                    self.logger.error(f"Error prefilling historical data for {symbol} - {interval}: {e}")
                await asyncio.sleep(0.25)

    async def start_stream(self, client: 'BinanceAPIClient'):
        """Inicia los streams de klines para los símbolos configurados"""
        await self.prefill_historical_data(client)
        
        self.is_running = True
        self.logger.info("Iniciando streams de klines...")
        
        streams = []
        for symbol in config.SYMBOLS:
            streams.append(f"{symbol.lower()}@kline_{config.INTERVAL_15M}")
            streams.append(f"{symbol.lower()}@kline_{config.INTERVAL_4H}")

        self.logger.info(f"Suscrito a los siguientes streams: {streams}")
        
        self.multiplex_socket = self.bsm.futures_multiplex_socket(streams)
        async with self.multiplex_socket as ms:
            while self.is_running:
                msg = await ms.recv()
                await self._process_message(msg)

    def get_klines(self, symbol: str, interval: str) -> Optional[pd.DataFrame]:
        """Obtiene los datos de klines para un símbolo e intervalo"""
        stream_name = f"{symbol.lower()}@kline_{interval}"
        with self.lock:
            return self.klines.get(stream_name, None)

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Obtiene el precio actual de un símbolo"""
        with self.lock:
            return self.current_prices.get(symbol, None)

    def stop_stream(self):
        """Detiene el stream de websockets"""
        self.is_running = False
        self.logger.info("Deteniendo streams de klines...")

class BinanceAPIClient:
    """Cliente para interactuar con la API de Binance Futures"""
    
    def __init__(self):
        """
        Inicializar el cliente de Binance
        """
        self.api_key = config.BINANCE_API_KEY
        self.api_secret = config.BINANCE_API_SECRET
        self.client = None
        self.async_client = None
        self.kline_streamer = None
        self.symbol_info = {}
        self.logger = logging.getLogger(__name__)
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializar la conexión con Binance"""
        try:
            self.client = Client(self.api_key, self.api_secret)
            self.async_client = AsyncClient(self.api_key, self.api_secret)
            self.kline_streamer = KlineDataStreamer(self.async_client)
            self._fetch_symbol_info()
            self._set_leverage_for_symbols()
            self.logger.info("Cliente de Binance inicializado correctamente")
        except Exception as e:
            self.logger.error(f"Error al inicializar cliente de Binance: {e}")
            raise

    def start_kline_stream(self):
        """Iniciar el stream de klines en un hilo separado"""
        if self.kline_streamer:
            self.stream_thread = Thread(target=lambda: asyncio.run(self.kline_streamer.start_stream(self)))
            self.stream_thread.daemon = True
            self.stream_thread.start()

    def stop_kline_stream(self):
        """Detener el stream de klines"""
        if self.kline_streamer:
            self.kline_streamer.stop_stream()
            if self.stream_thread.is_alive():
                self.stream_thread.join()

    def _fetch_symbol_info(self):
        """Obtener y almacenar la información de precisión de los símbolos."""
        try:
            exchange_info = self.client.futures_exchange_info()
            for s in exchange_info['symbols']:
                self.symbol_info[s['symbol']] = {
                    'pricePrecision': s['pricePrecision'],
                    'quantityPrecision': s['quantityPrecision'],
                }
            self.logger.info(f"Información de precisión para {len(self.symbol_info)} símbolos cargada.")
        except BinanceAPIException as e:
            self.logger.error(f"Error al obtener información de símbolos de Binance: {e}")
    
    def _format_price(self, symbol: str, price: float) -> str:
        """Formatea un precio según la precisión del símbolo."""
        if symbol in self.symbol_info:
            precision = self.symbol_info[symbol]['pricePrecision']
            return f"{price:.{precision}f}"
        return str(price)

    def _format_quantity(self, symbol: str, quantity: float) -> str:
        """Formatea una cantidad según la precisión del símbolo."""
        if symbol in self.symbol_info:
            precision = self.symbol_info[symbol]['quantityPrecision']
            return f"{quantity:.{precision}f}"
        return str(quantity)

    def _set_leverage_for_symbols(self):
        """Configurar apalancamiento para todos los símbolos de trading"""
        try:
            leverage = config.LEVERAGE
            for symbol in config.SYMBOLS:
                try:
                    self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
                    self.logger.info(f"🔧 Apalancamiento configurado: {symbol} = {leverage}x")
                    time.sleep(0.25)  # Retardo para no exceder los límites de la API
                except Exception as e:
                    self.logger.warning(f"⚠️ No se pudo configurar apalancamiento para {symbol}: {e}")
        except Exception as e:
            self.logger.error(f"Error al configurar apalancamiento: {e}")
    
    def get_account_balance(self) -> float:
        """Obtener el balance de la cuenta de futuros"""
        try:
            account_info = self.client.futures_account()
            total_balance = float(account_info["totalWalletBalance"])
            self.logger.debug(f"Balance de cuenta: {total_balance} USDT")
            return total_balance
        except BinanceAPIException as e:
            self.logger.error(f"Error al obtener balance: {e}")
            return 0.0
    
    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
        """Obtener datos de velas (klines) históricos"""
        try:
            klines = self.client.futures_klines(symbol=symbol, interval=interval, limit=limit)
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume', 
                               'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            self.logger.debug(f"Obtenidas {len(df)} velas históricas para {symbol} en {interval}")
            return df
        except BinanceAPIException as e:
            self.logger.error(f"Error al obtener klines históricos para {symbol}: {e}")
            return pd.DataFrame()

    def get_current_price(self, symbol: str) -> float:
        price = self.kline_streamer.get_current_price(symbol)
        if price is None:
            self.logger.warning(f"Precio no disponible en stream para {symbol}, usando REST API.")
            return self._get_current_price_rest(symbol)
        return price

    def _get_current_price_rest(self, symbol: str) -> float:
        """Obtener el precio actual de un símbolo vía REST API"""
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            price = float(ticker["price"])
            self.logger.debug(f"Precio actual de {symbol} (REST): {price}")
            return price
        except BinanceAPIException as e:
            self.logger.error(f"Error al obtener precio de {symbol} (REST): {e}")
            return 0.0

    def place_futures_order(self, symbol: str, side: str, quantity: float, order_type: str = 'MARKET') -> Dict:
        """Colocar una orden de futuros en Binance"""
        try:
            quantity_str = self._format_quantity(symbol, quantity)
            self.logger.info(f"🔄 Ejecutando orden {side} {order_type} para {quantity_str} {symbol}")
            
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity_str
            )
            
            self.logger.info(f"✅ Orden ejecutada exitosamente: {order}")
            return order
        except BinanceOrderException as e:
            self.logger.error(f"❌ Error al ejecutar orden {side} para {symbol}: {e}")
            return {}

    def place_futures_order_with_sl_tp(self, symbol: str, side: str, quantity: float, 
                                       stop_loss: float, take_profit: float) -> Optional[Dict]:
        """
        Colocar una orden de mercado y luego órdenes de Stop Loss y Take Profit.
        
        Args:
            symbol: Par de trading
            side: 'BUY' o 'SELL'
            quantity: Cantidad de la posición
            stop_loss: Precio de stop loss
            take_profit: Precio de take profit
            
        Returns:
            El resultado de la orden de mercado inicial o None si falla.
        """
        # 1. Colocar la orden de mercado principal
        market_order = self.place_futures_order(symbol, side, quantity, 'MARKET')
        
        if not market_order:
            self.logger.error(f"No se pudo colocar la orden de mercado para {symbol}. No se colocarán SL/TP.")
            return None
            
        # 2. Determinar el lado de las órdenes de cierre (SL/TP)
        exit_side = 'SELL' if side == 'BUY' else 'BUY'
        
        # Formatear precios y cantidad
        quantity_str = self._format_quantity(symbol, quantity)
        stop_loss_str = self._format_price(symbol, stop_loss)
        take_profit_str = self._format_price(symbol, take_profit)

        # 3. Colocar la orden Stop Loss (STOP_MARKET)
        try:
            self.logger.info(f"🛡️ Colocando orden Stop Loss para {symbol} a ${stop_loss_str}")
            sl_order = self.client.futures_create_order(
                symbol=symbol,
                side=exit_side,
                type='STOP_MARKET',
                stopPrice=stop_loss_str,
                quantity=quantity_str,
                reduceOnly=True
            )
            self.logger.info(f"✅ Orden Stop Loss colocada: {sl_order}")
        except BinanceAPIException as e:
            self.logger.error(f"❌ Error al colocar orden Stop Loss para {symbol}: {e}")
            # Aquí se podría añadir lógica para cerrar la posición si el SL falla
            
        # 4. Colocar la orden Take Profit (TAKE_PROFIT_MARKET)
        try:
            self.logger.info(f"🎯 Colocando orden Take Profit para {symbol} a ${take_profit_str}")
            tp_order = self.client.futures_create_order(
                symbol=symbol,
                side=exit_side,
                type='TAKE_PROFIT_MARKET',
                stopPrice=take_profit_str,
                quantity=quantity_str,
                reduceOnly=True
            )
            self.logger.info(f"✅ Orden Take Profit colocada: {tp_order}")
        except BinanceAPIException as e:
            self.logger.error(f"❌ Error al colocar orden Take Profit para {symbol}: {e}")

        return market_order

    def get_open_positions(self) -> List[Dict]:
        """Obtener posiciones abiertas"""
        try:
            positions = self.client.futures_position_information()
            return [p for p in positions if float(p['positionAmt']) != 0]
        except BinanceAPIException as e:
            self.logger.error(f"Error al obtener posiciones: {e}")
            return []

    def test_connection(self) -> bool:
        """Probar la conexión con Binance"""
        try:
            self.client.futures_ping()
            self.logger.info("Conexión con Binance exitosa")
            return True
        except Exception as e:
            self.logger.error(f"Error de conexión con Binance: {e}")
            return False
