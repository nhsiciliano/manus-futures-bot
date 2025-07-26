# Guía de Despliegue en Render - Manus Trading Bot

## Preparación Previa

### 1. Configurar API de Binance
- Crear cuenta en Binance y habilitar trading de futuros
- Generar API Key y Secret con permisos de:
  - Lectura de cuenta
  - Trading de futuros
  - **NO** habilitar retiros por seguridad

### 2. Configurar Variables de Entorno
En Render, configurar las siguientes variables:

**OBLIGATORIAS:**
- `BINANCE_API_KEY`: Tu API Key de Binance
- `BINANCE_API_SECRET`: Tu API Secret de Binance

**OPCIONALES (ya tienen valores por defecto):**
- `SYMBOLS`: BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT
- `MAX_RISK_PER_TRADE`: 0.01 (1% por operación)
- `MAX_CONCURRENT_TRADES`: 2
- `RISK_REWARD_RATIO`: 1.5
- `TRAILING_STOP_PERCENT`: 0.0075 (0.75%)
- `LOG_LEVEL`: INFO
- `BOT_RUN_INTERVAL`: 60 (segundos)

## Pasos de Despliegue en Render

### 1. Subir Código a GitHub
```bash
git init
git add .
git commit -m "Initial commit - Manus Trading Bot"
git remote add origin <tu-repositorio-github>
git push -u origin main
```

### 2. Crear Servicio en Render
1. Ir a [render.com](https://render.com) y crear cuenta
2. Conectar tu repositorio de GitHub
3. Crear nuevo "Background Worker"
4. Configurar:
   - **Name**: manus-trading-bot
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Plan**: Starter ($7/mes) o superior

### 3. Configurar Variables de Entorno
En la sección "Environment" del servicio, agregar todas las variables mencionadas arriba.

### 4. Desplegar
- Hacer clic en "Deploy"
- El bot comenzará a ejecutarse automáticamente

## Monitoreo

### Logs en Tiempo Real
- Acceder a los logs desde el dashboard de Render
- Monitorear operaciones, errores y rendimiento

### Métricas Importantes a Vigilar
- Conexión exitosa a Binance API
- Señales de trading generadas
- Operaciones ejecutadas
- Balance de la cuenta
- Errores de conectividad

## Consideraciones de Seguridad

1. **API Keys**: Nunca compartir las claves de API
2. **Permisos**: Solo habilitar trading, NO retiros
3. **Balance**: Comenzar con un balance pequeño para pruebas
4. **Monitoreo**: Revisar logs diariamente los primeros días

## Troubleshooting

### Problemas Comunes
- **Error de API**: Verificar que las claves sean correctas
- **Sin señales**: Normal, el bot espera confluencia de indicadores
- **Conexión perdida**: Render reiniciará automáticamente el servicio

### Comandos Útiles para Debugging
```bash
# Ver logs en tiempo real
render logs -f <service-id>

# Reiniciar servicio
render services restart <service-id>
```

## Costos Estimados

- **Render Starter Plan**: $7/mes
- **Comisiones Binance**: ~0.04% por operación
- **Total mensual**: ~$7-10 (dependiendo del volumen de trading)

## Próximos Pasos

1. Monitorear rendimiento durante la primera semana
2. Ajustar parámetros si es necesario
3. Considerar agregar más pares de trading
4. Implementar notificaciones por Telegram/Discord (opcional)
