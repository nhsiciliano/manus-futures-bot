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
from notifications import send_telegram_message

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
    
    async def initialize_components(self) -> bool:
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

            # Iniciar stream de datos de mercado
            print("🌊 Iniciando stream de datos de mercado...")
            self.binance_client.start_kline_stream()
            self.logger.info("Stream de datos de mercado iniciado, esperando para precargar datos...")
            
            # Esperar a que los datos históricos se carguen
            await asyncio.sleep(15) # Aumentado a 15s para asegurar la carga
            print("✅ Stream de datos de mercado iniciado y datos precargados")

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

            # Reconcilar posiciones con Binance
            print("🔄 Reconciliando posiciones con Binance...")
            self.logger.info("Sincronizando el estado de las posiciones con el exchange.")
            if not self.position_manager.reconcile_positions(self.binance_client):
                self.logger.error("No se pudo reconciliar las posiciones con Binance. El bot no continuará.")
                print("❌ Error: Falló la sincronización de posiciones con Binance.")
                return False
            print("✅ Posiciones reconciliadas correctamente.")
            
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
            
            # Filtrar señales por umbral de confianza
            high_confidence_signals = [a for a in trading_signals if a['confidence'] >= config.CONFIDENCE_THRESHOLD]
            
            if not high_confidence_signals:
                low_conf_count = len(trading_signals)
                self.logger.info(f"📊 {low_conf_count} señales detectadas pero ninguna supera el umbral de confianza ({config.CONFIDENCE_THRESHOLD:.2f})")
                return
            
            self.logger.info(f"🎯 Procesando {len(high_confidence_signals)} señales de trading con alta confianza")
            
            for analysis in high_confidence_signals:
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
                    
                    self.logger.info(f"🚀 Ejecutando señal {signal} para {symbol}")
                    
                    # Ejecutar la operación real
                    success = await self._execute_real_trade(analysis)
                    
                    if success:
                        self.logger.info(f"✅ Operación {signal} ejecutada exitosamente para {symbol}")
                    else:
                        self.logger.warning(f"⚠️ Falló la ejecución de {signal} para {symbol}")
                    
                except Exception as e:
                    self.logger.log_error(f"Error al ejecutar operación para {analysis.get('symbol', 'UNKNOWN')}", e)
                    continue
                    
        except Exception as e:
            self.logger.log_error("Error crítico en ejecución de trades", e)
    
    async def _execute_real_trade(self, analysis: Dict) -> bool:
        """
        Ejecutar una operación real en Binance
        
        Args:
            analysis: Análisis del mercado con la señal de trading
            
        Returns:
            True si la operación fue exitosa
        """
        try:
            symbol = analysis['symbol']
            signal = analysis['signal']
            entry_price = analysis['current_price']
            
            self.logger.info(f"💰 Preparando operación {signal} para {symbol} @ ${entry_price:.4f}")
            
            # Obtener balance de la cuenta
            account_balance = self.binance_client.get_account_balance()
            if account_balance <= 0:
                self.logger.error("❌ Balance de cuenta insuficiente")
                return False
            
            self.logger.info(f"💳 Balance disponible: ${account_balance:.2f} USDT")
            
            # Calcular stop loss
            stop_loss = self.risk_manager.calculate_stop_loss(symbol, signal, entry_price)
            
            # Calcular take profit
            take_profit = self.risk_manager.calculate_take_profit(entry_price, stop_loss, signal)
            
            # Calcular tamaño de posición
            position_size_usdt = self.risk_manager.calculate_position_size(
                account_balance, entry_price, stop_loss
            )
            
            # Verificar límites de riesgo
            if not self.risk_manager.check_risk_limits(position_size_usdt, account_balance):
                self.logger.warning(f"⚠️ Operación rechazada por límites de riesgo: {symbol}")
                return False
            
            # Validar parámetros de la operación
            if not self.risk_manager.validate_trade_parameters(
                symbol, signal, entry_price, stop_loss, take_profit, position_size_usdt
            ):
                self.logger.warning(f"⚠️ Parámetros de operación inválidos: {symbol}")
                return False
            
            # Log de los parámetros calculados
            self.logger.info(f"📊 Parámetros de operación:")
            self.logger.info(f"   💰 Tamaño: ${position_size_usdt:.2f} USDT")
            self.logger.info(f"   🛡️ Stop Loss: ${stop_loss:.4f}")
            self.logger.info(f"   🎯 Take Profit: ${take_profit:.4f}")
            
            # Ejecutar la orden en Binance
            order_result = self.binance_client.place_futures_order_with_sl_tp(
                symbol=symbol,
                side='BUY' if signal == 'LONG' else 'SELL',
                quantity=position_size_usdt / entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            if order_result:
                # Registrar la posición en el position manager
                position_data = {
                    'symbol': symbol,
                    'side': signal,
                    'entry_price': entry_price,
                    'quantity': position_size_usdt / entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'order_id': order_result.get('orderId'),
                    'timestamp': time.time()
                }
                
                self.position_manager.add_position(
                    symbol=position_data['symbol'],
                    side=position_data['side'],
                    entry_price=position_data['entry_price'],
                    quantity=position_data['quantity'],
                    stop_loss=position_data['stop_loss'],
                    take_profit=position_data['take_profit'],
                    order_id=position_data.get('order_id')
                )
                
                # Log de éxito
                self.logger.log_signal(
                    symbol, signal, entry_price,
                    f"SL: ${stop_loss:.4f}, TP: ${take_profit:.4f}, Size: ${position_size_usdt:.2f}"
                )
                
                self.logger.info(f"🎉 OPERACIÓN EJECUTADA: {signal} {symbol} @ ${entry_price:.4f}")
                self.logger.info(f"📋 Order ID: {order_result.get('orderId')}")

                

                # Enviar notificación a Telegram
                telegram_message = (
                    f"🚀 *Nueva Operación: {signal} {symbol}* 🚀\n\n"
                    f"*Entrada:* ${entry_price:.4f}\n"
                    f"*Stop Loss:* ${stop_loss:.4f}\n"
                    f"*Take Profit:* ${take_profit:.4f}\n"
                    f"*Tamaño:* ${position_size_usdt:.2f} USDT"
                )
                send_telegram_message(telegram_message)
                
                return True
            else:
                self.logger.error(f"❌ Error al ejecutar orden en Binance para {symbol}")
                return False
                
        except Exception as e:
            self.logger.log_error(f"Error al ejecutar operación real para {analysis.get('symbol', 'UNKNOWN')}", e)
            return False
    
    async def monitor_positions_safe(self) -> None:
        """Monitorea posiciones abiertas, actualiza PnL y gestiona Trailing Stops."""
        try:
            positions = self.position_manager.get_all_positions()
            if not positions:
                return

            self.logger.debug(f"Monitoreando {len(positions)} posiciones abiertas...")

            for symbol, position in positions.items():
                try:
                    current_price = self.binance_client.get_current_price(symbol)
                    if not current_price:
                        self.logger.warning(f"No se pudo obtener precio para monitorear {symbol}")
                        continue

                    # Actualizar PnL de la posición
                    self.position_manager.update_position_pnl(symbol, current_price)

                    # Verificar si se debe activar el Trailing Stop
                    if self.position_manager.should_activate_trailing_stop(symbol, current_price, config.TRAILING_STOP_PERCENT):
                        
                        # Calcular el nuevo precio de stop loss
                        new_stop_loss = self.risk_manager.calculate_trailing_stop(current_price, position['side'])
                        
                        # Verificar si el nuevo SL es una mejora y actualizarlo localmente
                        if self.position_manager.update_trailing_stop(symbol, new_stop_loss):
                            self.logger.info(f"Intentando actualizar Trailing Stop en Binance para {symbol} a ${new_stop_loss:.4f}")
                            
                            # Actualizar la orden en Binance
                            update_status = self.binance_client.update_trailing_stop_order(
                                symbol=symbol,
                                side=position['side'],
                                quantity=position['quantity'],
                                new_stop_loss=new_stop_loss,
                                take_profit=position['take_profit']
                            )

                            if update_status == 'UPDATED':
                                self.logger.info(f"✅ Trailing Stop para {symbol} actualizado exitosamente en Binance.")
                                send_telegram_message(f"🛡️ Trailing Stop Actualizado 🛡️\n\n*Símbolo:* {symbol}\n*Nuevo Stop Loss:* ${new_stop_loss:.4f}")
                            elif update_status == 'CLOSED':
                                self.logger.info(f"✅ Posición {symbol} cerrada por activación de Trailing Stop.")
                                send_telegram_message(f"💥 Posición Cerrada por Trailing Stop 💥\n\n*Símbolo:* {symbol}")
                                self.position_manager.remove_position(symbol)
                            else: # 'FAILED'
                                self.logger.error(f"❌ FALLO CRÍTICO: No se pudo actualizar el Trailing Stop en Binance para {symbol}. La posición puede no tener SL.")

                except Exception as e:
                    self.logger.log_error(f"Error al monitorear la posición {symbol}", e)
                    continue

        except Exception as e:
            self.logger.log_error("Error crítico al monitorear posiciones", e)
    
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
            
            if not await bot.initialize_components():
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
