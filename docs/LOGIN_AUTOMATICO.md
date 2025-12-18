# Guía de Login Automático SAP

Esta guía explica cómo configurar y usar el login automático con credenciales en el proyecto SAP Automation.

## 🔐 Opciones de Conexión

El proyecto soporta dos modos de conexión:

### 1. **Existing Session** (Modo por defecto)
- Conecta a una sesión SAP GUI ya abierta manualmente
- **No requiere credenciales**
- Más rápido y seguro para uso interactivo
- Recomendado para desarrollo y pruebas

### 2. **Credentials** (Login automático)
- Abre SAP GUI y hace login automáticamente
- Requiere credenciales almacenadas de forma segura
- Ideal para automatización desatendida
- Útil para tareas programadas o scripts batch

---

## 📝 Configuración Paso a Paso

### Paso 1: Almacenar Credenciales

Tienes dos opciones para almacenar credenciales:

#### Opción A: Keyring del Sistema (Recomendado)

```powershell
# Almacenar credenciales en el keyring seguro del sistema
python -m src.utils.credential_manager set \
  --username TU_USUARIO_SAP \
  --password TU_CONTRASEÑA \
  --client 100 \
  --system-id DEV
```

**Ventajas**:
- ✅ Credenciales encriptadas por el sistema operativo
- ✅ No se almacenan en archivos de texto
- ✅ Acceso restringido al usuario actual de Windows

#### Opción B: Variables de Entorno (.env)

```powershell
# 1. Copiar plantilla
copy .env.example .env

# 2. Editar .env con un editor de texto y completar:
SAP_USERNAME=tu_usuario
SAP_PASSWORD=tu_contraseña
SAP_CLIENT=100
SAP_SYSTEM_ID=DEV
```

**Nota**: El archivo `.env` está en `.gitignore` y no se commiteará a git.

---

### Paso 2: Configurar el Sistema SAP

Edita `config/settings.yaml`:

```yaml
sap:
  # Cambiar modo de conexión
  connection_mode: "credentials"  # ← Cambiar de "existing_session" a "credentials"
  
  # Configurar nombre del sistema SAP
  # Usa el nombre EXACTO como aparece en SAP Logon
  connection_string: "SAP ERP Production"  # ← Nombre de tu sistema SAP
  
  transaction_code: "/nZTSD_FACTURACION"
```

**¿Cómo encontrar el nombre del sistema?**
1. Abre **SAP Logon**
2. El nombre que aparece en la lista es tu `connection_string`
3. Ejemplo: "SAP ECC Development", "SAP S/4HANA QA", etc.

---

### Paso 3: Verificar Configuración

```powershell
# Verificar credenciales almacenadas (password oculto)
python -m src.utils.credential_manager get
```

Deberías ver:
```
Credenciales encontradas:
  Username:  TU_USUARIO
  Password:  ***
  Client:    100
  System ID: DEV
```

---

### Paso 4: Probar Login Automático

```powershell
# SAP GUI no necesita estar abierto
python main.py --task export_invoice --invoice 2025102419
```

Si todo está configurado correctamente:
1. SAP GUI se abrirá automáticamente
2. Se conectará al sistema configurado
3. Login automático con credenciales
4. Ejecutará la tarea
5. Cerrará la conexión al finalizar

---

## 🔄 Cambiar Entre Modos

### Usar Existing Session (manual)

```yaml
# config/settings.yaml
sap:
  connection_mode: "existing_session"  # ← Modo manual
  connection_index: 0
  session_index: 0
```

```powershell
# Abrir SAP GUI manualmente primero
python main.py --task export_invoice --invoice 2025102419
```

### Usar Credentials (automático)

```yaml
# config/settings.yaml
sap:
  connection_mode: "credentials"  # ← Modo automático
  connection_string: "SAP System Name"
```

```powershell
# SAP GUI se abrirá automáticamente
python main.py --task export_invoice --invoice 2025102419
```

---

## 🛠️ Gestión de Credenciales

### Ver Credenciales

```powershell
python -m src.utils.credential_manager get
```

### Actualizar Credenciales

