#!/usr/bin/env python3
"""
Bot de Trading Automático para Futuros de Criptomonedas
Estrategia: Confluencia de indicadores en múltiples temporalidades
Autor: Manus AI
"""

import asyncio
import time
import signal
import sys
from typing import Dict, List
import logging

from binance_client import BinanceAPIClient
from trading_strategy import TradingStrategy
from risk_manager import RiskManager
from position_manager import PositionManager
from logger import TradingLogger
import config

class TradingBot:
    """Bot principal de trading automático"""
    
    def __init__(self):
        """Inicializar el bot de trading"""
        self.running = False
        self.logger = None
        self.binance_client = None
        self.trading_strategy = None
        self.risk_manager = None
        self.position_manager = None
        
        # Configurar el manejo de señales para cierre seguro
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Manejar señales de cierre"""
        print("\nSeñal de cierre recibida. Cerrando bot de forma segura...")
        self.running = False
    
    def initialize_components(self) -> bool:
        """
        Inicializar todos los componentes del bot
        
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            # Inicializar logger
            self.logger = TradingLogger(config.LOG_FILE, config.LOG_LEVEL)
            self.logger.log_bot_status("STARTING", "Inicializando componentes del bot")
            
            # Inicializar cliente de Binance
            self.binance_client = BinanceAPIClient(
                config.BINANCE_API_KEY, 
                config.BINANCE_API_SECRET
            )
            
            # Probar conexión
            if not self.binance_client.test_connection():
                self.logger.log_error("No se pudo establecer conexión con Binance")
                return False
            
            # Inicializar estrategia de trading
            self.trading_strategy = TradingStrategy(self.binance_client)
            
            # Inicializar gestor de riesgos
            self.risk_manager = RiskManager(self.binance_client)
            
            # Inicializar gestor de posiciones
            self.position_manager = PositionManager()
            self.position_manager.load_positions_from_file()
            
            self.logger.log_bot_status("INITIALIZED", "Todos los componentes inicializados correctamente")
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.log_error("Error al inicializar componentes", e)
            else:
                print(f"Error crítico al inicializar: {e}")
            return False
    
    async def analyze_markets(self) -> List[Dict]:
        """
        Analizar todos los mercados configurados
        
        Returns:
            Lista de análisis de mercado
        """
        analysis_results = []
        
        for symbol in config.SYMBOLS:
            try:
                self.logger.debug(f"Analizando {symbol}")
                analysis = self.trading_strategy.analyze_symbol(symbol)
                analysis_results.append(analysis)
                
                # Log del análisis
                self.logger.log_market_analysis(
                    symbol, 
                    "15m/4h", 
                    {
                        'signal': analysis['signal'],
                        'trend_4h': analysis['trend_4h'],
                        'rsi_15m': analysis['rsi_15m'],
                        'confidence': analysis['confidence']
                    }
                )
                
            except Exception as e:
                self.logger.log_error(f"Error al analizar {symbol}", e)
                continue
        
        return analysis_results
    
    async def execute_trades(self, analysis_results: List[Dict]) -> None:
        """
        Ejecutar operaciones basadas en los análisis
        
        Args:
            analysis_results: Lista de análisis de mercado
        """
        for analysis in analysis_results:
            try:
                symbol = analysis['symbol']
                signal = analysis['signal']
                
                # Solo procesar señales de trading (no HOLD)
                if signal == 'HOLD':
                    continue
                
                # Verificar si se puede abrir nueva posición
                if not self.risk_manager.can_open_new_position():
                    self.logger.warning("No se pueden abrir más posiciones (límite alcanzado)")
                    break
                
                # Verificar que no hay posición existente para este símbolo
                if self.position_manager.get_position(symbol):
                    self.logger.warning(f"Ya existe posición para {symbol}")
                    continue
                
                # Validar la señal
                if not self.trading_strategy.validate_signal(signal, symbol):
                    continue
                
                # Ejecutar la operación
                await self._execute_single_trade(analysis)
                
            except Exception as e:
                self.logger.log_error(f"Error al ejecutar operación para {analysis.get('symbol', 'UNKNOWN')}", e)
                continue
    
    async def _execute_single_trade(self, analysis: Dict) -> None:
        """
        Ejecutar una operación individual
        
        Args:
            analysis: Análisis del mercado para el símbolo
        """
        try:
            symbol = analysis['symbol']
            signal = analysis['signal']
            entry_price = analysis['current_price']
            
            # Obtener balance de la cuenta
            account_balance = self.binance_client.get_account_balance()
            if account_balance <= 0:
                self.logger.log_error("Balance de cuenta insuficiente")
                return
            
            # Calcular stop loss
            stop_loss = self.risk_manager.calculate_stop_loss(symbol, signal, entry_price)
            
            # Calcular take profit
            take_profit = self.risk_manager.calculate_take_profit(entry_price, stop_loss, signal)
            
            # Calcular tamaño de posición
            position_size = self.risk_manager.calculate_position_size(
                account_balance, entry_price, stop_loss
            )
            
            # Verificar límites de riesgo
            if not self.risk_manager.check_risk_limits(position_size, account_balance):
                self.logger.warning(f"Operación rechazada por límites de riesgo: {symbol}")
                return
            
            # Validar parámetros de la operación
            if not self.risk_manager.validate_trade_parameters(
                symbol, signal, entry_price, stop_loss, take_profit, position_size
            ):
                self.logger.warning(f"Parámetros de operación inválidos: {symbol}")
                return
            
            # Log de la señal
            self.logger.log_signal(
                symbol, signal, entry_price,
                f"SL: {stop_loss:.4f}, TP: {take_profit:.4f}, Size: {position_size:.4f}"
            )
            
            # Ejecutar orden de mercado
            side = 'BUY' if signal == 'LONG' else 'SELL'
            order = self.binance_client.place_market_order(symbol, side, position_size)
            
            if order:
                # Log de la orden
                self.logger.log_order("MARKET", symbol, side, position_size, entry_price)
                
                # Colocar stop loss
                sl_side = 'SELL' if signal == 'LONG' else 'BUY'
                sl_order = self.binance_client.place_stop_loss_order(
                    symbol, sl_side, position_size, stop_loss
                )
                
                # Colocar take profit
                tp_order = self.binance_client.place_take_profit_order(
                    symbol, sl_side, position_size, take_profit
                )
                
                # Añadir posición al gestor
                self.position_manager.add_position(
                    symbol, signal, entry_price, position_size,
                    stop_loss, take_profit, order.get('orderId')
                )
                
                # Log de la posición
                self.logger.log_position_update(
                    symbol, "OPEN",
                    f"{signal} @ {entry_price}, SL: {stop_loss}, TP: {take_profit}"
                )
                
                # Guardar posiciones
                self.position_manager.save_positions_to_file()
            
        except Exception as e:
            self.logger.log_error(f"Error al ejecutar operación individual para {symbol}", e)
    
    async def monitor_positions(self) -> None:
        """Monitorear posiciones existentes y actualizar trailing stops"""
        try:
            positions = self.position_manager.get_all_positions()
            
            for symbol, position in positions.items():
                try:
                    # Obtener precio actual
                    current_price = self.binance_client.get_current_price(symbol)
                    
                    # Actualizar PnL
                    pnl = self.position_manager.update_position_pnl(symbol, current_price)
                    
                    # Verificar si activar trailing stop
                    if self.position_manager.should_activate_trailing_stop(
                        symbol, current_price, config.TRAILING_STOP_PERCENT
                    ):
                        # Calcular nuevo trailing stop
                        new_stop_loss = self.risk_manager.update_trailing_stop(
                            position, current_price
                        )
                        
                        if new_stop_loss:
                            # Actualizar trailing stop en el gestor de posiciones
                            if self.position_manager.update_trailing_stop(symbol, new_stop_loss):
                                self.logger.log_position_update(
                                    symbol, "UPDATE_TRAILING_STOP",
                                    f"Nuevo SL: {new_stop_loss:.4f}"
                                )
                    
                except Exception as e:
                    self.logger.log_error(f"Error al monitorear posición {symbol}", e)
                    continue
            
            # Log resumen de posiciones
            summary = self.position_manager.get_position_summary()
            if summary['total_positions'] > 0:
                self.logger.debug(f"Resumen posiciones: {summary}")
                
        except Exception as e:
            self.logger.log_error("Error al monitorear posiciones", e)
    
    async def run_cycle(self) -> None:
        """Ejecutar un ciclo completo del bot"""
        try:
            self.logger.debug("Iniciando ciclo de análisis")
            
            # Analizar mercados
            analysis_results = await self.analyze_markets()
            
            # Ejecutar operaciones
            await self.execute_trades(analysis_results)
            
            # Monitorear posiciones existentes
            await self.monitor_positions()
            
            self.logger.debug("Ciclo completado")
            
        except Exception as e:
            self.logger.log_error("Error en ciclo del bot", e)
    
    async def run(self) -> None:
        """Ejecutar el bucle principal del bot"""
        try:
            self.running = True
            self.logger.log_bot_status("RUNNING", "Bot iniciado correctamente")
            
            while self.running:
                await self.run_cycle()
                
                # Esperar antes del próximo ciclo
                await asyncio.sleep(config.BOT_RUN_INTERVAL)
            
            self.logger.log_bot_status("STOPPING", "Bot detenido por el usuario")
            
        except Exception as e:
            self.logger.log_error("Error crítico en el bucle principal", e)
            self.running = False
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """Cierre seguro del bot"""
        try:
            self.logger.log_bot_status("SHUTDOWN", "Iniciando cierre seguro")
            
            # Guardar posiciones
            if self.position_manager:
                self.position_manager.save_positions_to_file()
            
            self.logger.log_bot_status("SHUTDOWN", "Bot cerrado correctamente")
            
        except Exception as e:
            if self.logger:
                self.logger.log_error("Error durante el cierre", e)

async def main():
    """Función principal"""
    print("=== Bot de Trading de Futuros Crypto ===")
    print("Inicializando...")
    
    bot = TradingBot()
    
    if not bot.initialize_components():
        print("Error: No se pudieron inicializar los componentes del bot")
        sys.exit(1)
    
    print("Bot inicializado correctamente. Presiona Ctrl+C para detener.")
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\nBot detenido por el usuario")
    except Exception as e:
        print(f"Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

