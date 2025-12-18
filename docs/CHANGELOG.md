# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## v1.1.0 (2025-12-05)

### ✨ Added
- Script `export_multi_client.py` para exportar facturas de múltiples clientes
- Soporte para lectura de lista de clientes desde archivo de texto
- Función `read_client_list()` para parsear archivos de clientes con comentarios
- Exportación masiva con resumen de resultados por cliente
- Sistema de control de versiones con `VERSION.txt` y `CHANGELOG.md`
- Guía completa de versionado en documentación

### 🔄 Changed
- Formato de exportación de Excel (XLSX) a CSV en configuración
- Aumentado tiempo de espera tras ejecutar transacción de 0.5s a 2.0s
- Mejorado manejo de errores en diálogo de exportación con fallback a formato por defecto
- Actualizado método `_handle_export_dialog()` con manejo robusto de errores

### 🐛 Fixed
- Error "The method got an invalid argument" en exportación CSV
- Error "The control could not be found by id" por tiempo de espera insuficiente
- Manejo graceful cuando el combo de formato de exportación no está disponible

---

## v1.0.0 (2025-11-27)

### ✨ Added
- Sistema de conexión SAP con dos modos: `existing_session` y `credentials`
- Gestión segura de credenciales con `credential_manager`
- Script `export_invoice.py` para exportar facturas individuales
- Sistema de logging configurable
- Utilidades SAP en `sap_utils.py`:
  - `find_alv_shell()` - Localizar grids ALV
  - `handle_security_popup()` - Manejar popups de seguridad
  - `close_excel_workbook()` - Cerrar archivos Excel automáticamente
- Documentación completa con MkDocs:
  - Arquitectura del sistema
  - Guías de uso
  - Diagramas de secuencia
- Inspector SAP para explorar interfaces
- Configuración centralizada en `config/settings.yaml`

### 🏗️ Infrastructure
- Estructura de proyecto modular por capas:
  - `src/core/` - Conexión y utilidades SAP
  - `src/scripts/` - Scripts de automatización
  - `src/utils/` - Herramientas auxiliares
- Sistema de configuración con YAML
- Gestión de credenciales con keyring
- Sistema de logs rotativo

---

## Categorías de Cambios

- ✨ **Added**: Nuevas funcionalidades
- 🔄 **Changed**: Cambios en funcionalidades existentes
- 🗑️ **Deprecated**: Funcionalidades que serán eliminadas próximamente
- ❌ **Removed**: Funcionalidades eliminadas
- 🐛 **Fixed**: Correcciones de bugs
- 🔒 **Security**: Cambios relacionados con seguridad
- 🏗️ **Infrastructure**: Cambios en estructura o configuración del proyecto
