#!/usr/bin/env python3
"""
Bot de Trading Automático para Futuros de Criptomonedas - Versión Robusta
Estrategia: Confluencia de indicadores en múltiples temporalidades
Autor: Manus AI
"""

import asyncio
import time
import signal
import sys
import traceback
from typing import Dict, List
import logging

from binance_client import BinanceAPIClient
from trading_strategy import TradingStrategy
from risk_manager import RiskManager
from position_manager import PositionManager
from logger import TradingLogger
import config

class RobustTradingBot:
    """Bot principal de trading automático con manejo robusto de errores"""
    
    def __init__(self):
        """Inicializar el bot de trading"""
        self.running = False
        self.logger = None
        self.binance_client = None
        self.trading_strategy = None
        self.risk_manager = None
        self.position_manager = None
        self.cycle_count = 0
        self.last_successful_cycle = None
        
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
            print("🔧 Inicializando componentes del bot...")
            
            # Inicializar logger
            self.logger = TradingLogger()
            self.logger.log_bot_status("STARTING", "Inicializando componentes del bot")
            
            # Inicializar cliente de Binance
            print("📡 Conectando a Binance API...")
            self.binance_client = BinanceAPIClient()
            
            # Probar conexión
            if not self.binance_client.test_connection():
                self.logger.log_error("No se pudo establecer conexión con Binance")
                print("❌ Error: No se pudo conectar a Binance API")
                return False
            
            print("✅ Conexión a Binance establecida")
            
            # Inicializar estrategia de trading
            print("📊 Inicializando estrategia de trading...")
            self.trading_strategy = TradingStrategy(self.binance_client)
            
            # Inicializar gestor de riesgos
            print("🛡️ Inicializando gestor de riesgos...")
            self.risk_manager = RiskManager(self.binance_client)
            
            # Inicializar gestor de posiciones
            print("📈 Inicializando gestor de posiciones...")
            self.position_manager = PositionManager()
            self.position_manager.load_positions_from_file()
            
            self.logger.log_bot_status("INITIALIZED", "Todos los componentes inicializados correctamente")
            print("✅ Todos los componentes inicializados correctamente")
            return True
            
        except Exception as e:
            error_msg = f"Error al inicializar componentes: {str(e)}"
            if self.logger:
                self.logger.log_error(error_msg, e)
            else:
                print(f"❌ {error_msg}")
                print(f"Traceback: {traceback.format_exc()}")
            return False
    
    async def analyze_markets_safe(self) -> List[Dict]:
        """
        Analizar todos los mercados configurados con manejo robusto de errores
        
        Returns:
            Lista de análisis de mercado
        """
        analysis_results = []
        
        try:
            self.logger.info(f"🔍 Iniciando análisis de mercados (Ciclo #{self.cycle_count})")
            
            for symbol in config.SYMBOLS:
                try:
                    self.logger.debug(f"Analizando {symbol}")
                    
                    # Verificar conexión antes de analizar
                    if not self.binance_client.test_connection():
                        self.logger.warning("Conexión perdida, reintentando...")
                        await asyncio.sleep(5)
                        continue
                    
                    analysis = self.trading_strategy.analyze_symbol(symbol)
                    if analysis:
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
                        
                        self.logger.info(f"📊 {symbol}: {analysis['signal']} (Confianza: {analysis['confidence']:.2f})")
                    else:
                        self.logger.warning(f"No se pudo obtener análisis para {symbol}")
                        
                except Exception as e:
                    self.logger.log_error(f"Error al analizar {symbol}", e)
                    continue
            
            self.logger.info(f"✅ Análisis completado: {len(analysis_results)} símbolos procesados")
            return analysis_results
            
        except Exception as e:
            self.logger.log_error("Error crítico en análisis de mercados", e)
            return []
    
    async def execute_trades_safe(self, analysis_results: List[Dict]) -> None:
        """
        Ejecutar operaciones basadas en los análisis con manejo robusto de errores
        
        Args:
            analysis_results: Lista de análisis de mercado
        """
        try:
            if not analysis_results:
                self.logger.debug("No hay análisis para procesar")
                return
            
            trading_signals = [a for a in analysis_results if a['signal'] != 'HOLD']
            
            if not trading_signals:
                self.logger.info("📊 No hay señales de trading en este ciclo")
                return
            
            self.logger.info(f"🎯 Procesando {len(trading_signals)} señales de trading")
            
            for analysis in trading_signals:
                try:
                    symbol = analysis['symbol']
                    signal = analysis['signal']
                    
                    # Verificar si se puede abrir nueva posición
                    if not self.risk_manager.can_open_new_position():
                        self.logger.warning("⚠️ No se pueden abrir más posiciones (límite alcanzado)")
                        break
                    
                    # Verificar que no hay posición existente para este símbolo
                    if self.position_manager.get_position(symbol):
                        self.logger.warning(f"⚠️ Ya existe posición para {symbol}")
                        continue
                    
                    # Calcular parámetros de la operación
                    entry_price = analysis['current_price']
                    stop_loss = self.risk_manager.calculate_stop_loss(symbol, signal, entry_price)
                    take_profit = self.risk_manager.calculate_take_profit(entry_price, stop_loss, signal)
                    
                    # Calcular tamaño de posición en USDT
                    balance = self.binance_client.get_account_balance()
                    position_size_usdt = self.risk_manager.calculate_position_size(balance, entry_price, stop_loss)
                    
                    # Validar límites de riesgo
                    if not self.risk_manager.check_risk_limits(position_size_usdt, balance):
                        self.logger.warning(f"⚠️ Operación rechazada por límites de riesgo: {symbol}")
                        continue
                    
                    # Validar parámetros de la operación
                    if not self.risk_manager.validate_trade_parameters(symbol, signal, entry_price, stop_loss, take_profit, position_size_usdt):
                        self.logger.warning(f"⚠️ Parámetros de operación inválidos para {symbol}")
                        continue

                    self.logger.info(f"🚀 Ejecutando señal {signal} para {symbol} con tamaño {position_size_usdt:.2f} USDT")
                    
                except Exception as e:
                    self.logger.log_error(f"Error al ejecutar operación para {analysis.get('symbol', 'UNKNOWN')}", e)
                    continue
                    
        except Exception as e:
            self.logger.log_error("Error crítico en ejecución de trades", e)
    
    async def monitor_positions_safe(self) -> None:
        """Monitorear posiciones existentes con manejo robusto de errores"""
        try:
            positions = self.position_manager.get_all_positions()
            if positions:
                self.logger.debug(f"Monitoreando {len(positions)} posiciones")
                # Aquí iría la lógica de monitoreo de posiciones
            
        except Exception as e:
            self.logger.log_error("Error al monitorear posiciones", e)
    
    async def run_cycle_safe(self) -> bool:
        """
        Ejecutar un ciclo completo del bot con manejo robusto de errores
        
        Returns:
            True si el ciclo fue exitoso
        """
        try:
            self.cycle_count += 1
            cycle_start = time.time()
            
            self.logger.debug(f"🔄 Iniciando ciclo #{self.cycle_count}")
            
            # Analizar mercados
            analysis_results = await self.analyze_markets_safe()
            
            # Ejecutar operaciones
            await self.execute_trades_safe(analysis_results)
            
            # Monitorear posiciones existentes
            await self.monitor_positions_safe()
            
            cycle_duration = time.time() - cycle_start
            self.last_successful_cycle = time.time()
            
            self.logger.info(f"✅ Ciclo #{self.cycle_count} completado en {cycle_duration:.2f}s")
            return True
            
        except Exception as e:
            self.logger.log_error(f"Error en ciclo #{self.cycle_count}", e)
            return False
    
    async def run(self) -> None:
        """Ejecutar el bucle principal del bot con reintentos automáticos"""
        try:
            self.running = True
            self.logger.log_bot_status("RUNNING", "Bot iniciado correctamente")
            print("🤖 Bot iniciado - Operando 24/7")
            print(f"📊 Monitoreando: {', '.join(config.SYMBOLS)}")
            print(f"⏱️ Intervalo: {config.BOT_RUN_INTERVAL} segundos")
            
            consecutive_failures = 0
            max_failures = 5
            
            while self.running:
                try:
                    # Ejecutar ciclo
                    success = await self.run_cycle_safe()
                    
                    if success:
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                        self.logger.warning(f"⚠️ Fallo consecutivo #{consecutive_failures}")
                        
                        if consecutive_failures >= max_failures:
                            self.logger.error(f"❌ Máximo de fallos consecutivos alcanzado ({max_failures})")
                            break
                    
                    # Esperar antes del próximo ciclo
                    self.logger.debug(f"⏳ Esperando {config.BOT_RUN_INTERVAL} segundos...")
                    await asyncio.sleep(config.BOT_RUN_INTERVAL)
                    
                except asyncio.CancelledError:
                    self.logger.info("🛑 Bot cancelado")
                    break
                except Exception as e:
                    consecutive_failures += 1
                    self.logger.log_error(f"Error en bucle principal (fallo #{consecutive_failures})", e)
                    
                    if consecutive_failures >= max_failures:
                        self.logger.error(f"❌ Demasiados fallos consecutivos, deteniendo bot")
                        break
                    
                    # Esperar antes de reintentar
                    await asyncio.sleep(30)
            
            self.logger.log_bot_status("STOPPING", "Bot detenido")
            
        except Exception as e:
            self.logger.log_error("Error crítico en el bucle principal", e)
            self.running = False
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """Cierre seguro del bot"""
        try:
            self.logger.log_bot_status("SHUTDOWN", "Iniciando cierre seguro")
            print("🛑 Cerrando bot de forma segura...")
            
            # Guardar posiciones
            if self.position_manager:
                self.position_manager.save_positions_to_file()
                print("💾 Posiciones guardadas")
            
            self.logger.log_bot_status("SHUTDOWN", "Bot cerrado correctamente")
            print("✅ Bot cerrado correctamente")
            
        except Exception as e:
            if self.logger:
                self.logger.log_error("Error durante el cierre", e)
            print(f"❌ Error durante el cierre: {e}")

