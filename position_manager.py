import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

class PositionManager:
    """Gestiona las posiciones abiertas y sus órdenes asociadas"""
    
    def __init__(self):
        """Inicializar el gestor de posiciones"""
        self.positions = {}  # Diccionario para almacenar posiciones
        self.logger = logging.getLogger(__name__)
    
    def add_position(self, symbol: str, side: str, entry_price: float, 
                    quantity: float, stop_loss: float, take_profit: float,
                    order_id: Optional[str] = None) -> bool:
        """
        Añadir una nueva posición
        
        Args:
            symbol: Par de trading
            side: 'LONG' o 'SHORT'
            entry_price: Precio de entrada
            quantity: Cantidad de la posición
            stop_loss: Precio de stop loss
            take_profit: Precio de take profit
            order_id: ID de la orden (opcional)
            
        Returns:
            True si se añadió exitosamente
        """
        try:
            position_data = {
                'symbol': symbol,
                'side': side,
                'entry_price': entry_price,
                'quantity': quantity,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'order_id': order_id,
                'entry_time': datetime.now().isoformat(),
                'status': 'OPEN',
                'trailing_stop_active': False,
                'current_stop_loss': stop_loss,
                'max_profit': 0.0,
                'current_pnl': 0.0
            }
            
            self.positions[symbol] = position_data
            self.logger.info(f"Posición añadida: {side} {symbol} @ {entry_price}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al añadir posición para {symbol}: {e}")
            return False
    
    def remove_position(self, symbol: str) -> bool:
        """
        Remover una posición
        
        Args:
            symbol: Par de trading
            
        Returns:
            True si se removió exitosamente
        """
        try:
            if symbol in self.positions:
                position = self.positions[symbol]
                del self.positions[symbol]
                self.logger.info(f"Posición removida: {position['side']} {symbol}")
                return True
            else:
                self.logger.warning(f"No se encontró posición para {symbol}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al remover posición para {symbol}: {e}")
            return False
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """
        Obtener información de una posición específica
        
        Args:
            symbol: Par de trading
            
        Returns:
            Diccionario con información de la posición o None
        """
        return self.positions.get(symbol)
    
    def update_position(self, symbol: str, **kwargs) -> bool:
        """
        Actualizar datos de una posición
        
        Args:
            symbol: Par de trading
            **kwargs: Campos a actualizar
            
        Returns:
            True si se actualizó exitosamente
        """
        try:
            if symbol in self.positions:
                for key, value in kwargs.items():
                    if key in self.positions[symbol]:
                        self.positions[symbol][key] = value
                        self.logger.debug(f"Posición {symbol} actualizada: {key}={value}")
                return True
            else:
                self.logger.warning(f"No se encontró posición para actualizar: {symbol}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al actualizar posición {symbol}: {e}")
            return False
    
    def get_all_positions(self) -> Dict:
        """
        Obtener todas las posiciones
        
        Returns:
            Diccionario con todas las posiciones
        """
        return self.positions.copy()
    
    def update_position_pnl(self, symbol: str, current_price: float) -> float:
        """
        Actualizar el PnL de una posición
        
        Args:
            symbol: Par de trading
            current_price: Precio actual
            
        Returns:
            PnL actual de la posición
        """
        try:
            if symbol not in self.positions:
                return 0.0
            
            position = self.positions[symbol]
            entry_price = position['entry_price']
            quantity = position['quantity']
            side = position['side']
            
            if side == 'LONG':
                pnl = (current_price - entry_price) * quantity
                profit_percent = (current_price - entry_price) / entry_price
            else:  # SHORT
                pnl = (entry_price - current_price) * quantity
                profit_percent = (entry_price - current_price) / entry_price
            
            # Actualizar datos de la posición
            self.positions[symbol]['current_pnl'] = pnl
            
            # Actualizar máximo profit si es mayor
            if profit_percent > position['max_profit']:
                self.positions[symbol]['max_profit'] = profit_percent
            
            return pnl
            
        except Exception as e:
            self.logger.error(f"Error al actualizar PnL para {symbol}: {e}")
            return 0.0
    
    def should_activate_trailing_stop(self, symbol: str, current_price: float, 
                                    activation_threshold: float) -> bool:
        """
        Verificar si se debe activar el trailing stop
        
        Args:
            symbol: Par de trading
            current_price: Precio actual
            activation_threshold: Umbral de activación (porcentaje)
            
        Returns:
            True si se debe activar el trailing stop
        """
        try:
            if symbol not in self.positions:
                return False
            
            position = self.positions[symbol]
            
            # Si ya está activo, no necesitamos verificar de nuevo
            if position['trailing_stop_active']:
                return True
            
            entry_price = position['entry_price']
            side = position['side']
            
            if side == 'LONG':
                profit_percent = (current_price - entry_price) / entry_price
            else:  # SHORT
                profit_percent = (entry_price - current_price) / entry_price
            
            if profit_percent >= activation_threshold:
                self.positions[symbol]['trailing_stop_active'] = True
                self.logger.info(f"Trailing stop activado para {symbol} con {profit_percent:.2%} de ganancia")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error al verificar trailing stop para {symbol}: {e}")
            return False
    
    def update_trailing_stop(self, symbol: str, new_stop_loss: float) -> bool:
        """
        Actualizar el trailing stop de una posición
        
        Args:
            symbol: Par de trading
            new_stop_loss: Nuevo precio de stop loss
            
        Returns:
            True si se actualizó exitosamente
        """
        try:
            if symbol not in self.positions:
                return False
            
            position = self.positions[symbol]
            current_stop = position['current_stop_loss']
            side = position['side']
            
            # Verificar que el nuevo stop loss sea mejor que el actual
            should_update = False
            
            if side == 'LONG':
                # Para posiciones largas, el nuevo SL debe ser mayor (más favorable)
                should_update = new_stop_loss > current_stop
            else:  # SHORT
                # Para posiciones cortas, el nuevo SL debe ser menor (más favorable)
                should_update = new_stop_loss < current_stop
            
            if should_update:
                self.positions[symbol]['current_stop_loss'] = new_stop_loss
                self.logger.info(f"Trailing stop actualizado para {symbol}: {current_stop} -> {new_stop_loss}")
                return True
            else:
                self.logger.debug(f"Nuevo stop loss no es mejor para {symbol}: {new_stop_loss} vs {current_stop}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al actualizar trailing stop para {symbol}: {e}")
            return False
    
    def get_position_summary(self) -> Dict:
        """
        Obtener un resumen de todas las posiciones
        
        Returns:
            Diccionario con resumen de posiciones
        """
        try:
            summary = {
                'total_positions': len(self.positions),
                'long_positions': 0,
                'short_positions': 0,
                'total_pnl': 0.0,
                'positions_with_trailing_stop': 0
            }
            
            for symbol, position in self.positions.items():
                if position['side'] == 'LONG':
                    summary['long_positions'] += 1
                else:
                    summary['short_positions'] += 1
                
                summary['total_pnl'] += position['current_pnl']
                
                if position['trailing_stop_active']:
                    summary['positions_with_trailing_stop'] += 1
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error al generar resumen de posiciones: {e}")
            return {}
    
    def save_positions_to_file(self, filename: str = 'positions.json') -> bool:
        """
        Guardar posiciones en un archivo JSON
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            True si se guardó exitosamente
        """
        try:
            with open(filename, 'w') as f:
                json.dump(self.positions, f, indent=2, default=str)
            self.logger.debug(f"Posiciones guardadas en {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al guardar posiciones: {e}")
            return False
    
    def load_positions_from_file(self, filename: str = 'positions.json') -> bool:
        """
        Cargar posiciones desde un archivo JSON
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            True si se cargó exitosamente
        """
        try:
            with open(filename, 'r') as f:
                self.positions = json.load(f)
            self.logger.info(f"Posiciones cargadas desde {filename}")
            return True
            
        except FileNotFoundError:
            self.logger.info(f"Archivo {filename} no encontrado, iniciando con posiciones vacías")
            return True
        except Exception as e:
            self.logger.error(f"Error al cargar posiciones: {e}")
            return False

