# Capa Core

La capa Core contiene los componentes fundamentales para interactuar con SAP GUI. Proporciona abstracción de bajo nivel para conexión, autenticación y manipulación de

 interfaces.

## Componentes

### SAPConnection

**Ubicación**: `src/core/sap_connection.py`

**Responsabilidad**: Gestionar conexión y autenticación con SAP GUI

#### Arquitectura

```mermaid
classDiagram
    class SAPConnection {
        +connection_index: int
        +session_index: int
        +connection_mode: str
        +connection_string: str
        +credentials: dict
        +session
        +connection
        +__init__()
        +connect() session
        +get_session() session
        +disconnect()
        -_connect_existing_session() session
        -_connect_with_credentials() session
        -_start_sap_logon()
        -_login()
    }
```

#### Flujo de Conexión - Modo Existing Session

```mermaid
sequenceDiagram
    participant Client as Cliente
    participant SC as SAPConnection
    participant SAPGUI as SAP GUI

    Client->>SC: connect()
    SC->>SC: _connect_existing_session()
    SC->>SAPGUI: GetObject("SAPGUI")
    SAPGUI-->>SC: SAP GUI Application
    SC->>SAPGUI: GetScriptingEngine
    SAPGUI-->>SC: Scripting Engine
    SC->>SAPGUI: Children(connection_index)
    SAPGUI-->>SC: Connection
    SC->>SAPGUI: Children(session_index)
    SAPGUI-->>SC: Session
    SC-->>Client: Session establecida
```

#### Flujo de Conexión - Modo Credentials

```mermaid
sequenceDiagram
    participant Client as Cliente
    participant SC as SAPConnection
    participant SAPGUI as SAP GUI
    participant Logon as SAP Logon

    Client->>SC: connect()    SC->>SC: _connect_with_credentials()
    SC->>SAPGUI: GetObject("SAPGUI")
    
    alt SAP Logon no ejecutándose
        SAPGUI-->>SC: Error
        SC->>SC: _start_sap_logon()
        SC->>Logon: Iniciar proceso
        Logon-->>SC: Proceso iniciado
        SC->>SC: Esperar 3 segundos
        SC->>SAPGUI: GetObject("SAPGUI")
    end
    
    SAPGUI-->>SC: SAP GUI Application
    SC->>SAPGUI: OpenConnection(connection_string)
    SAPGUI-->>SC: Nueva conexión
    SC->>SAPGUI: Children(0)
    SAPGUI-->>SC: Session
    SC->>SC: _login()
    SC->>SAPGUI: Rellenar campos login
    SC->>SAPGUI: sendVKey(0)
    SAPGUI-->>SC: Login completado
    SC-->>Client: Session autenticada
```

#### Método: connect()

**Descripción**: Establece conexión con SAP basándose en el modo configurado

**Retorna**: Objeto session de SAP GUI

**Excepciones**:
- `ValueError`: Modo de conexión inválido
- `RuntimeError`: Error en conexión o autenticación
- `IndexError`: Índices fuera de rango

**Ejemplo de uso**:

```python
from src.core.sap_connection import SAPConnection

# Modo existing_session
conn = SAPConnection(
    connection_index=0,
    session_index=0,
    connection_mode="existing_session"
)
session = conn.connect()

# Modo credentials
credentials = {
    "username": "usuario",
    "password": "pass",
    "client": "300"
}
conn = SAPConnection(
    connection_mode="credentials",
    connection_string="ECOSISCAT - ESX - Produccio",
    credentials=credentials
)
session = conn.connect()
```

#### Método: _login()

**Descripción**: Realiza login automático rellenando campos de la pantalla

**Flujo**:

```mermaid
sequenceDiagram
    participant Login as _login()
    participant GUI as SAP GUI

    Login->>Login: Esperar 1 segundo
    Login->>GUI: findById("wnd[0]")
    GUI-->>Login: Ventana principal
    
    Login->>GUI: Rellenar Mandante
    Login->>GUI: Rellenar Usuario
    Login->>GUI: Rellenar Password
    
    opt Idioma especificado
        Login->>GUI: Rellenar Idioma
    end
    
    Login->>GUI: sendVKey(0)
    Login->>Login: Esperar 2 segundos
    
    alt Error de login
        Login->>GUI: findById("wnd[1]")
        GUI-->>Login: Ventana de error
        Login->>GUI: Leer mensaje de error
        Login->>Login: RuntimeError
    else Login exitoso
        Login->>Login: Log success
    end
```

**Campos rellenados**:

| Campo | ID SAP | Variable |
|-------|--------|----------|
| Mandante | `wnd[0]/usr/txtRSYST-MANDT` | `client` |
| Usuario | `wnd[0]/usr/txtRSYST-BNAME` | `username` |
| Password | `wnd[0]/usr/pwdRSYST-BCODE` | `password` |
| Idioma | `wnd[0]/usr/txtRSYST-LANGU` | `language` |

---

### sap_utils