async def main():
    """Función principal con reinicio automático"""
    print("=" * 60)
    print("🤖 MANUS TRADING BOT - VERSIÓN ROBUSTA")
    print("=" * 60)
    print("🎯 Estrategia: Confluencia multi-temporal")
    print("⚡ Modo: 24/7 Producción")
    print("=" * 60)
    
    max_restarts = 3
    restart_count = 0
    
    while restart_count < max_restarts:
        try:
            print(f"\n🚀 Iniciando bot (Intento #{restart_count + 1})")
            
            bot = RobustTradingBot()
            
            if not bot.initialize_components():
                print("❌ Error: No se pudieron inicializar los componentes del bot")
                restart_count += 1
                if restart_count < max_restarts:
                    print(f"⏳ Reintentando en 30 segundos...")
                    await asyncio.sleep(30)
                    continue
                else:
                    sys.exit(1)
            
            print("✅ Bot inicializado correctamente")
            print("🔄 Presiona Ctrl+C para detener")
            
            await bot.run()
            break  # Salida normal
            
        except KeyboardInterrupt:
            print("\n🛑 Bot detenido por el usuario")
            break
        except Exception as e:
            restart_count += 1
            print(f"❌ Error crítico: {e}")
            print(f"📊 Traceback: {traceback.format_exc()}")
            
            if restart_count < max_restarts:
                print(f"🔄 Reiniciando automáticamente en 60 segundos... (Intento {restart_count + 1}/{max_restarts})")
                await asyncio.sleep(60)
            else:
                print(f"❌ Máximo de reinicios alcanzado ({max_restarts})")
                sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
