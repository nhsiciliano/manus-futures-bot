import os

# Configuración de la API de Binance
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "YOUR_BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "YOUR_BINANCE_API_SECRET")

# Configuración del bot
SYMBOLS = os.getenv("SYMBOLS", "BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT").split(",")  # Pares a monitorear
INTERVAL_4H = "4h"
INTERVAL_15M = "15m"

# Parámetros de la estrategia
EMA_200_PERIOD = 200
EMA_20_PERIOD = 20
RSI_PERIOD = 14
RSI_OVERBOUGHT = 75  # Límite superior para considerar salida
RSI_OVERSOLD = 25   # Límite inferior para considerar salida
RSI_BUY_ENTRY = 40    # Nivel mínimo de RSI para entrar en LONG
RSI_SELL_ENTRY = 60   # Nivel máximo de RSI para entrar en SHORT
RSI_MID_LEVEL = 50

# Parámetros del MACD
MACD_FAST_PERIOD = 12
MACD_SLOW_PERIOD = 26
MACD_SIGNAL_PERIOD = 9

# Gestión de riesgos
MAX_RISK_PER_TRADE = float(os.getenv("MAX_RISK_PER_TRADE", "0.02"))  # 2% del capital por operación
MAX_CONCURRENT_TRADES = int(os.getenv("MAX_CONCURRENT_TRADES", "2"))
RISK_REWARD_RATIO = float(os.getenv("RISK_REWARD_RATIO", "1.5"))
MAX_POSITION_SIZE_PERCENT = float(os.getenv("MAX_POSITION_SIZE_PERCENT", "0.1")) # 10% del balance por posición
TRAILING_STOP_PERCENT = float(os.getenv("TRAILING_STOP_PERCENT", "0.0075")) # 0.75% para activar trailing stop
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.8"))  # Umbral mínimo de confianza para ejecutar operaciones
LEVERAGE = int(os.getenv("LEVERAGE", "5"))  # Apalancamiento para futuros (recomendado: 3-10x para estrategias conservadoras)

# Configuración de Logging
LOG_FILE = os.getenv("LOG_FILE", "trading_bot.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Intervalo de ejecución del bot (en segundos)
BOT_RUN_INTERVAL = int(os.getenv("BOT_RUN_INTERVAL", "120")) # Cada 120 segundos el bot revisará el mercado

# Configuración de Notificaciones de Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID")
