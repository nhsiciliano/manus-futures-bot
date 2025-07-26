# Bot de Trading Automático para Futuros de Criptomonedas

## Descripción

Este bot de trading automático está diseñado para operar en el mercado de futuros de criptomonedas de Binance utilizando una estrategia de confluencia de indicadores técnicos en múltiples temporalidades. El bot busca generar ganancias semanales consistentes con un estricto control de riesgos.

## Características Principales

- **Estrategia Multi-Temporal**: Combina análisis de tendencia en 4h con señales de entrada en 15m
- **Gestión de Riesgos Estricta**: Máximo 1% de riesgo por operación
- **Trailing Stop Automático**: Protege ganancias con stops dinámicos
- **Monitoreo Multi-Par**: Analiza múltiples pares simultáneamente
- **Logging Detallado**: Registro completo de todas las operaciones
- **Arquitectura Modular**: Código bien estructurado y mantenible

## Estrategia de Trading

### Análisis de Tendencia Principal (4 horas)
- Utiliza EMA de 200 períodos para determinar la tendencia principal
- Solo busca operaciones LONG en tendencia alcista
- Solo busca operaciones SHORT en tendencia bajista

### Señales de Entrada (15 minutos)
**Para posiciones LONG:**
- Tendencia principal alcista (precio > EMA 200 en 4h)
- Cruce alcista del precio sobre EMA 20 en 15m
- RSI entre 50 y 70 (evita sobrecompra)
- **MACD**: Cruce alcista (MACD > SIGNAL) y MACD > 0 (confirmación de momentum alcista)

**Para posiciones SHORT:**
- Tendencia principal bajista (precio < EMA 200 en 4h)
- Cruce bajista del precio bajo EMA 20 en 15m
- RSI entre 30 y 50 (evita sobreventa)
- **MACD**: Cruce bajista (MACD < SIGNAL) y MACD < 0 (confirmación de momentum bajista)

### Gestión de Riesgos
- **Riesgo por operación**: Máximo 1% del capital
- **Stop Loss**: Basado en el mínimo/máximo de la vela anterior
- **Take Profit**: Relación riesgo/beneficio de 1:1.5
- **Máximo de posiciones**: 2 operaciones simultáneas
- **Trailing Stop**: Se activa con 0.75% de ganancia

## Instalación

### Requisitos Previos
- Python 3.8 o superior
- Cuenta de Binance con API habilitada para futuros
- Capital mínimo recomendado: $1000 USDT

### Pasos de Instalación

1. **Clonar o descargar el proyecto**
```bash
# Si tienes git instalado
git clone <repository_url>
cd crypto_trading_bot

# O simplemente descargar y extraer los archivos
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno**
```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar el archivo .env con tus credenciales
nano .env
```

4. **Configurar las credenciales de Binance**
Edita el archivo `.env` y añade tus credenciales:
```
BINANCE_API_KEY=tu_api_key_aqui
BINANCE_API_SECRET=tu_api_secret_aqui
```

## Configuración

### Obtener Credenciales de Binance

1. Inicia sesión en tu cuenta de Binance
2. Ve a "Gestión de API" en tu perfil
3. Crea una nueva API Key
4. **Importante**: Habilita solo "Futuros" y "Lectura" inicialmente
5. Una vez que hayas probado el bot, puedes habilitar "Trading de Futuros"
6. Configura restricciones de IP para mayor seguridad

### Parámetros Configurables

Puedes modificar los siguientes parámetros en el archivo `config.py`:

```python
# Pares a monitorear
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT']

# Gestión de riesgos
MAX_RISK_PER_TRADE = 0.01  # 1% del capital por operación
MAX_CONCURRENT_TRADES = 2   # Máximo 2 operaciones simultáneas
RISK_REWARD_RATIO = 1.5     # Relación riesgo/beneficio

# Intervalos de tiempo
BOT_RUN_INTERVAL = 60       # Revisar mercado cada 60 segundos
```

## Uso

### Ejecutar el Bot

```bash
python main.py
```

### Detener el Bot

Presiona `Ctrl+C` para detener el bot de forma segura. El bot guardará todas las posiciones abiertas antes de cerrarse.

### Monitoreo

El bot genera logs detallados en:
- **Consola**: Información en tiempo real
- **Archivo**: `trading_bot.log` (historial completo)

## Estructura del Proyecto

```
crypto_trading_bot/
├── main.py                 # Archivo principal del bot
├── config.py              # Configuración del bot
├── binance_client.py      # Cliente de la API de Binance
├── trading_strategy.py    # Lógica de la estrategia
├── technical_analysis.py  # Indicadores técnicos
├── risk_manager.py        # Gestión de riesgos
├── position_manager.py    # Gestión de posiciones
├── logger.py             # Sistema de logging
├── requirements.txt      # Dependencias de Python
├── .env.example         # Ejemplo de variables de entorno
└── README.md           # Esta documentación
```

## Seguridad y Mejores Prácticas

### Seguridad de API
- **Nunca compartas tus claves API**
- Usa restricciones de IP cuando sea posible
- Habilita solo los permisos necesarios
- Revisa regularmente la actividad de tu API

### Gestión de Capital
- **Comienza con capital pequeño** para probar el bot
- **Nunca inviertas más de lo que puedes permitirte perder**
- Monitorea regularmente el rendimiento
- Ajusta los parámetros según tu tolerancia al riesgo

### Monitoreo
- Revisa los logs regularmente
- Monitorea las posiciones abiertas
- Verifica que el bot esté funcionando correctamente
- Ten un plan de contingencia para problemas técnicos

## Solución de Problemas

### Errores Comunes

**Error de conexión con Binance**
- Verifica tus credenciales API
- Comprueba tu conexión a internet
- Revisa si Binance está en mantenimiento

**Error de permisos**
- Asegúrate de que tu API Key tenga permisos de futuros habilitados
- Verifica que el trading esté habilitado en tu API Key

**Posiciones no se abren**
- Verifica que tengas balance suficiente
- Comprueba que no hayas alcanzado el límite de posiciones
- Revisa los logs para ver si las condiciones de entrada se cumplen

### Logs y Debugging

El bot genera logs detallados que incluyen:
- Análisis de mercado para cada símbolo
- Señales generadas
- Órdenes colocadas
- Actualizaciones de posiciones
- Errores y advertencias

Revisa el archivo `trading_bot.log` para información detallada.

## Disclaimer y Advertencias

⚠️ **ADVERTENCIA IMPORTANTE** ⚠️

- **Este bot es para fines educativos y de investigación**
- **El trading de futuros conlleva riesgos significativos**
- **Puedes perder todo tu capital**
- **Siempre prueba con cantidades pequeñas primero**
- **No somos responsables de pérdidas financieras**
- **Usa bajo tu propio riesgo**

### Recomendaciones
1. **Prueba en papel primero**: Ejecuta el bot sin dinero real para entender su comportamiento
2. **Comienza pequeño**: Usa cantidades mínimas al principio
3. **Monitorea constantemente**: No dejes el bot funcionando sin supervisión
4. **Entiende la estrategia**: Asegúrate de comprender completamente cómo funciona
5. **Ten un plan de salida**: Define cuándo detendrás el bot

## Soporte y Contribuciones

Para reportar problemas o sugerir mejoras, por favor:
1. Revisa la documentación completa
2. Verifica los logs de error
3. Proporciona información detallada del problema

## Licencia

Este proyecto es de código abierto y se proporciona "tal como está" sin garantías de ningún tipo.

---

**¡Feliz Trading! 🚀**

*Recuerda: El trading exitoso requiere disciplina, paciencia y gestión de riesgos adecuada.*

