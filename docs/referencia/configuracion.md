# Referencia de Configuración

Documentación completa de todos los parámetros de configuración del sistema.

## config/settings.yaml

### Sección: sap

#### connection_mode

**Tipo**: `string`  
**Valores**: `"existing_session"`, `"credentials"`  
**Default**: `"existing_session"`  
**Descripción**: Modo de conexión a SAP GUI

**Ejemplo**:
```yaml
sap:
  connection_mode: "credentials"
```

---

#### connection_index

**Tipo**: `int`  
**Valores**: `0`, `1`, `2`, ...  
**Default**: `0`  
**Aplicable**: Modo `existing_session`  
**Descripción**: Índice de la conexión SAP en SAP Logon

---

#### session_index

**Tipo**: `int`  
**Valores**: `0`, `1`, `2`, ...  
**Default**: `0`  
**Aplicable**: Modo `existing_session`  
**Descripción**: Índice de la sesión dentro de la conexión

---

#### connection_string

**Tipo**: `string`  
**Aplicable**: Modo `credentials`  
**Descripción**: Nombre del sistema SAP como aparece en SAP Logon

**Formato**: Texto exacto de la descripción en SAP Logon

**Ejemplos**:
```yaml
connection_string: "ECOSISCAT - ESX - Produccio"
connection_string: "SAP ECC Development"
connection_string: "/H/servidor.com/S/3200"
```

---

#### transaction_code

**Tipo**: `string`  
**Descripción**: Código de transacción SAP por defecto

**Formato**: `/n` seguido del código de transacción

**Ejemplos**:
```yaml
transaction_code: "/nZTSD_FACTURACION"
transaction_code: "/nVA05"
transaction_code: "/nSE38"
```

---

### Sección: export

#### default_directory

**Tipo**: `string`  
**Default**: `"exports"`  
**Descripción**: Directorio para archivos exportados

**Puede ser**:
- Ruta relativa al proyecto
- Ruta absoluta

**Ejemplos**:
```yaml
default_directory: "exports"
default_directory: "C:\\Users\\Z1081401\\Desktop\\exports"
default_directory: "D:\\SAP_Exports"
```

---

#### default_filename_prefix

**Tipo**: `string`  
**Default**: `"EXPORT_"`  
**Descripción**: Prefijo para nombres de archivos exportados

**Ejemplo**:
```yaml
default_filename_prefix: "FACTURA_"
# Genera: FACTURA_20251127_120000.csv
```

---

#### format

**Tipo**: `string`  
**Default**: `"csv-LEAN-STANDARD"`  
**Descripción**: Formato de exportación SAP ALV

**Valores comunes**:
- `"csv-LEAN-STANDARD"`: CSV estándar
- `"xlsx"`: Excel
- `"xml"`: XML

---

### Sección: logging

#### level

**Tipo**: `string`  
**Valores**: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`  
**Default**: `"INFO"`  
**Descripción**: Nivel de detalle de logs

**Niveles**:
- `DEBUG`: Información muy detallada (desarrollo)
- `INFO`: Información general (default)
- `WARNING`: Advertencias
- `ERROR`: Errores recuperables
- `CRITICAL`: Errores fatales

**Ejemplo**:
```yaml
logging:
  level: "DEBUG"  # Para desarrollo
  # level: "WARNING"  # Para producción
```

---

#### file

**Tipo**: `string`  
**Default**: `"logs/app.log"`  
**Descripción**: Archivo de log

**Puede ser**:
- Ruta relativa al proyecto
- Ruta absoluta

---

#### format

**Tipo**: `string`  
**Default**: `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"`  
**Descripción**: Formato de mensajes de log

**Formato Python logging**:
- `%(asctime)s`: Timestamp
- `%(name)s`: Logger name
- `%(levelname)s`: Nivel (INFO, ERROR, etc.)
- `%(message)s`: Mensaje

---

### Sección: timeouts

#### default_wait

**Tipo**: `float`  
**Default**: `0.5`  
**Unidad**: Segundos  
**Descripción**: Espera general entre operaciones SAP

