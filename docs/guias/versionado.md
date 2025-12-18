# Control de Versiones

Esta guía explica cómo manejar versiones y documentar cambios en el proyecto.

## Versionado Semántico

El proyecto sigue [Semantic Versioning 2.0.0](https://semver.org/lang/es/):

```
MAJOR.MINOR.PATCH
```

### Incrementar Versión

- **MAJOR** (1.0.0 → 2.0.0): Cambios incompatibles con versiones anteriores
  - Cambios en la estructura de configuración que rompen compatibilidad
  - Eliminación de funcionalidades
  - Cambios en la API de scripts que requieren modificar código existente

- **MINOR** (1.0.0 → 1.1.0): Nuevas funcionalidades compatibles
  - Nuevos scripts de automatización
  - Nuevas opciones de configuración (con valores por defecto)
  - Mejoras que no afectan funcionalidad existente

- **PATCH** (1.0.0 → 1.0.1): Correcciones de bugs
  - Arreglar errores
  - Mejorar tiempos de espera
  - Correcciones de documentación

## Archivos de Versionado

### VERSION.txt

Contiene únicamente el número de versión actual:

```
1.1.0
```

### CHANGELOG.md

Documenta todos los cambios siguiendo el formato [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

## Proceso de Release

### 1. Hacer Cambios

Desarrolla tus cambios normalmente en el proyecto.

### 2. Documentar en CHANGELOG.md

Agrega una entrada en la sección superior del `CHANGELOG.md`:

```markdown
## [Unreleased]

### Added
- Nueva funcionalidad X

### Changed
- Modificado comportamiento de Y

### Fixed
- Corregido error en Z
```

### 3. Determinar Nueva Versión

Basándote en los cambios, determina si es MAJOR, MINOR o PATCH.

### 4. Actualizar Archivos

#### a) Actualizar VERSION.txt

```bash
# Ejemplo: de 1.1.0 a 1.2.0
echo 1.2.0 > VERSION.txt
```

#### b) Actualizar CHANGELOG.md

Cambia `[Unreleased]` por la versión y fecha:

```markdown
## [1.2.0] - 2025-12-15

### Added
- Nueva funcionalidad X
...
```

### 5. Crear Tag Git (Opcional)

Si usas Git:

```bash
git add VERSION.txt CHANGELOG.md
git commit -m "Release version 1.2.0"
git tag -a v1.2.0 -m "Version 1.2.0"
git push origin main --tags
```

## Categorías de Cambios

### Added
Nuevas funcionalidades, archivos, scripts.

**Ejemplo**:
```markdown
### Added
- Script `export_payments.py` para exportar pagos
- Parámetro CLI `--output-format` para elegir formato de salida
```

### Changed
Modificaciones a funcionalidades existentes.

**Ejemplo**:
```markdown
### Changed
- Aumentado timeout por defecto de 0.5s a 1.0s
- Mejorado logging en `sap_connection.py` con más detalles
```

### Deprecated
Funcionalidades que se eliminarán en futuras versiones.

**Ejemplo**:
```markdown
### Deprecated
- Parámetro `--old-format` será eliminado en v2.0.0
- Usar `--format` en su lugar
```

### Removed
Funcionalidades eliminadas.

**Ejemplo**:
```markdown
### Removed
- Eliminado soporte para Python 3.7
- Removido script obsoleto `legacy_export.py`
```

### Fixed
Correcciones de bugs.

**Ejemplo**:
```markdown
### Fixed
- Corregido error "control not found" en transacciones lentas
- Arreglado encoding en logs de Windows
```

### Security
Cambios relacionados con vulnerabilidades.

**Ejemplo**:
```markdown
### Security
- Actualizado almacenamiento de credenciales para usar keyring
- Mejorada validación de paths de archivos
```

## Historial de Versiones

Consulta [CHANGELOG.md](../CHANGELOG.md) para el historial completo de versiones.

## Versión Actual

La versión actual del proyecto se encuentra en [VERSION.txt](../VERSION.txt).

Para consultar la versión desde Python:

```python
import os

def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'VERSION.txt')
    with open(version_file, 'r') as f:
        return f.read().strip()

print(f"Version: {get_version()}")
```

## Plantilla para Nuevas Versiones

Al crear una nueva versión, usa esta plantilla en `CHANGELOG.md`:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- 

### Changed
- 

### Deprecated
- 

### Removed
- 

### Fixed
- 

### Security
- 
```

Elimina las secciones que no apliquen.
