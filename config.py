import os

# Configuración de la API de Binance
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "YOUR_BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "YOUR_BINANCE_API_SECRET")

# Configuración del bot
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]  # Pares a monitorear
INTERVAL_4H = "4h"
INTERVAL_15M = "15m"

# Parámetros de la estrategia
EMA_200_PERIOD = 200
EMA_20_PERIOD = 20
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
RSI_MID_LEVEL = 50

# Parámetros del MACD
MACD_FAST_PERIOD = 12
MACD_SLOW_PERIOD = 26
MACD_SIGNAL_PERIOD = 9

# Gestión de riesgos
MAX_RISK_PER_TRADE = 0.01  # 1% del capital por operación
MAX_CONCURRENT_TRADES = 2
RISK_REWARD_RATIO = 1.5
TRAILING_STOP_PERCENT = 0.0075 # 0.75% para activar trailing stop

# Configuración de Logging
LOG_FILE = "trading_bot.log"
LOG_LEVEL = "INFO"

# Intervalo de ejecución del bot (en segundos)
BOT_RUN_INTERVAL = 60 # Cada 60 segundos el bot revisará el mercado


