# 🔧 Troubleshooting - Manus Trading Bot

## Error: numpy.dtype size changed (Binary Incompatibility)

### Problema
```
ValueError: numpy.dtype size changed, may indicate binary incompatibility. 
Expected 96 from C header, got 88 from PyObject
```

### Causa
Este error ocurre cuando hay incompatibilidad entre las versiones compiladas de numpy y pandas en el entorno de producción.

### ✅ Solución Implementada

He actualizado los archivos de configuración para resolver este problema:

1. **requirements.txt**: Especifica numpy==1.24.3 antes que pandas
2. **Dockerfile**: Instala numpy primero, luego el resto de dependencias
3. **render.yaml**: Usa script de instalación personalizado
4. **install_deps.sh**: Instala dependencias en orden específico

### 🚀 Pasos para Re-desplegar

1. **Commit y push los cambios**:
```bash
git add .
git commit -m "Fix numpy/pandas binary incompatibility"
git push origin main
```

2. **En Render Dashboard**:
   - Ir a tu servicio "manus-trading-bot"
   - Hacer clic en "Manual Deploy"
   - Seleccionar "Deploy latest commit"

3. **Monitorear el build**:
   - Ver logs de build en tiempo real
   - Verificar que la instalación de dependencias sea exitosa

### 📋 Orden de Instalación Correcto

El script `install_deps.sh` instala en este orden:
1. pip, setuptools, wheel (actualizados)
2. numpy==1.24.3
3. pandas==2.0.3
4. pandas-ta==0.3.14b0
5. python-binance==1.0.19
6. Utilidades (dotenv, requests, etc.)

### 🔍 Verificar Instalación Exitosa

En los logs de Render deberías ver:
```
🔧 Instalando dependencias para Manus Trading Bot...
📦 Instalando numpy...
📦 Instalando pandas...
📦 Instalando pandas-ta...
📦 Instalando python-binance...
📦 Instalando utilidades...
✅ Instalación completada!
🚀 Listo para ejecutar el bot de trading
```

### 🆘 Si el Problema Persiste

1. **Opción A**: Usar requirements-fixed.txt
```bash
# En render.yaml, cambiar buildCommand a:
buildCommand: pip install -r requirements-fixed.txt
```

2. **Opción B**: Build manual paso a paso
```bash
# En render.yaml, cambiar buildCommand a:
buildCommand: pip install --upgrade pip && pip install numpy==1.24.3 && pip install pandas==2.0.3 && pip install pandas-ta==0.3.14b0 && pip install python-binance==1.0.19 && pip install python-dotenv requests aiohttp websockets
```

### 📞 Contacto de Soporte

Si ninguna solución funciona:
- Render Support: https://render.com/support
- Documentación: https://render.com/docs/troubleshooting-deploys
