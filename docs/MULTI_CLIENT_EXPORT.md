# Script de Exportación Multi-Cliente

## Resumen

Este script exporta facturas de **múltiples clientes** aplicando los mismos filtros a todos.

## Campos Identificados

Basado en la inspección del formulario `/nZTSD_FACTURACION`, estos son los campos utilizados:

| Campo | Nombre Técnico | Tipo | Descripción |
|-------|----------------|------|-------------|
| Cliente | `S_KUNNR-LOW` | GuiCTextField | Código del cliente |
| Mes inicial | `S_MES-LOW` | GuiCTextField | Mes de inicio del periodo |
| Mes final | `S_MES-HIGH` | GuiCTextField | Mes fin del periodo |
| Año | `S_GJAHR-LOW` | GuiTextField | Año de facturación |
| Status | `S_STATUS-LOW` | GuiCTextField | Status de facturación |

## Uso

### Preparar Archivo de Clientes

Crea un archivo de texto con los códigos de clientes (uno por línea):

**Ejemplo: `config/clients.txt`**
```txt
# Clientes para exportación
CLI001
CLI002
CLI003
```

### Uso básico (valores por defecto)

```powershell
python main.py --task export_multi_client --clients-file config/clients.txt
```

**Valores por defecto:**
- Mes inicial: 1
- Mes final: 10
- Año: 2025
- Status: F

### Uso con filtros personalizados

```powershell
python main.py --task export_multi_client \
    --clients-file config/clients.txt \
    --month-from 3 \
    --month-to 6 \
    --year 2024 \
    --status A
```

### Uso con diferentes archivos de clientes

```powershell
# Clientes región A
python main.py --task export_multi_client --clients-file config/clients_region_a.txt

# Clientes región B
python main.py --task export_multi_client --clients-file config/clients_region_b.txt
```

## Archivos Generados

Los archivos se guardan en `exports/` con este formato:

```
EXPORT_CLIENT_{CODIGO_CLIENTE}_{AÑO}M{MES_DESDE}-{MES_HASTA}_{TIMESTAMP}.csv
```

Ejemplos:
- `EXPORT_CLIENT_CLI001_2025M01-10_20251128_093000.csv`
- `EXPORT_CLIENT_CLI002_2025M01-10_20251128_093015.csv`

## Proceso por Cliente

Para cada cliente, el script:

1. Navega a la transacción `/nZTSD_FACTURACION`
2. Aplica los filtros:
   - Cliente: código actual
   - Mes inicial y final
   - Año
   - Status
3. Ejecuta la búsqueda
4. Exporta los resultados a Excel/CSV
5. Cierra Excel automáticamente
6. Continúa con el siguiente cliente

## Logs

El progreso se registra en `logs/app.log` y en consola:

```
2025-11-28 09:00:00 - SAP_Automation - INFO - Starting multi-client export for 3 clients
2025-11-28 09:00:00 - SAP_Automation - INFO - Filters: Month=1-10, Year=2025, Status=F
2025-11-28 09:00:00 - SAP_Automation - INFO - [1/3] Processing client: CLI001
2025-11-28 09:00:15 - SAP_Automation - INFO - ✓ Client CLI001 exported successfully
2025-11-28 09:00:15 - SAP_Automation - INFO - [2/3] Processing client: CLI002
...
2025-11-28 09:00:45 - SAP_Automation - INFO - ============================================================
2025-11-28 09:00:45 - SAP_Automation - INFO - EXPORT SUMMARY: Success=3, Failed=0, Total=3
2025-11-28 09:00:45 - SAP_Automation - INFO - ============================================================
```

## Manejo de Errores

- Si un cliente no tiene datos: se registra warning y continúa con el siguiente
- Si falla la exportación de un cliente: se registra error y continúa con el siguiente
- Al final se muestra un resumen de éxitos y fallos

## Catálogo de Campos Completo

El archivo `config/field_mappings.yaml` contiene el mapeo completo de **104 campos** del formulario para uso futuro.

Algunos campos adicionales disponibles (no utilizados en este script):
- `S_HOSP-LOW`: Hospital
- `S_ENTIT-LOW`: Entidad solicitante
- `S_NUM_F-LOW`: Número de factura
- `S_PRE_F-LOW`: Número de prefactura
- `S_MATNR-LOW`: Código de concepto facturable
- etc.
