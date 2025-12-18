# Configuración

Guía de configuración del sistema de automatización SAP.

## Archivos de Configuración

### Ubicación

```
config/
├── settings.yaml    # Configuración general del sistema
└── secrets.yaml     # Credenciales SAP (crear manualmente)
```

## settings.yaml

### Estructura

```yaml
sap:
  # Modo de conexión
  connection_mode: "existing_session"  # o "credentials"
  
  # Para existing_session
  connection_index: 0
  session_index: 0
  
  # Para credentials
  connection_string: "Nombre Sistema SAP"
  
  # Transacción por defecto
  transaction_code: "/nZTSD_FACTURACION"

export:
  default_directory: "exports"
  default_filename_prefix: "EXPORT_"
  format: "csv-LEAN-STANDARD"

logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: "logs/app.log"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

timeouts:
  default_wait: 0.5
  login_wait: 2.0
  export_wait: 3.0
```

### Parámetros SAP

| Parámetro | Descripción | Valores |
|-----------|-------------|---------|
| `connection_mode` | Modo de conexión | `"existing_session"`, `"credentials"` |
| `connection_index` | Índice de conexión SAP | `0`, `1`, `2`, ... |
| `session_index` | Índice de sesión | `0`, `1`, `2`, ... |
| `connection_string` | Nombre del sistema en SAP Logon | Texto exacto de Descripción |
| `transaction_code` | Código de transacción | Ej: `"/nVA05"`, `"/nSE38"` |

### Parámetros de Exportación

| Parámetro | Descripción | Default |
|-----------|-------------|---------|
| `default_directory` | Carpeta de exportaciones | `"exports"` |
| `default_filename_prefix` | Prefijo de archivos | `"EXPORT_"` |
| `format` | Formato de exportación SAP | `"csv-LEAN-STANDARD"` |

### Parámetros de Logging

| Parámetro | Descripción | Valores |
|-----------|-------------|---------|
| `level` | Nivel de detalle de logs | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `file` | Archivo de log | Ruta relativa o absoluta |
| `format` | Formato de mensajes | Formato Python logging |

### Parámetros de Timeouts

| Parámetro | Descripción | Valor (segundos) |
|-----------|-------------|------------------|
| `default_wait` | Espera general | `0.5` |
| `login_wait` | Espera post-login | `2.0` |
| `export_wait` | Espera en exportaciones | `3.0` |

## secrets.yaml

### Crear Archivo

```powershell
# Copiar plantilla (si existe)
# O crear manualmente
notepad config\secrets.yaml
```

### Estructura

```yaml
# SAP Credentials Configuration
# IMPORTANTE: Este archivo contiene información sensible
# NO compartir ni commitear a git

sap_credentials:
  username: "usuario_sap"
  password: "contraseña_sap"
  client: "300"
  system_id: "SAP_SYSTEM"
  language: "ES"  # ES, EN, CA, DE, etc.
```

### Parámetros

| Campo | Descripción | Requerido | Ejemplo |
|-------|-------------|-----------|---------|
| `username` | Usuario SAP | Sí | `"Z1081401S"` |
| `password` | Contraseña SAP | Sí | `"MiPass123"` |
| `client` | Mandante (Client) | Sí | `"300"`, `"100"` |
| `system_id` | Identificador del sistema | No | `"SAP_ECOFIN"` |
| `language` | Idioma de login | No | `"ES"`, `"EN"`, `"CA"` |

### Seguridad

El archivo `secrets.yaml` debe:

- ✅ Estar en `.gitignore`
- ✅ Tener permisos restrictivos
- ❌ NO commitear a git
- ❌ NO compartir por email/chat

## Modos de Conexión

### Existing Session

Conecta a sesión SAP ya abierta manualmente.

**Configuración**:
```yaml
sap:
  connection_mode: "existing_session"
  connection_index: 0
  session_index: 0
```

**Uso**:
1. Abrir SAP Logon manualmente
2. Conectar y hacer login
3. Ejecutar script

**Ventajas**:
- No requiere credenciales
- Más rápido (sin login)
- Más seguro

**Desventajas**:
- Requiere intervención manual
- No funciona en automatización desatendida

### Credentials

Login automático con credenciales almacenadas.

**Configuración**:
```yaml
sap:
  connection_mode: "credentials"
  connection_string: "ECOSISCAT - ESX - Produccio"
```

Además, crear `config/secrets.yaml` con credenciales.

**Uso**:
1. Ejecutar script
2. Sistema hace login automáticamente

**Ventajas**:
- Totalmente automático
- Ideal para scripts programados
- No requiere SAP GUI abierto

**Desventajas**:
- Requiere gestión de credenciales
- Más lento (tiempo de login)

## Encontrar connection_string

### Desde SAP Logon

1. Abrir SAP Logon
2. Click derecho en la conexión
3. Seleccionar "Propiedades"
4. Copiar el campo **"Descripción"** exactamente

**Ejemplo**: `"ECOSISCAT - ESX - Produccio"`

### Alternativa: connection_string técnica

Si falla con descripción, usar formato técnico:

```
/H/servidor.dominio.com/S/3200
```

Donde:
- `servidor.dominio.com`: Hostname del servidor SAP
- `3200`: Puerto (número de instancia × 100 + 3200)

## Configuración por Entorno

### Desarrollo

```yaml
sap:
  connection_mode: "existing_session"

logging:
  level: "DEBUG"
  
timeouts:
  default_wait: 1.0  # Más lento para debugging
```

### Producción

```yaml
sap:
  connection_mode: "credentials"

logging:
  level: "WARNING"
  
timeouts:
  default_wait: 0.3  # Más rápido
```

## Validar Configuración

### Test de Configuración

```powershell
# Verificar que se lee correctamente
python -c "import yaml; print(yaml.safe_load(open('config/settings.yaml')))"
```

### Test de Credenciales

```powershell
python -m src.utils.credential_manager get
```

Debe mostrar credenciales (password oculto).

## Próximos Pasos

- [Login Automático](login-automatico.md): Configurar autenticación
- [Crear Script](crear-script.md): Desarrollar automatización
- [Referencia Configuración](../referencia/configuracion.md): Detalles avanzados
