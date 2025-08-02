import logging
import pandas as pd
from typing import Dict, Optional
from technical_analysis import TechnicalAnalysis
from binance_client import BinanceAPIClient
import config

class TradingStrategy:
    """Implementa la estrategia de trading basada en confluencia de indicadores"""
    
    def __init__(self, binance_client: BinanceAPIClient):
        """
        Inicializar la estrategia de trading
        
        Args:
            binance_client: Cliente de la API de Binance
        """
        self.binance_client = binance_client
        self.technical_analysis = TechnicalAnalysis()
        self.logger = logging.getLogger(__name__)
    
    def analyze_symbol(self, symbol: str) -> Dict:
        """
        Analizar un símbolo específico y generar señal de trading
        
        Args:
            symbol: Par de trading (ej. 'BTCUSDT')
            
        Returns:
            Diccionario con el análisis completo
        """
        analysis_result = {
            'symbol': symbol,
            'signal': 'HOLD',
            'trend_4h': 'SIDEWAYS',
            'ema_crossover_15m': False,
            'rsi_15m': 0,
            'macd_15m': {},
            'current_price': 0,
            'confidence': 0
        }
        
        try:
            # Obtener datos de 4h para tendencia principal
            klines_4h = self.binance_client.get_klines(symbol, config.INTERVAL_4H, 200)
            if klines_4h is None or klines_4h.empty:
                self.logger.warning(f"No se pudieron obtener datos de 4h para {symbol}")
                return analysis_result
            
            # Obtener datos de 15m para señales de entrada
            klines_15m = self.binance_client.get_klines(symbol, config.INTERVAL_15M, 100)
            if klines_15m is None or klines_15m.empty:
                self.logger.warning(f"No se pudieron obtener datos de 15m para {symbol}")
                return analysis_result
            
            # Precio actual
            current_price = self.binance_client.get_current_price(symbol)
            analysis_result['current_price'] = current_price
            
            # Análisis de tendencia principal (4h)
            trend_4h = self.technical_analysis.get_trend_direction(klines_4h, config.EMA_200_PERIOD)
            analysis_result['trend_4h'] = trend_4h
            
            # Calcular RSI en 15m
            rsi_15m = self.technical_analysis.calculate_rsi(klines_15m['close'], config.RSI_PERIOD)
            if rsi_15m is None or rsi_15m.empty or pd.isna(rsi_15m.iloc[-1]):
                self.logger.warning(f"RSI no calculable para {symbol}")
                analysis_result['rsi_15m'] = 0
            else:
                analysis_result['rsi_15m'] = rsi_15m.iloc[-1]
            
            # Calcular MACD en 15m
            macd_data = self.technical_analysis.calculate_macd(
                klines_15m['close'], 
                config.MACD_FAST_PERIOD, 
                config.MACD_SLOW_PERIOD, 
                config.MACD_SIGNAL_PERIOD
            )
            if macd_data is None or macd_data.empty:
                self.logger.warning(f"MACD no calculable para {symbol}")
                analysis_result['macd_15m'] = {}
            else:
                analysis_result['macd_15m'] = {
                    'MACD': macd_data['MACD'].iloc[-1],
                    'SIGNAL': macd_data['MACD_SIGNAL'].iloc[-1],
                    'HIST': macd_data['MACD_HIST'].iloc[-1]
                }
            
            # Generar señal basada en la estrategia
            signal = self.generate_signal(symbol, trend_4h, klines_15m, analysis_result['rsi_15m'], analysis_result['macd_15m'])
            analysis_result['signal'] = signal
            
            # Calcular confianza de la señal
            analysis_result['confidence'] = self._calculate_signal_confidence(analysis_result)
            
            self.logger.debug(f"Análisis de {symbol}: {analysis_result}")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Error al analizar {symbol}: {e}")
            return analysis_result
    
    def generate_signal(self, symbol: str, trend_4h: str, klines_15m: pd.DataFrame, rsi_15m: float, macd_15m: Dict) -> str:
        """
        Generar señal de trading basada en la estrategia
        
        Args:
            symbol: Par de trading
            trend_4h: Tendencia en 4h
            klines_15m: Datos de velas de 15m
            rsi_15m: Valor del RSI en 15m
            macd_15m: Valores del MACD en 15m
            
        Returns:
            'LONG', 'SHORT' o 'HOLD'
        """
        try:
            # Verificar condiciones para LONG
            if self.check_long_conditions(trend_4h, klines_15m, rsi_15m, macd_15m):
                self.logger.info(f"Señal LONG generada para {symbol}")
                return 'LONG'
            
            # Verificar condiciones para SHORT
            elif self.check_short_conditions(trend_4h, klines_15m, rsi_15m, macd_15m):
                self.logger.info(f"Señal SHORT generada para {symbol}")
                return 'SHORT'
            
            # Si no se cumplen las condiciones, mantener
            return 'HOLD'
            
        except Exception as e:
            self.logger.error(f"Error al generar señal para {symbol}: {e}")
            return 'HOLD'
    
    def check_long_conditions(self, trend_4h: str, klines_15m: pd.DataFrame, rsi_15m: float, macd_15m: Dict) -> bool:
        """
        Verificar condiciones para posición larga
        
        Args:
            trend_4h: Tendencia en 4h
            klines_15m: Datos de velas de 15m
            rsi_15m: Valor del RSI en 15m
            macd_15m: Valores del MACD en 15m
            
        Returns:
            True si se cumplen las condiciones para LONG
        """
        # Condición 1: Tendencia principal alcista
        if trend_4h != 'UPTREND':
            return False
        
        # Condición 2: Cruce alcista de EMA 20 en 15m
        ema_crossover = self.technical_analysis.check_ema_crossover(
            klines_15m, config.EMA_20_PERIOD, 'UP'
        )
        if not ema_crossover:
            return False
        
        # Condición 3: RSI entre 40 y 75 (rango de compra)
        if not self.technical_analysis.is_rsi_in_range(
            rsi_15m, config.RSI_BUY_ENTRY, config.RSI_OVERBOUGHT
        ):
            return False
            
        # Condición 4: MACD - Cruce alcista (MACD > SIGNAL)
        if not macd_15m or pd.isna(macd_15m.get('MACD')) or pd.isna(macd_15m.get('SIGNAL')):
            return False
        
        if not (macd_15m['MACD'] > macd_15m['SIGNAL']):
            return False
        
        return True
    
    def check_short_conditions(self, trend_4h: str, klines_15m: pd.DataFrame, rsi_15m: float, macd_15m: Dict) -> bool:
        """
        Verificar condiciones para posición corta
        
        Args:
            trend_4h: Tendencia en 4h
            klines_15m: Datos de velas de 15m
            rsi_15m: Valor del RSI en 15m
            macd_15m: Valores del MACD en 15m
            
        Returns:
            True si se cumplen las condiciones para SHORT
        """
        # Condición 1: Tendencia principal bajista
        if trend_4h != 'DOWNTREND':
            return False
        
        # Condición 2: Cruce bajista de EMA 20 en 15m
        ema_crossover = self.technical_analysis.check_ema_crossover(
            klines_15m, config.EMA_20_PERIOD, 'DOWN'
        )
        if not ema_crossover:
            return False
        
        # Condición 3: RSI entre 25 y 60 (rango de venta)
        if not self.technical_analysis.is_rsi_in_range(
            rsi_15m, config.RSI_OVERSOLD, config.RSI_SELL_ENTRY
        ):
            return False
            
        # Condición 4: MACD - Cruce bajista (MACD < SIGNAL)
        if not macd_15m or pd.isna(macd_15m.get('MACD')) or pd.isna(macd_15m.get('SIGNAL')):
            return False
            
        if not (macd_15m['MACD'] < macd_15m['SIGNAL']):
            return False
        
        return True
    
    def validate_signal(self, signal: str, symbol: str) -> bool:
        """
        Validar la señal generada
        
        Args:
            signal: Señal generada
            symbol: Par de trading
            
        Returns:
            True si la señal es válida
        """
        if signal == 'HOLD':
            return True
        
        # Verificar que no hay posición abierta en este símbolo
        open_positions = self.binance_client.get_open_positions()
        for position in open_positions:
            if position['symbol'] == symbol and float(position['positionAmt']) != 0:
                self.logger.warning(f"Ya existe posición abierta para {symbol}")
                return False
        
        return True
    
    def _calculate_signal_confidence(self, analysis_result: Dict) -> float:
        """
        Calcular la confianza de la señal basada en múltiples factores
        
        Args:
            analysis_result: Resultado del análisis
            
        Returns:
            Valor de confianza entre 0 y 1
        """
        confidence = 0.0
        
        # Factor 1: Tendencia clara en 4h
        if analysis_result['trend_4h'] in ['UPTREND', 'DOWNTREND']:
            confidence += 0.3
        
        # Factor 2: RSI en zona favorable
        rsi = analysis_result['rsi_15m']
        if 30 < rsi < 70:  # RSI no en extremos
            confidence += 0.2
            
        # Factor 3: MACD en zona favorable y con cruce
        macd = analysis_result['macd_15m']
        if macd and not pd.isna(macd.get('MACD')) and not pd.isna(macd.get('SIGNAL')):
            if analysis_result['signal'] == 'LONG' and macd['MACD'] > macd['SIGNAL'] and macd['MACD'] > 0:
                confidence += 0.3
            elif analysis_result['signal'] == 'SHORT' and macd['MACD'] < macd['SIGNAL'] and macd['MACD'] < 0:
                confidence += 0.3
        
        # Factor 4: Señal diferente de HOLD
        if analysis_result['signal'] != 'HOLD':
            confidence += 0.2
        
        return min(confidence, 1.0)