```powershell
# Actualizar con nuevas credenciales
python -m src.utils.credential_manager set \
  --username NUEVO_USUARIO \
  --password NUEVA_PASS \
  --client 100 \
  --system-id DEV
```

### Eliminar Credenciales

```powershell
python -m src.utils.credential_manager delete
```

---

## ⚠️ Troubleshooting

### Error: "Invalid or missing credentials"

**Solución**: Configurar credenciales
```powershell
python -m src.utils.credential_manager set --username USER --password PASS --client 100 --system-id SYS
```

### Error: "connection_string not found in config"

**Solución**: Agregar nombre del sistema en `config/settings.yaml`
```yaml
sap:
  connection_string: "Nombre del Sistema SAP"  # Como aparece en SAP Logon
```

### Error: "SAP Login failed: [mensaje de error]"

**Causas comunes**:
- ❌ Usuario o contraseña incorrectos → Verificar credenciales
- ❌ Cliente incorrecto → Verificar el mandante (client)
- ❌ Usuario bloqueado → Contactar administrador SAP
- ❌ Contraseña expirada → Cambiar contraseña en SAP

**Solución**: Revisar logs en `logs/app.log` para más detalles

### Error: "Connection opened but no session available"

**Solución**: Verificar que el nombre del sistema en `connection_string` sea exacto como aparece en SAP Logon

---

## 🔒 Seguridad

### Mejores Prácticas

✅ **Hacer**:
- Usar keyring del sistema para credenciales
- Cambiar contraseñas periódicamente
- No compartir credenciales
- Usar `.env` solo para desarrollo local
- Mantener `.env` en `.gitignore`

❌ **No hacer**:
- Commitear credenciales a git
- Compartir archivo `.env`
- Hardcodear contraseñas en código
- Usar credenciales de administrador

### Permisos de Archivo

Si usas `.env`, asegúrate de que solo tú tengas acceso:

```powershell
# Windows - Verificar permisos del archivo
icacls .env
```

---

## 📊 Comparación de Modos

| Característica | Existing Session | Credentials |
|----------------|------------------|-------------|
| SAP GUI abierto manualmente | ✅ Requerido | ❌ No necesario |
| Requiere credenciales | ❌ No | ✅ Sí |
| Velocidad | ⚡ Rápido | 🐢 Más lento (login) |
| Automatización desatendida | ❌ No | ✅ Sí |
| Ideal para | Desarrollo, pruebas | Producción, scripts programados |

---

## 💡 Ejemplos de Uso

### Desarrollo Interactivo

```powershell
# Modo: existing_session
# 1. Abrir SAP GUI manualmente
# 2. Ejecutar script
python main.py --task export_invoice --invoice XXX
```

### Automatización Desatendida

```powershell
# Modo: credentials
# Todo automático, sin intervención
python main.py --task export_invoice --invoice XXX
```

### Script Programado (Task Scheduler)

```powershell
# Crear tarea programada que ejecute:
C:\Users\Z1081401\Desktop\scripts_SAP\venv\Scripts\python.exe ^
  C:\Users\Z1081401\Desktop\scripts_SAP\main.py ^
  --task export_invoice --invoice 2025102419
```

---

## 🔮 Configuración Avanzada

### Idioma de Login (Opcional)

Agrega idioma a las credenciales:

```powershell
# Almacenar con idioma
python -m src.utils.credential_manager set \
  --username USER \
  --password PASS \
  --client 100 \
  --system-id DEV

# Luego editar manualmente .env para agregar idioma:
SAP_LANGUAGE=ES  # ES, EN, DE, etc.
```

### Múltiples Sistemas SAP

Para trabajar con múltiples sistemas, puedes:

1. Usar diferentes archivos `.env`:
   ```powershell
   # .env.dev
   SAP_USERNAME=user_dev
   # .env.prod
   SAP_USERNAME=user_prod
   ```

2. Cambiar `connection_string` en config según necesidad

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa `logs/app.log` para errores detallados
2. Verifica credenciales: `python -m src.utils.credential_manager get`
3. Prueba login manual en SAP GUI con las mismas credenciales
4. Verifica que SAP Scripting esté habilitado

---

**Última actualización**: 2025-11-27
