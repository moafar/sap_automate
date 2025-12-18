# SAP Automation Scripts

![Version](https://img.shields.io/badge/version-1.1.0-blue)
![Python](https://img.shields.io/badge/python-3.7+-green)

Proyecto de automatización de procesos SAP GUI usando Python y win32com. Actualmente incluye funcionalidad de exportación de facturas con arquitectura modular preparada para futuras expansiones.

📋 **[Ver CHANGELOG](docs/CHANGELOG.md)** para historial completo de cambios.

## 📁 Estructura del Proyecto

```
scripts_SAP/
├── src/
│   ├── core/              # Componentes principales
│   │   ├── sap_connection.py   # Gestión de conexión SAP
│   │   └── sap_utils.py        # Utilidades SAP compartidas
│   ├── scripts/           # Scripts de automatización
│   │   └── export_invoice.py  # Exportador de facturas
│   └── utils/             # Herramientas de soporte
│       ├── logger.py           # Configuración de logging
│       ├── credential_manager.py  # Gestión segura de credenciales
│       └── sap_inspector.py    # Inspector de interfaz (desarrollo)
├── config/
│   └── settings.yaml      # Configuración del proyecto
├── exports/               # Archivos CSV exportados
├── logs/                  # Archivos de log
├── main.py                # Punto de entrada principal
├── requirements.txt       # Dependencias Python
├── .env.example          # Plantilla de variables de entorno
└── README.md             # Este archivo
```

## 🚀 Instalación

### Requisitos previos
- Python 3.7 o superior
- SAP GUI instalado en Windows
- SAP Scripting habilitado

### Pasos de instalación

1. **Clonar o descargar el proyecto**
   ```powershell
   cd C:\Users\Z1081401\Desktop\scripts_SAP
   ```

2. **Crear entorno virtual** (recomendado)
   ```powershell
   # Crear venv
   python -m venv venv
   
   # Activar venv
   .\venv\Scripts\Activate.ps1
   
   # Si da error de permisos, ejecutar una vez:
   # Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Instalar dependencias**
   ```powershell
   # Con el venv activado (verás "(venv)" en el prompt)
   pip install -r requirements.txt
   ```

4. **Configurar modo de conexión**

   El proyecto soporta dos modos:
   
   **Modo A: Existing Session** (Por defecto - más simple)
   ```powershell
   # Solo abrir SAP GUI manualmente antes de ejecutar
   # No requiere configuración adicional
   #    connection_string: "Nombre Sistema SAP"  # Como aparece en SAP Logon
   ```
   
   📖 **Guía completa**: Ver [docs/LOGIN_AUTOMATICO.md](docs/LOGIN_AUTOMATICO.md)

## 🔧 Configuración

### Archivo `config/settings.yaml`

```yaml
sap:
  # Modo de conexión: "existing_session" o "credentials"
  connection_mode: "existing_session"  # Por defecto
  
  # Para existing_session (sesión ya abierta):
  connection_index: 0
  session_index: 0
  
  # Para credentials (login automático):
  connection_string: ""  # Nombre del sistema SAP (de SAP Logon)
  
  transaction_code: "/nZTSD_FACTURACION"
```

**Modos de conexión:**

| Modo | Descripción | Uso |
|------|-------------|-----|
| `existing_session` | Conecta a sesión SAP GUI ya abierta | Desarrollo, uso interactivo |
| `credentials` | Login automático con credenciales | Automatización, scripts programados |

📖 **Configurar login automático**: Ver [docs/LOGIN_AUTOMATICO.md](docs/LOGIN_AUTOMATICO.md)

## 📝 Uso

### Exportar Factura

```powershell
# Requiere SAP GUI abierto con una sesión activa
python main.py --task export_invoice --invoice 2025102419
```

El archivo CSV se guardará en `exports/` con formato:
```
EXPORT_ZTSD_FACTURACION_20251127_120000.csv
```

### Exportar Múltiples Clientes

Exporta facturas para múltiples clientes con filtros comunes.

**Los clientes se leen desde un archivo de texto** (un código por línea):

```powershell
# Exportar clientes desde archivo con valores por defecto
python main.py --task export_multi_client --clients-file config/clients.txt

# Con filtros personalizados
python main.py --task export_multi_client \
    --clients-file config/clients.txt \
    --month-from 1 \
    --month-to 10 \
    --year 2025 \
    --status F
```

**Formato del archivo de clientes:**
```txt
# Comentarios comienzan con #
CLI001
CLI002
CLI003
```

**Parámetros disponibles:**
- `--clients-file`: Ruta al archivo con códigos de clientes (requerido)
- `--month-from`: Mes inicial de facturación (default: 1)
- `--month-to`: Mes final de facturación (default: 10)
- `--year`: Año de facturación (default: 2025)
- `--status`: Status de facturación (default: F)

Los archivos se guardarán en `exports/` con formato:
```
EXPORT_CLIENT_CLI001_2025M01-10_20251128_083000.csv
EXPORT_CLIENT_CLI002_2025M01-10_20251128_083015.csv
EXPORT_CLIENT_CLI003_2025M01-10_20251128_083030.csv
```

### Inspector SAP (Herramienta de desarrollo)

Utilidad para explorar la estructura de la interfaz SAP durante el desarrollo de nuevas funcionalidades:

```powershell
# Inspección básica de la ventana principal
python -m src.utils.sap_inspector

# Exportar estructura a JSON
python -m src.utils.sap_inspector --output structure.json

# Exportar a texto
python -m src.utils.sap_inspector --output structure.txt --format txt

# Inspeccionar ventana modal específica
python -m src.utils.sap_inspector --window-id "wnd[1]"

# Limitar profundidad del árbol
python -m src.utils.sap_inspector --max-depth 5
```

El inspector detecta y marca:
- `[ALV]` - Grids ALV
- `[BTN]` - Botones
- `[TXT]` - Campos de texto

### Gestión de Credenciales

```powershell
# Almacenar credenciales en keyring
python -m src.utils.credential_manager set --username USER --password PASS --client 100 --system-id DEV

# Ver credenciales almacenadas (password oculto)
python -m src.utils.credential_manager get

# Eliminar credenciales
python -m src.utils.credential_manager delete
```

## 🔒 Seguridad de Credenciales

Las credenciales SAP **NUNCA** deben almacenarse en texto plano en archivos de código o configuración.

### Opciones disponibles:

1. **Variables de entorno** (`.env`)
   - Archivo `.env` excluido de git via `.gitignore`
   - Adecuado para desarrollo local
   - No commitear nunca el archivo `.env`

2. **Keyring del sistema** (recomendado)
   - Usa el almacén seguro del sistema operativo (Windows Credential Manager)
   - Credenciales encriptadas por el SO
   - Más seguro para uso en producción

3. **Sesión existente** (más simple)
   - No requiere credenciales
   - Conecta a sesión SAP GUI ya abierta manualmente
   - Modo por defecto

## 🛠️ Desarrollo de Nuevas Funcionalidades

### Estructura modular

El proyecto usa una arquitectura modular:

- **`src/core/`**: Componentes reutilizables (conexión, utilidades)
- **`src/scripts/`**: Scripts de automatización específicos
- **`src/utils/`**: Herramientas de soporte

### Crear un nuevo script

1. Crear archivo en `src/scripts/nombre_script.py`
2. Implementar clase con método `run()`
3. Agregar task en `main.py`
4. Usar el inspector para explorar la interfaz

Ejemplo:

```python
# src/scripts/mi_nueva_tarea.py
import logging
logger = logging.getLogger("SAP_Automation")

class MiNuevaTarea:
    def __init__(self, session, config):
        self.session = session
        self.config = config
    
    def run(self, parametro):
        logger.info(f"Ejecutando tarea con: {parametro}")
        # Implementación aquí
        return True
```

```python
# En main.py, agregar:
from src.scripts.mi_nueva_tarea import MiNuevaTarea

# En dispatch task:
elif args.task == "mi_tarea":
    tarea = MiNuevaTarea(session, config)
    success = tarea.run(args.parametro)
```

## 📊 Logging

Los logs se guardan automáticamente en `logs/app.log` con formato:
```
2025-11-27 12:00:00 - SAP_Automation - INFO - Task finished successfully.
```

Nivel de log configurable en `config/settings.yaml`:
- `DEBUG`: Información detallada para debugging
- `INFO`: Información general de operación (default)
- `WARNING`: Advertencias
- `ERROR`: Errores
- `CRITICAL`: Errores críticos

## ⚠️ Troubleshooting

### SAP Scripting no habilitado
```
Error: Scripting is not enabled
```
**Solución**: Habilitar scripting en SAP GUI:
1. SAP Logon → Options → Accessibility & Scripting → Scripting
2. Marcar "Enable scripting"

### No se encuentra la sesión
```
RuntimeError: No hay conexiones abiertas en SAP Logon
```
**Solución**: Abrir SAP GUI manualmente antes de ejecutar el script

### Error de permisos
```
Error: Access denied
```
**Solución**: Ejecutar como administrador o verificar permisos de SAP

## 📋 Tareas Disponibles

Actualmente el proyecto soporta:

| Tarea | Comando | Descripción |
|-------|---------|-------------|
| `export_invoice` | `--task export_invoice --invoice NUM` | Exporta factura individual a CSV |
| `export_multi_client` | `--task export_multi_client --clients-file FILE` | Exporta facturas de múltiples clientes desde archivo |

## 🔮 Roadmap

Funcionalidades planeadas para futuras versiones:

- [ ] Login automático con credenciales
- [ ] Exportación masiva de facturas
- [ ] Integración con base de datos
- [ ] Generación de reportes
- [ ] Dashboard web
- [ ] Tests automatizados

## 📄 Licencia

Proyecto interno - Uso privado

## 👤 Autor

Usuario Z1081401

---
**Versión actual**: 1.1.0 | **Última actualización**: 2025-12-05
