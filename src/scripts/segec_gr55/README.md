# SEGEC GR55 — Seguimiento Económico

Script de automatización SAP para la transacción GR55 (Seguimiento Económico por Centres de Cost).

## Pruebas

### Requisitos previos

1. **SAP GUI** abierto con una sesión activa
2. **SAP Scripting** habilitado
3. **Entorno virtual** activado:
   ```powershell
   cd C:\Users\Z1081401\Desktop\sap_automate
   .\.venv\Scripts\Activate.ps1
   ```
4. `config/settings.yaml` con `connection_mode: "existing_session"`

### Ejecución

```powershell
python main.py --task segec_gr55
```

O directamente:

```powershell
python src/scripts/segec_gr55/segec_gr55_main.py
```

### Qué esperar

1. SAP navega a la transacción GR55
2. Se rellena "Grup d'informes" = `Z002`
3. F8 → pantalla de selección
4. Se rellenan los filtros (Societat CO, Exercici, Períodes, Grup classes cost)
5. F8 → pantalla de resultados (resumen)
6. Doble clic en "* Centres de cost" → **espera hasta 10 min** con verificaciones cada 10s
7. Se carga la pantalla de detalle

> **Nota:** El paso 6 puede tardar varios minutos. El log muestra progreso cada 10 segundos. Si en 10 minutos no carga, el script aborta con `TimeoutError`.

### Verificación

- La pantalla final de SAP debe mostrar el detalle de centres de cost
- El log debe terminar con:
  ```
  INFO - Detalle de centres de cost cargado correctamente.
  INFO - Transacción GR55 lanzada correctamente (Seguimiento Económico)
  ```

### Configuración de filtros

Editar `src/scripts/segec_gr55/config.yaml`:

```yaml
segec_gr55:
  sociedad_co: IDI
  ejercicio: 2025
  periodo_de: 12
  periodo_fins: 12
  grupo_clases_costo: co-7
```

| Parámetro | Campo SAP | ID SAP | Valor actual |
|-----------|-----------|--------|--------------|
| `sociedad_co` | Societat CO | `ctxt$1KOKRE` | `IDI` |
| `ejercicio` | Exercici | `txt$1GJAHLJ` | `2025` |
| `periodo_de` | Període de | `ctxt$0FRPMAF` | `12` |
| `periodo_fins` | Període fins | `ctxt$0FRPMAT` | `12` |
| `grupo_clases_costo` | Grup de classes de cost | `ctxt$1KSTAR` | `co-7` |

## Arquitectura

```
src/scripts/segec_gr55/
├── __init__.py              # Re-exporta SegecGR55
├── config.yaml              # Configuración local del script
├── segec_gr55.py            # Clase principal con lógica de automatización
├── segec_gr55_main.py       # Entry point independiente (existing_session)
└── README.md                # Este archivo
```

### Clase `SegecGR55`

El flujo se ejecuta en métodos privados secuenciales:

| Paso | Método | Descripción |
|------|--------|-------------|
| 1 | `_lanzar_transaccion()` | Ejecuta `/nGR55`, rellena Grup d'informes = `Z002` |
| 2 | `_avanzar_a_seleccion()` | F8 → pantalla de selección |
| 3 | `_rellenar_filtros()` | Diligencia los 5 campos desde `config.yaml` |
| 4 | `_ejecutar_busqueda()` | F8 → pantalla de resultados |
| 5 | `_navegar_detalle_centres()` | Doble clic en "* Centres de cost" + espera con polling |

### Modos de conexión

- **`existing_session`** (actual): Requiere SAP GUI abierto manualmente
- **`credentials`** (pendiente): Login automático — se implementará en fase posterior

### Entry points

- **Vía `main.py`**: `python main.py --task segec_gr55` — usa `config/settings.yaml` para la conexión
- **Directo**: `python src/scripts/segec_gr55/segec_gr55_main.py` — fuerza `existing_session`, carga su propio `config.yaml`

## Desarrollo

### Estado actual

- [x] Scaffold y estructura de carpetas
- [x] Paso 1: Lanzar transacción GR55 + campo Z002
- [x] Paso 2: Avanzar a pantalla de selección (F8)
- [x] Paso 3: Rellenar filtros desde config.yaml
- [x] Paso 4: Ejecutar búsqueda (F8)
- [x] Paso 5: Navegar a detalle centres de cost (doble clic + espera 10 min)
- [ ] Paso 6: Exportar resultados del detalle
- [ ] Migrar a modo `credentials`
- [ ] Documentación en `docs/`

### Código legacy

El directorio `src/scripts/old_segec_gr55/` contiene la versión exploratoria original con `input()` bloqueantes, `print()` de debug y exploraciones JSON de las pantallas. Se usa como referencia para los IDs de los elementos SAP.
