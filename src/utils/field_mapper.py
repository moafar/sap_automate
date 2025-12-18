"""
SAP Filter Field Mapper
========================
Herramienta para mapear todos los campos de filtros de una transacción SAP.

Uso:
    python -m src.utils.field_mapper --transaction /nZTSD_FACTURACION
"""

import yaml
import argparse
import logging
import os
from datetime import datetime
from src.core.sap_connection import SAPConnection
from src.utils.logger import setup_logger

logger = logging.getLogger("SAP_Automation")


def is_filter_field(component) -> bool:
    """
    Detecta si un componente es un campo de filtro (input field).
    
    Args:
        component: Componente SAP GUI
        
    Returns:
        True si es un campo de filtro, False en caso contrario
    """
    try:
        comp_type = getattr(component, "Type", "")
        return comp_type in (
            "GuiTextField", 
            "GuiCTextField", 
            "GuiComboBox",
            "GuiCheckBox"
        )
    except Exception:
        return False


def iter_children(component):
    """
    Iterador seguro sobre los hijos de un componente.
    
    Args:
        component: Componente SAP GUI
        
    Yields:
        Componentes hijos
    """
    try:
        count = component.Children.Count
    except Exception:
        return
    for i in range(count):
        try:
            yield component.Children(i)
        except Exception:
            continue


def extract_field_info(component) -> dict:
    """
    Extrae información de un campo de filtro.
    
    Args:
        component: Componente SAP GUI
        
    Returns:
        Diccionario con información del campo
    """
    try:
        return {
            "id": getattr(component, "Id", None),
            "name": getattr(component, "Name", None),
            "type": getattr(component, "Type", None),
            "text": getattr(component, "Text", None),
            "tooltip": getattr(component, "Tooltip", None),
            "changeable": getattr(component, "Changeable", None),
        }
    except Exception as e:
        logger.warning(f"Error extracting field info: {e}")
        return {}


def scan_fields(component, fields_dict: dict, depth: int = 0, max_depth: int = 15):
    """
    Escanea recursivamente todos los campos de filtro en la ventana.
    
    Args:
        component: Componente raíz
        fields_dict: Diccionario donde almacenar los campos encontrados
        depth: Profundidad actual
        max_depth: Profundidad máxima de búsqueda
    """
    if depth > max_depth:
        return
    
    if is_filter_field(component):
        field_info = extract_field_info(component)
        if field_info.get("id"):
            # Usar el ID como clave única
            field_id = field_info["id"]
            
            # Intentar extraer el nombre técnico del ID
            # Ejemplo: "wnd[0]/usr/txtS_NUM_F-LOW" -> "S_NUM_F-LOW"
            technical_name = None
            if "/" in field_id:
                parts = field_id.split("/")
                last_part = parts[-1]
                # Remover prefijos como "txt", "cmb", "chk"
                for prefix in ["txt", "cmb", "chk", "ctxt"]:
                    if last_part.startswith(prefix):
                        technical_name = last_part[len(prefix):]
                        break
                if not technical_name:
                    technical_name = last_part
            
            field_info["technical_name"] = technical_name
            fields_dict[field_id] = field_info
            logger.info(f"Found field: {field_id} | {technical_name}")
    
    # Recursión en hijos
    for child in iter_children(component):
        scan_fields(child, fields_dict, depth + 1, max_depth)


def map_transaction_fields(session, transaction_code: str) -> dict:
    """
    Mapea todos los campos de filtro de una transacción.
    
    Args:
        session: Sesión SAP GUI activa
        transaction_code: Código de transacción (ej: "/nZTSD_FACTURACION")
        
    Returns:
        Diccionario con los campos encontrados
    """
    logger.info(f"Navigating to transaction: {transaction_code}")
    
    # Navegar a la transacción
    session.findById("wnd[0]/tbar[0]/okcd").Text = transaction_code
    session.findById("wnd[0]").sendVKey(0)
    
    logger.info("Scanning for filter fields...")
    
    # Escanear la ventana principal
    wnd0 = session.findById("wnd[0]")
    fields = {}
    scan_fields(wnd0, fields)
    
    logger.info(f"Total fields found: {len(fields)}")
    return fields


def save_field_mapping(fields: dict, output_file: str):
    """
    Guarda el mapeo de campos en un archivo YAML.
    
    Args:
        fields: Diccionario con los campos
        output_file: Ruta del archivo de salida
    """
    # Organizar por nombre técnico para mejor legibilidad
    organized_mapping = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_fields": len(fields)
        },
        "fields": {}
    }
    
    for field_id, field_info in fields.items():
        tech_name = field_info.get("technical_name", "unknown")
        organized_mapping["fields"][tech_name] = {
            "id": field_id,
            "type": field_info.get("type"),
            "text": field_info.get("text"),
            "tooltip": field_info.get("tooltip"),
            "changeable": field_info.get("changeable")
        }
    
    # Guardar en YAML
    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(organized_mapping, f, allow_unicode=True, default_flow_style=False, sort_keys=True)
    
    logger.info(f"Field mapping saved to: {output_file}")


def main():
    """Función principal para ejecutar como script standalone."""
    parser = argparse.ArgumentParser(
        description="SAP Filter Field Mapper",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--transaction", "-t", type=str, default="/nZTSD_FACTURACION",
                        help="Transaction code to map (default: /nZTSD_FACTURACION)")
    parser.add_argument("--output", "-o", type=str, default="config/field_mappings.yaml",
                        help="Output file for field mappings (default: config/field_mappings.yaml)")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logger()
    
    try:
        # Conectar a SAP
        logger.info("Connecting to SAP...")
        sap_conn = SAPConnection()
        session = sap_conn.connect()
        
        # Mapear campos
        fields = map_transaction_fields(session, args.transaction)
        
        # Guardar resultado
        save_field_mapping(fields, args.output)
        
        logger.info("Field mapping completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during field mapping: {e}")
        raise


if __name__ == "__main__":
    main()
