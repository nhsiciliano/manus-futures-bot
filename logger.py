import logging
import os
from datetime import datetime
from typing import Optional

class TradingLogger:
    """Sistema de logging para el bot de trading"""
    
    def __init__(self, log_file: str = 'trading_bot.log', log_level: str = 'INFO'):
        """
        Inicializar el sistema de logging
        
        Args:
            log_file: Nombre del archivo de log
            log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        """
        self.log_file = log_file
        self.log_level = getattr(logging, log_level.upper())
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Configurar el logger"""
        logger = logging.getLogger('TradingBot')
        logger.setLevel(self.log_level)
        
        # Evitar duplicar handlers
        if logger.handlers:
            logger.handlers.clear()
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def log_signal(self, symbol: str, signal: str, price: float, details: Optional[str] = None):
        """
        Registrar señales de trading
        
        Args:
            symbol: Par de trading
            signal: Tipo de señal (LONG, SHORT, HOLD)
            price: Precio actual
            details: Detalles adicionales
        """
        message = f"SEÑAL: {signal} para {symbol} @ {price}"
        if details:
            message += f" - {details}"
        self.logger.info(message)
    
    def log_order(self, order_type: str, symbol: str, side: str, quantity: float, price: Optional[float] = None):
        """
        Registrar órdenes
        
        Args:
            order_type: Tipo de orden (MARKET, LIMIT, STOP_LOSS, TAKE_PROFIT)
            symbol: Par de trading
            side: BUY o SELL
            quantity: Cantidad
            price: Precio (si aplica)
        """
        message = f"ORDEN: {order_type} {side} {quantity} {symbol}"
        if price:
            message += f" @ {price}"
        self.logger.info(message)
    
    def log_position_update(self, symbol: str, action: str, details: str):
        """
        Registrar actualizaciones de posición
        
        Args:
            symbol: Par de trading
            action: Acción realizada (OPEN, CLOSE, UPDATE_SL, UPDATE_TP)
            details: Detalles de la acción
        """
        message = f"POSICIÓN: {action} {symbol} - {details}"
        self.logger.info(message)
    
    def log_error(self, error_message: str, exception: Optional[Exception] = None):
        """
        Registrar errores
        
        Args:
            error_message: Mensaje de error
            exception: Excepción capturada (opcional)
        """
        if exception:
            self.logger.error(f"ERROR: {error_message} - {str(exception)}")
        else:
            self.logger.error(f"ERROR: {error_message}")
    
    def log_performance(self, symbol: str, pnl: float, duration: str, entry_price: float, exit_price: float):
        """
        Registrar rendimiento de operaciones
        
        Args:
            symbol: Par de trading
            pnl: Ganancia/pérdida
            duration: Duración de la operación
            entry_price: Precio de entrada
            exit_price: Precio de salida
        """
        message = f"RENDIMIENTO: {symbol} PnL: {pnl:.4f} USDT, Duración: {duration}, Entrada: {entry_price}, Salida: {exit_price}"
        self.logger.info(message)
    
    def log_risk_check(self, symbol: str, risk_percent: float, position_size: float, account_balance: float):
        """
        Registrar verificaciones de riesgo
        
        Args:
            symbol: Par de trading
            risk_percent: Porcentaje de riesgo
            position_size: Tamaño de posición
            account_balance: Balance de cuenta
        """
        message = f"RIESGO: {symbol} - Riesgo: {risk_percent:.2%}, Tamaño: {position_size}, Balance: {account_balance}"
        self.logger.debug(message)
    
    def log_market_analysis(self, symbol: str, timeframe: str, analysis_result: dict):
        """
        Registrar análisis de mercado
        
        Args:
            symbol: Par de trading
            timeframe: Marco temporal
            analysis_result: Resultado del análisis
        """
        message = f"ANÁLISIS: {symbol} {timeframe} - {analysis_result}"
        self.logger.debug(message)
    
    def log_bot_status(self, status: str, details: Optional[str] = None):
        """
        Registrar estado del bot
        
        Args:
            status: Estado del bot (STARTING, RUNNING, STOPPING, ERROR)
            details: Detalles adicionales
        """
        message = f"BOT: {status}"
        if details:
            message += f" - {details}"
        self.logger.info(message)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)

