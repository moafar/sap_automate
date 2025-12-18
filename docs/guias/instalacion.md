# Instalación

Guía para configurar el entorno de desarrollo del sistema de automatización SAP.

## Requisitos Previos

### Software Necesario

- **Python 3.7 o superior**
- **SAP GUI** instalado y configurado
- **SAP Logon** con conexiones configuradas
- **Git** (opcional, para control de versiones)

### Configuración Crítica de SAP GUI

!!! warning "Configuración de Seguridad Requerida"
    Es **imprescindible** desactivar el módulo de seguridad de SAP GUI para que el scripting funcione correctamente.

**Pasos para desactivar**:

1. Abrir **SAP Logon** o **SAP GUI**
2. Presionar `ALT + F12` (abre menú de opciones)
3. Navegar a: **Seguridad** → **Configuración de seguridad**
4. En la opción **"Modul de seguretat"** seleccionar: **"Desactivats"**
5. Confirmar y cerrar

**Verificación**:
- La configuración debe mostrar "Desactivats" en "Modul de seguretat"
- Sin esta configuración, el scripting no podrá interactuar con SAP GUI

### Verificación de Python

```bash
python --version
# Output esperado: Python 3.x.x
```

## Proceso de Instalación

### 1. Clonar o Descargar el Proyecto

```bash
cd C:\Users\Z1081401\Desktop
# Si se tiene en repositorio:
# git clone <url-repositorio> scripts_SAP

cd scripts_SAP
```

### 2. Crear Entorno Virtual

```powershell
# Crear venv
python -m venv venv

# Activar venv
.\venv\Scripts\Activate.ps1
```

**Nota**: Si aparece error de permisos:

```powershell
# Ejecutar una sola vez
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Instalar Dependencias

```powershell
# Con venv activado (debe aparecer "(venv)" en el prompt)
pip install -r requirements.txt
```

**Dependencias instaladas**:
- `pywin32`: Interacción con SAP GUI
- `pyyaml`: Gestión de configuración
- `python-dotenv`: Variables de entorno
- `keyring`: Almacenamiento seguro
- `mkdocs`: Documentación (opcional)
- `mkdocs-material`: Tema de documentación (opcional)

### 4. Verificar Instalación

```powershell
# Verificar importaciones
python -c "import win32com.client; print('pywin32: OK')"
python -c "import yaml; print('pyyaml: OK')"
```

## Configuración Inicial

### Estructura de Directorios

El proyecto creará automáticamente los directorios necesarios:

```
scripts_SAP/
├── config/          # Archivos de configuración
├── exports/         # Archivos exportados
├── logs/            # Registros de ejecución
└── venv/            # Entorno virtual
```

### Verificar SAP GUI

```powershell
# Test de conexión SAP
python -c "import win32com.client; sap=win32com.client.GetObject('SAPGUI'); print('SAP GUI disponible')"
```

Si da error, asegurarse que:
- SAP Logon está instalado
- SAP Scripting está habilitado

## Habilitación de SAP Scripting

### En Cliente SAP

1. Abrir SAP Logon
2. `Opciones` → ` Accesibilidad y scripting` → `Scripting`
3. Marcar **"Habilitar scripting"**
4. Desmarcar **"Notificar cuando un script adjunte SAP GUI"** (opcional)

### En Servidor SAP (requiere permisos)

Ejecutar en SAP:

```
Transaction: RZ11
Parameter: sapgui/user_scripting
Value: TRUE
```

## Verificación Final

### Test Completo

```powershell
# Ejecutar test de inspector
python -m src.utils.sap_inspector --help
```

Debe mostrar ayuda del comando sin errores.

## Troubleshooting

### Error: "No module named win32com"

```powershell
pip install --upgrade pywin32
python venv\Scripts\pywin32_postinstall.py -install
```

### Error: "SAPGUI Object not found"

- Verificar que SAP Logon está instalado
- Abrir SAP Logon al menos una vez
- Verificar que scripting está habilitado

### Error: Permisos de ejecución

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Próximos Pasos

- [Configuración](configuracion.md): Configurar credenciales y sistema
- [Login Automático](login-automatico.md): Configurar autenticación
- [Crear Script](crear-script.md): Desarrollar primera automatización
