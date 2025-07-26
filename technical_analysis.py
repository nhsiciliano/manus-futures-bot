import pandas as pd
import pandas_ta as ta
import logging

class TechnicalAnalysis:
    """Clase para realizar cálculos de indicadores técnicos"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """
        Calcula la Media Móvil Exponencial (EMA)
        
        Args:
            data: Serie de precios (usualmente 'close')
            period: Período de la EMA
            
        Returns:
            Serie con los valores de la EMA
        """
        if data.empty:
            return pd.Series(dtype='float64')
        return ta.ema(data, length=period)
    
    def calculate_rsi(self, data: pd.Series, period: int) -> pd.Series:
        """
        Calcula el Índice de Fuerza Relativa (RSI)
        
        Args:
            data: Serie de precios (usualmente 'close')
            period: Período del RSI
            
        Returns:
            Serie con los valores del RSI
        """
        if data.empty:
            return pd.Series(dtype='float64')
        return ta.rsi(data, length=period)

    def calculate_macd(self, data: pd.Series, fast_period: int, slow_period: int, signal_period: int) -> pd.DataFrame:
        """
        Calcula el Moving Average Convergence Divergence (MACD)
        
        Args:
            data: Serie de precios (usualmente 'close')
            fast_period: Período de la EMA rápida
            slow_period: Período de la EMA lenta
            signal_period: Período de la línea de señal
            
        Returns:
            DataFrame con las columnas 'MACD', 'MACD_SIGNAL', 'MACD_HIST'
        """
        if data.empty:
            return pd.DataFrame()
        macd = ta.macd(data, fast=fast_period, slow=slow_period, signal=signal_period)
        if macd is not None and not macd.empty:
            # Construir los nombres de columna esperados por pandas_ta
            macd_line_col = f"MACD_{fast_period}_{slow_period}_{signal_period}"
            macd_signal_col = f"MACDs_{fast_period}_{slow_period}_{signal_period}"
            macd_hist_col = f"MACDh_{fast_period}_{slow_period}_{signal_period}"
            
            # Renombrar a nombres genéricos
            macd.rename(columns={
                macd_line_col: 'MACD',
                macd_signal_col: 'MACD_SIGNAL',
                macd_hist_col: 'MACD_HIST'
            }, inplace=True)
            return macd[['MACD', 'MACD_SIGNAL', 'MACD_HIST']]
        return pd.DataFrame()
    
    def get_trend_direction(self, klines_4h: pd.DataFrame, ema_period: int) -> str:
        """
        Determina la dirección de la tendencia principal (4h) usando EMA.
        
        Args:
            klines_4h: DataFrame de velas de 4 horas
            ema_period: Período de la EMA (ej. 200)
            
        Returns:
            'UPTREND', 'DOWNTREND' o 'SIDEWAYS'
        """
        if klines_4h is None or klines_4h.empty:
            self.logger.warning("No hay datos de 4h para determinar la tendencia.")
            return 'SIDEWAYS'
        
        ema_200 = self.calculate_ema(klines_4h["close"], ema_period)
        
        if ema_200.empty or pd.isna(ema_200.iloc[-1]):
            self.logger.warning("EMA 200 no calculable para la tendencia.")
            return 'SIDEWAYS'
            
        current_price = klines_4h["close"].iloc[-1]
        last_ema_200 = ema_200.iloc[-1]
        
        if current_price > last_ema_200:
            return 'UPTREND'
        elif current_price < last_ema_200:
            return 'DOWNTREND'
        else:
            return 'SIDEWAYS'

    def check_ema_crossover(self, klines_15m: pd.DataFrame, ema_period: int, direction: str) -> bool:
        """
        Verifica el cruce de la EMA en 15m.
        
        Args:
            klines_15m: DataFrame de velas de 15 minutos
            ema_period: Período de la EMA (ej. 20)
            direction: 'UP' para cruce alcista, 'DOWN' para cruce bajista
            
        Returns:
            True si hay cruce en la dirección especificada, False en caso contrario.
        """
        if klines_15m is None or klines_15m.empty or len(klines_15m) < ema_period + 1:
            self.logger.warning("No hay suficientes datos de 15m para verificar el cruce de EMA.")
            return False
        
        ema = self.calculate_ema(klines_15m["close"], ema_period)
        
        if ema.empty or pd.isna(ema.iloc[-1]) or pd.isna(ema.iloc[-2]):
            self.logger.warning("EMA no calculable para el cruce.")
            return False

        current_price = klines_15m["close"].iloc[-1]
        previous_price = klines_15m["close"].iloc[-2]
        current_ema = ema.iloc[-1]
        previous_ema = ema.iloc[-2]

        if direction == 'UP':
            # Cruce alcista: precio actual > EMA y precio anterior < EMA
            return (current_price > current_ema) and (previous_price < previous_ema)
        elif direction == 'DOWN':
            # Cruce bajista: precio actual < EMA y precio anterior > EMA
            return (current_price < current_ema) and (previous_price > previous_ema)
        return False

    def is_rsi_in_range(self, rsi_value: float, min_val: float, max_val: float) -> bool:
        """
        Verifica si el valor del RSI está dentro de un rango específico.
        
        Args:
            rsi_value: Valor actual del RSI
            min_val: Valor mínimo del rango
            max_val: Valor máximo del rango
            
        Returns:
            True si el RSI está en el rango, False en caso contrario.
        """
        return min_val <= rsi_value <= max_val