**Ubicación**: `src/core/sap_utils.py`

**Responsabilidad**: Utilidades para manipular componentes de SAP GUI

#### Funciones Principales

##### find_alv_shell()

**Descripción**: Localiza componentes ALV Grid en la interfaz SAP

**Flujo de búsqueda**:

```mermaid
graph TD
    A[Inicio: root component] --> B{Es GuiShell?}
    B -->|Sí| C{Tiene GetCellValue?}
    C -->|Sí| D[Retornar component]
    C -->|No| E[Explorar hijos]
    B -->|No| E
    E --> F{Más hijos?}
    F -->|Sí| B
    F -->|No| G[Retornar None]
```

**Firma**:

```python
def find_alv_shell(root) -> Optional[object]
```

**Parámetros**:
- `root`: Componente raíz desde donde buscar

**Retorna**:
- Componente `GuiShell` del ALV si se encuentra
- `None` si no se encuentra

**Ejemplo**:

```python
from src.core.sap_utils import find_alv_shell

wnd = session.findById("wnd[0]")
alv = find_alv_shell(wnd)

if alv:
    row_count = alv.RowCount
    column_count = alv.ColumnCount
```

##### handle_security_popup()

**Descripción**: Detecta y acepta popups de seguridad de SAP

**Flujo**:

```mermaid
sequenceDiagram
    participant H as handle_security_popup()
    participant SAP as SAP GUI

    loop 6 intentos (cada 0.5s)
        loop Ventanas wnd[1], wnd[2]
            H->>SAP: findById("wnd[i]")
            alt Ventana encontrada
                SAP-->>H: Ventana modal
                H->>H: Buscar botón "Permitir/Allow"
                alt Botón encontrado
                    H->>SAP: press()
                    H->>H: Retornar
                end
            end
        end
        H->>H: Esperar 0.5s
    end
```

##### close_excel_workbook()

**Descripción**: Cierra libro Excel abierto por SAP tras exportación

**Parámetros**:
- `full_path`: Ruta completa del archivo Excel

**Flujo**:

```mermaid
graph TD
    A[Inicio] --> B{Excel abierto?}
    B -->|No| C[Retornar]
    B -->|Sí| D[Buscar workbook]
    D --> E{Encontrado?}
    E -->|No| C
    E -->|Sí| F[Cerrar sin guardar]
    F --> G{Único workbook?}
    G -->|Sí| H[Cerrar Excel]
    G -->|No| C
```

## Patrones de Uso

### Inicialización de Conexión

```python
from src.core.sap_connection import SAPConnection
from src.utils.credential_manager import get_credentials

# Cargar credenciales
credentials = get_credentials()

# Inicializar conexión
sap_conn = SAPConnection(
    connection_mode="credentials",
    connection_string="Sistema SAP",
    credentials=credentials
)

# Conectar
session = sap_conn.connect()

# Usar sesión
session.findById("wnd[0]/tbar[0]/okcd").Text = "/nSE38"
session.findById("wnd[0]").sendVKey(0)

# Limpiar
sap_conn.disconnect()
```

### Búsqueda y Manipulación de ALV

```python
from src.core.sap_utils import find_alv_shell

# Ejecutar transacción que muestra ALV
session.findById("wnd[0]/tbar[0]/okcd").Text = "/nSE16"
session.findById("wnd[0]").sendVKey(0)

# Buscar ALV
wnd = session.findById("wnd[0]")
alv = find_alv_shell(wnd)

if alv:
    # Leer datos
    for row in range(alv.RowCount):
        for col in range(alv.ColumnCount):
            value = alv.GetCellValue(row, col)
            print(f"[{row},{col}] = {value}")
```

## Consideraciones Técnicas

### Thread Safety

Los componentes Core **no son thread-safe**. Cada thread debe tener su propia instancia de `SAPConnection`.

### Gestión de Recursos

Las conexiones SAP deben cerrarse explícitamente:

```python
try:
    session = sap_conn.connect()
    # Usar sesión
finally:
    sap_conn.disconnect()
```

### Timeouts

Tiempos de espera configurables:

- Login: 1s antes, 2s después
- Inicio SAP Logon: 3s
- Popup seguridad: hasta 3s (6 intentos × 0.5s)

## Manejo de Errores

### Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `RuntimeError: No open connections` | SAP GUI no abierto | Iniciar SAP Logon |
| `IndexError: connection_index out of range` | Índice inválido | Verificar índices en config |
| `RuntimeError: SAP Login failed` | Credenciales incorrectas | Validar credenciales |
| `ValueError: connection_string required` | Falta connection_string | Configurar en settings.yaml |

### Logging

Todos los errores se registran con contexto completo:

```python
logger.error(f"Failed to connect with credentials: {e}")
logger.warning(f"Could not set client field: {e}")
logger.info(f"Login successful")
```

## Próximas Secciones

- [Capa Utils](utils.md): Herramientas de soporte
- [Capa Scripts](scripts.md): Crear scripts personalizados