**Recomendaciones**:
- Desarrollo: `1.0` (más lento, debugging)
- Producción: `0.3` - `0.5` (más rápido)

---

#### login_wait

**Tipo**: `float`  
**Default**: `2.0`  
**Unidad**: Segundos  
**Descripción**: Espera después de login automático

---

#### export_wait

**Tipo**: `float`  
**Default**: `3.0`  
**Unidad**: Segundos  
**Descripción**: Espera durante exportaciones

---

## config/secrets.yaml

### Sección: sap_credentials

#### username

**Tipo**: `string`  
**Requerido**: Sí (para modo `credentials`)  
**Descripción**: Usuario SAP

---

#### password

**Tipo**: `string`  
**Requerido**: Sí (para modo `credentials`)  
**Descripción**: Contraseña SAP

**Seguridad**: ⚠️ Archivo debe estar en `.gitignore`

---

#### client

**Tipo**: `string`  
**Requerido**: Sí (para modo `credentials`)  
**Descripción**: Mandante SAP

**Formato**: Número de 3 dígitos (como string)

**Ejemplos**: `"100"`, `"200"`, `"300"`, `"800"`

---

#### system_id

**Tipo**: `string`  
**Requerido**: No  
**Descripción**: Identificador descriptivo del sistema

**Uso**: Solo para logs y referencia interna

---

#### language

**Tipo**: `string`  
**Requerido**: No  
**Descripción**: Código de idioma para login

**Valores comunes**: `"ES"`, `"EN"`, `"CA"`, `"DE"`, `"FR"`

---

## Variables de Entorno (.env)

Alternativa a `secrets.yaml`:

### SAP_USERNAME

**Tipo**: Cadena  
**Descripción**: Usuario SAP

---

### SAP_PASSWORD

**Tipo**: Cadena  
**Descripción**: Contraseña SAP

---

### SAP_CLIENT

**Tipo**: Cadena  
**Descripción**: Mandante SAP

---

### SAP_SYSTEM_ID

**Tipo**: Cadena  
**Descripción**: Identificador del sistema

---

### SAP_LANGUAGE

**Tipo**: Cadena  
**Descripción**: Código de idioma

---

## Ejemplos Completos

### Configuración Desarrollo

**settings.yaml**:
```yaml
sap:
  connection_mode: "existing_session"
  connection_index: 0
  session_index: 0
  transaction_code: "/nZTSD_FACTURACION"

export:
  default_directory: "exports"
  default_filename_prefix: "DEV_"
  format: "csv-LEAN-STANDARD"

logging:
  level: "DEBUG"
  file: "logs/app.log"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

timeouts:
  default_wait: 1.0
  login_wait: 2.0
  export_wait: 3.0
```

### Configuración Producción

**settings.yaml**:
```yaml
sap:
  connection_mode: "credentials"
  connection_string: "ECOSISCAT - ESX - Produccio"
  transaction_code: "/nZTSD_FACTURACION"

export:
  default_directory: "D:\\SAP_Exports"
  default_filename_prefix: "PROD_"
  format: "csv-LEAN-STANDARD"

logging:
  level: "WARNING"
  file: "D:\\SAP_Logs\\app.log"
  format: "%(asctime)s - %(levelname)s - %(message)s"

timeouts:
  default_wait: 0.3
  login_wait: 2.0
  export_wait: 3.0
```

**secrets.yaml**:
```yaml
sap_credentials:
  username: "Z1081401S"
  password: "password_seguro"
  client: "300"
  system_id: "SAP_PROD"
  language: "ES"
```

## Validación

### Validar YAML

```powershell
python -c "import yaml; yaml.safe_load(open('config/settings.yaml'))"
python -c "import yaml; yaml.safe_load(open('config/secrets.yaml'))"
```

Si no hay errores, la configuración es válida.

## Referencias

- [Configuración](../guias/configuracion.md): Guía de configuración
- [Login Automático](../guias/login-automatico.md): Configurar autenticación
