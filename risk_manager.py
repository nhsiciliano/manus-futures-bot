import logging
import pandas as pd
from typing import Dict, Optional, Tuple
from binance_client import BinanceAPIClient
import config

class RiskManager:
    """Gestiona el riesgo y calcula tamaños de posición"""
    
    def __init__(self, binance_client: BinanceAPIClient):
        """
        Inicializar el gestor de riesgos
        
        Args:
            binance_client: Cliente de la API de Binance
        """
        self.binance_client = binance_client
        self.logger = logging.getLogger(__name__)
        self.max_risk_per_trade = config.MAX_RISK_PER_TRADE
        self.max_position_size_percent = config.MAX_POSITION_SIZE_PERCENT
        self.max_concurrent_trades = config.MAX_CONCURRENT_TRADES
        self.risk_reward_ratio = config.RISK_REWARD_RATIO
        self.trailing_stop_percent = config.TRAILING_STOP_PERCENT
    
    def calculate_position_size(self, account_balance: float, entry_price: float, 
                              stop_loss_price: float) -> float:
        """
        Calcular el tamaño de la posición basado en el riesgo, respetando el máximo tamaño de posición.
        
        Args:
            account_balance: Balance total de la cuenta
            entry_price: Precio de entrada
            stop_loss_price: Precio de stop loss
            
        Returns:
            Tamaño de la posición en USDT
        """
        try:
            # 1. Calcular el tamaño de posición basado en el riesgo por operación
            distance_to_sl = abs(entry_price - stop_loss_price)
            if distance_to_sl == 0:
                self.logger.warning("La distancia al Stop Loss es cero, no se puede calcular el tamaño de la posición.")
                return 0.0

            max_risk_usdt = account_balance * self.max_risk_per_trade
            position_size_based_on_risk = max_risk_usdt / distance_to_sl
            
            # 2. Calcular el tamaño máximo de posición permitido
            max_position_size_usdt = account_balance * self.max_position_size_percent
            
            # 3. Usar el menor de los dos tamaños
            final_position_size = min(position_size_based_on_risk, max_position_size_usdt)
            
            if final_position_size < position_size_based_on_risk:
                self.logger.info(f"Tamaño de posición ajustado por límite máximo. "
                                 f"Original: {position_size_based_on_risk:.2f}, "
                                 f"Ajustado: {final_position_size:.2f}")

            self.logger.debug(f"Cálculo de posición: Balance={account_balance}, "
                            f"Entrada={entry_price}, SL={stop_loss_price}, "
                            f"Distancia SL={distance_to_sl}, Tamaño Final={final_position_size}")
            
            return final_position_size
            
        except Exception as e:
            self.logger.error(f"Error al calcular tamaño de posición: {e}")
            return 0.0
    
    def calculate_stop_loss(self, symbol: str, side: str, entry_price: float) -> float:
        """
        Calcular el precio de stop loss basado en la vela anterior
        
        Args:
            symbol: Par de trading
            side: 'LONG' o 'SHORT'
            entry_price: Precio de entrada
            
        Returns:
            Precio de stop loss
        """
        try:
            # Obtener datos de 15m para calcular el stop loss
            klines_15m = self.binance_client.get_klines(symbol, config.INTERVAL_15M, 5)
            
            if klines_15m.empty or len(klines_15m) < 2:
                self.logger.warning(f"No hay suficientes datos para calcular SL de {symbol}")
                # Fallback: usar un porcentaje fijo del precio de entrada
                if side == 'LONG':
                    return entry_price * 0.98  # 2% por debajo
                else:
                    return entry_price * 1.02  # 2% por encima
            
            # Obtener la vela anterior (penúltima)
            previous_candle = klines_15m.iloc[-2]
            
            if side == 'LONG':
                # Para posiciones largas, SL en el mínimo de la vela anterior
                stop_loss = previous_candle['low']
            else:
                # Para posiciones cortas, SL en el máximo de la vela anterior
                stop_loss = previous_candle['high']
            
            self.logger.debug(f"Stop loss calculado para {symbol} {side}: {stop_loss}")
            return stop_loss
            
        except Exception as e:
            self.logger.error(f"Error al calcular stop loss para {symbol}: {e}")
            # Fallback en caso de error
            if side == 'LONG':
                return entry_price * 0.98
            else:
                return entry_price * 1.02
    
    def calculate_take_profit(self, entry_price: float, stop_loss_price: float, 
                            side: str) -> float:
        """
        Calcular el precio de take profit basado en la relación riesgo/beneficio
        
        Args:
            entry_price: Precio de entrada
            stop_loss_price: Precio de stop loss
            side: 'LONG' o 'SHORT'
            
        Returns:
            Precio de take profit
        """
        try:
            # Calcular la distancia al stop loss
            distance_to_sl = abs(entry_price - stop_loss_price)
            
            # Calcular la distancia al take profit (riesgo/beneficio)
            distance_to_tp = distance_to_sl * self.risk_reward_ratio
            
            if side == 'LONG':
                take_profit = entry_price + distance_to_tp
            else:
                take_profit = entry_price - distance_to_tp
            
            self.logger.debug(f"Take profit calculado: Entrada={entry_price}, "
                            f"SL={stop_loss_price}, TP={take_profit}, "
                            f"R/R={self.risk_reward_ratio}")
            
            return take_profit
            
        except Exception as e:
            self.logger.error(f"Error al calcular take profit: {e}")
            return entry_price
    
    def can_open_new_position(self) -> bool:
        """
        Verificar si se puede abrir una nueva posición
        
        Returns:
            True si se puede abrir nueva posición
        """
        try:
            open_positions = self.binance_client.get_open_positions()
            current_positions = len([pos for pos in open_positions 
                                   if float(pos['positionAmt']) != 0])
            
            can_open = current_positions < self.max_concurrent_trades
            
            if not can_open:
                self.logger.warning(f"Máximo de posiciones alcanzado: {current_positions}/{self.max_concurrent_trades}")
            
            return can_open
            
        except Exception as e:
            self.logger.error(f"Error al verificar posiciones: {e}")
            return False
    
    def check_risk_limits(self, position_size_usdt: float, account_balance: float) -> bool:
        """
        Verificar que el tamaño de posición no exceda los límites de riesgo
        
        Args:
            position_size_usdt: Tamaño de la posición en USDT
            account_balance: Balance de la cuenta
            
        Returns:
            True si está dentro de los límites
        """
        try:
            max_position_size = account_balance * self.max_position_size_percent  # Máximo 10% del balance por posición
            
            if position_size_usdt > max_position_size:
                self.logger.warning(f"Tamaño de posición excede límite: {position_size_usdt} > {max_position_size}")
                return False
            
            # Verificar que el tamaño mínimo sea viable
            if position_size_usdt < 2:  # Mínimo 2 USDT
                self.logger.warning(f"Tamaño de posición muy pequeño: {position_size_usdt}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al verificar límites de riesgo: {e}")
            return False
    
    def update_trailing_stop(self, position: Dict, current_price: float) -> Optional[float]:
        """
        Actualizar trailing stop para una posición
        
        Args:
            position: Información de la posición
            current_price: Precio actual
            
        Returns:
            Nuevo precio de stop loss si debe actualizarse, None en caso contrario
        """
        try:
            symbol = position['symbol']
            position_amt = float(position['positionAmt'])
            entry_price = float(position['entryPrice'])
            
            # Determinar si es posición larga o corta
            is_long = position_amt > 0
            
            # Calcular el porcentaje de ganancia actual
            if is_long:
                profit_percent = (current_price - entry_price) / entry_price
            else:
                profit_percent = (entry_price - current_price) / entry_price
            
            # Solo activar trailing stop si hay ganancia suficiente
            if profit_percent >= self.trailing_stop_percent:
                
                if is_long:
                    # Para posiciones largas, trailing stop por debajo del precio actual
                    new_stop_loss = current_price * (1 - self.trailing_stop_percent)
                else:
                    # Para posiciones cortas, trailing stop por encima del precio actual
                    new_stop_loss = current_price * (1 + self.trailing_stop_percent)
                
                self.logger.info(f"Trailing stop activado para {symbol}: {new_stop_loss}")
                return new_stop_loss
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error al actualizar trailing stop: {e}")
            return None
    
    def validate_trade_parameters(self, symbol: str, side: str, entry_price: float, 
                                stop_loss: float, take_profit: float, 
                                position_size_usdt: float) -> bool:
        """
        Validar todos los parámetros de una operación antes de ejecutarla
        
        Args:
            symbol: Par de trading
            side: 'LONG' o 'SHORT'
            entry_price: Precio de entrada
            stop_loss: Precio de stop loss
            take_profit: Precio de take profit
            position_size: Tamaño de la posición
            
        Returns:
            True si todos los parámetros son válidos
        """
        try:
            # Validar que los precios sean positivos
            if any(price <= 0 for price in [entry_price, stop_loss, take_profit, position_size_usdt]):
                self.logger.error("Precios o tamaño de posición inválidos (negativos o cero)")
                return False
            
            # Validar la lógica de stop loss y take profit
            if side == 'LONG':
                if stop_loss >= entry_price:
                    self.logger.error("Stop loss debe estar por debajo del precio de entrada para LONG")
                    return False
                if take_profit <= entry_price:
                    self.logger.error("Take profit debe estar por encima del precio de entrada para LONG")
                    return False
            else:  # SHORT
                if stop_loss <= entry_price:
                    self.logger.error("Stop loss debe estar por encima del precio de entrada para SHORT")
                    return False
                if take_profit >= entry_price:
                    self.logger.error("Take profit debe estar por debajo del precio de entrada para SHORT")
                    return False
            
            # Validar relación riesgo/beneficio
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            actual_rr = reward / risk if risk > 0 else 0
            
            if actual_rr < (self.risk_reward_ratio * 0.9):  # Permitir 10% de tolerancia
                self.logger.warning(f"Relación R/R subóptima: {actual_rr:.2f} < {self.risk_reward_ratio}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al validar parámetros de operación: {e}")
            return False

