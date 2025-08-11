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
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Manejar señales de cierre"""
        print("\nSeñal de cierre recibida. Cerrando bot de forma segura...")
        self.running = False
    
    async def initialize_components(self) -> bool:
        """Inicializar todos los componentes del bot"""
        try:
            print("🔧 Inicializando componentes del bot...")
            self.logger = TradingLogger()
            self.logger.log_bot_status("STARTING", "Inicializando componentes del bot")
            
            print("📡 Conectando a Binance API...")
            self.binance_client = BinanceAPIClient()
            
            if not self.binance_client.test_connection():
                self.logger.log_error("No se pudo establecer conexión con Binance")
                print("❌ Error: No se pudo conectar a Binance API")
                return False
            print("✅ Conexión a Binance establecida")

            print("🔌 Iniciando stream de datos de mercado (Websocket)...")
            self.binance_client.start_kline_stream()
            
            print("⏳ Esperando la llegada de datos iniciales del stream...")
            await asyncio.sleep(10) # Dar tiempo a que el websocket se conecte y reciba datos

            print("📈 Cargando datos históricos iniciales para el análisis...")
            await self._populate_initial_klines()

            print("📊 Inicializando estrategia de trading...")
            self.trading_strategy = TradingStrategy(self.binance_client)
            
            print("🛡️ Inicializando gestor de riesgos...")
            self.risk_manager = RiskManager(self.binance_client)
            
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

    async def _populate_initial_klines(self):
        """Carga los datos históricos de klines al inicio"""
        for symbol in config.SYMBOLS:
            for interval in [config.INTERVAL_15M, config.INTERVAL_4H]:
                try:
                    klines = self.binance_client.get_klines(symbol, interval, 500)
                    if not klines.empty:
                        stream_name = f"{symbol.lower()}@kline_{interval}"
                        self.binance_client.kline_streamer.klines[stream_name] = klines
                        self.logger.info(f"Cargados {len(klines)} klines históricos para {symbol} ({interval})")
                    else:
                        self.logger.warning(f"No se pudieron cargar klines históricos para {symbol} ({interval})")
                    await asyncio.sleep(0.5) # Pequeña pausa para no sobrecargar la API
                except Exception as e:
                    self.logger.error(f"Error cargando klines históricos para {symbol} ({interval}): {e}")

    async def analyze_markets_safe(self) -> List[Dict]:
        """Analizar todos los mercados configurados"""
        analysis_results = []
        try:
            self.logger.info(f"🔍 Iniciando análisis de mercados (Ciclo #{self.cycle_count})")
            
            for symbol in config.SYMBOLS:
                try:
                    self.logger.debug(f"Analizando {symbol}")
                    analysis = self.trading_strategy.analyze_symbol(symbol)
                    if analysis and analysis.get('signal') != 'HOLD':
                        analysis_results.append(analysis)
                        self.logger.info(f"📊 {symbol}: {analysis['signal']} (Confianza: {analysis['confidence']:.2f})")
                    elif analysis:
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
        """Ejecutar operaciones basadas en los análisis"""
        try:
            high_confidence_signals = [a for a in analysis_results if a['confidence'] >= config.CONFIDENCE_THRESHOLD and a['signal'] != 'HOLD']
            
            if not high_confidence_signals:
                self.logger.info("📊 No hay señales de alta confianza para operar en este ciclo")
                return

            self.logger.info(f"🎯 Procesando {len(high_confidence_signals)} señales de trading con alta confianza")
            
            for analysis in high_confidence_signals:
                try:
                    symbol = analysis['symbol']
                    signal = analysis['signal']
                    
                    if not self.risk_manager.can_open_new_position():
                        self.logger.warning("⚠️ No se pueden abrir más posiciones (límite alcanzado)")
                        break
                    
                    if self.position_manager.get_position(symbol):
                        self.logger.warning(f"⚠️ Ya existe posición para {symbol}")
                        continue
                    
                    entry_price = analysis['current_price']
                    stop_loss = self.risk_manager.calculate_stop_loss(symbol, signal, entry_price)
                    take_profit = self.risk_manager.calculate_take_profit(entry_price, stop_loss, signal)
                    balance = self.binance_client.get_account_balance()
                    position_size_usdt = self.risk_manager.calculate_position_size(balance, entry_price, stop_loss)
                    
                    if not self.risk_manager.validate_trade_parameters(symbol, signal, entry_price, stop_loss, take_profit, position_size_usdt):
                        self.logger.warning(f"⚠️ Parámetros de operación inválidos para {symbol}")
                        continue

                    self.logger.info(f"🚀 Ejecutando señal {signal} para {symbol} con tamaño {position_size_usdt:.2f} USDT")
                    # Aquí iría la lógica para ejecutar la orden
                    
                except Exception as e:
                    self.logger.log_error(f"Error al ejecutar operación para {analysis.get('symbol', 'UNKNOWN')}", e)
                    
        except Exception as e:
            self.logger.log_error("Error crítico en ejecución de trades", e)
    
    async def monitor_positions_safe(self) -> None:
        """Monitorear posiciones existentes"""
        # Lógica de monitoreo
        pass
    
    async def run_cycle_safe(self) -> bool:
        """Ejecutar un ciclo completo del bot"""
        try:
            self.cycle_count += 1
            cycle_start = time.time()
            self.logger.debug(f"🔄 Iniciando ciclo #{self.cycle_count}")
            
            analysis_results = await self.analyze_markets_safe()
            await self.execute_trades_safe(analysis_results)
            await self.monitor_positions_safe()
            
            cycle_duration = time.time() - cycle_start
            self.last_successful_cycle = time.time()
            self.logger.info(f"✅ Ciclo #{self.cycle_count} completado en {cycle_duration:.2f}s")
            return True
            
        except Exception as e:
            self.logger.log_error(f"Error en ciclo #{self.cycle_count}", e)
            return False
    
    async def run(self) -> None:
        """Ejecutar el bucle principal del bot"""
        try:
            self.running = True
            self.logger.log_bot_status("RUNNING", "Bot iniciado correctamente")
            print("🤖 Bot iniciado - Operando 24/7")
            print(f"📊 Monitoreando: {', '.join(config.SYMBOLS)}")
            print(f"⏱️ Intervalo: {config.BOT_RUN_INTERVAL} segundos")
            
            while self.running:
                await self.run_cycle_safe()
                self.logger.debug(f"⏳ Esperando {config.BOT_RUN_INTERVAL} segundos...")
                await asyncio.sleep(config.BOT_RUN_INTERVAL)
            
        except asyncio.CancelledError:
            self.logger.info("🛑 Bot cancelado")
        except Exception as e:
            self.logger.log_error("Error crítico en el bucle principal", e)
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """Cierre seguro del bot"""
        try:
            self.logger.log_bot_status("SHUTDOWN", "Iniciando cierre seguro")
            print("🛑 Cerrando bot de forma segura...")
            
            if self.binance_client:
                self.binance_client.stop_kline_stream()
                print("🔌 Stream de datos detenido")

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
    
    bot = RobustTradingBot()
    try:
        if await bot.initialize_components():
            print("✅ Bot inicializado correctamente")
            print("🔄 Presiona Ctrl+C para detener")
            await bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot detenido por el usuario")
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        print(f"📊 Traceback: {traceback.format_exc()}")
    finally:
        await bot.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
