# 🚀 Checklist de Despliegue - Manus Trading Bot

## Antes del Despliegue
- [ ] API Keys de Binance configuradas y probadas
- [ ] Permisos de API correctos (solo trading, NO retiros)
- [ ] Balance inicial en la cuenta de futuros
- [ ] Todos los archivos del proyecto subidos a GitHub

## Configuración en Render
- [ ] Servicio creado como "Background Worker"
- [ ] Variables de entorno configuradas:
  - [ ] BINANCE_API_KEY
  - [ ] BINANCE_API_SECRET
  - [ ] SYMBOLS (opcional)
  - [ ] MAX_RISK_PER_TRADE (opcional)
  - [ ] Otras variables opcionales según necesidad

## Post-Despliegue
- [ ] Bot iniciado correctamente
- [ ] Logs muestran conexión exitosa a Binance
- [ ] Monitoreo activo durante las primeras 24 horas
- [ ] Verificar que se generan señales de trading
- [ ] Confirmar que las operaciones se ejecutan correctamente

## Monitoreo Continuo
- [ ] Revisar logs diariamente
- [ ] Monitorear balance de la cuenta
- [ ] Verificar rendimiento semanal
- [ ] Ajustar parámetros si es necesario

## Contactos de Emergencia
- Render Support: https://render.com/support
- Binance API Docs: https://binance-docs.github.io/apidocs/
