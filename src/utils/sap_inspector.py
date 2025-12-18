"""
SAP GUI Inspector Tool
======================
Herramienta para explorar la estructura de la interfaz SAP GUI durante el desarrollo.

Uso como script standalone:
    python -m src.utils.sap_inspector [--output FILE] [--window-id ID]

Uso como módulo:
    from src.utils.sap_inspector import inspect_window, export_structure
"""

import win32com.client
import json
import sys
import argparse
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger("SAP_Inspector")


def get_session(connection_index: int = 0, session_index: int = 0):
    """
    Conecta a una sesión SAP GUI concreta.
    
    Args:
        connection_index: Índice de la conexión SAP (default: 0)
        session_index: Índice de la sesión (default: 0)
        
    Returns:
        Sesión SAP GUI
        
    Raises:
        RuntimeError: Si no hay conexiones o sesiones abiertas
        IndexError: Si los índices están fuera de rango
    """
    sap_gui_auto = win32com.client.GetObject("SAPGUI")
    app = sap_gui_auto.GetScriptingEngine

    if app.Children.Count == 0:
        raise RuntimeError("No hay conexiones abiertas en SAP Logon.")

    if connection_index >= app.Children.Count:
        raise IndexError(f"connection_index fuera de rango (max {app.Children.Count - 1})")

    connection = app.Children(connection_index)

    if connection.Children.Count == 0:
        raise RuntimeError("La conexión seleccionada no tiene sesiones abiertas.")

    if session_index >= connection.Children.Count:
        raise IndexError(f"session_index fuera de rango (max {connection.Children.Count - 1})")

    return connection.Children(session_index)


def is_alv(component) -> bool:
    """
    Detecta si un componente es un ALV Grid.
    
    Args:
        component: Componente SAP GUI a verificar
        
    Returns:
        True si es un componente ALV, False en caso contrario
    """
    try:
        comp_type = getattr(component, "Type", "")
        comp_id = getattr(component, "Id", "")
        comp_name = getattr(component, "Name", "")

        text = f"{comp_type} {comp_id} {comp_name}".upper()
        
        # Detección por tipo
        if comp_type in ("GuiALVGrid", "GuiALVTree"):
            return True
            
        # Detección por nombre/id
        if "ALV" in text:
            return True
            
        # Detección por métodos característicos del ALV
        if comp_type == "GuiShell" and hasattr(component, "GetCellValue"):
            return True
            
        return False
    except Exception:
        return False


def is_button(component) -> bool:
    """Detecta si un componente es un botón."""
    try:
        return getattr(component, "Type", "") == "GuiButton"
    except Exception:
        return False


def is_textfield(component) -> bool:
    """Detecta si un componente es un campo de texto."""
    try:
        comp_type = getattr(component, "Type", "")
        return comp_type in ("GuiTextField", "GuiCTextField")
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


def get_component_info(component) -> Dict[str, Any]:
    """
    Extrae información detallada de un componente.
    
    Args:
        component: Componente SAP GUI
        
    Returns:
        Diccionario con información del componente
    """
    info = {}
    
    # Propiedades básicas
    for prop in ["Type", "Id", "Name", "Text", "Tooltip", "Changeable", "Modified"]:
        try:
            info[prop] = getattr(component, prop, None)
        except Exception:
            info[prop] = None
    
    # Clasificación
    info["is_alv"] = is_alv(component)
    info["is_button"] = is_button(component)
    info["is_textfield"] = is_textfield(component)
    
    # Información adicional para ALV
    if info["is_alv"]:
        try:
            info["RowCount"] = getattr(component, "RowCount", None)
            info["ColumnCount"] = getattr(component, "ColumnCount", None)
        except Exception:
            pass
    
    return info


def dump_tree(component, depth: int = 0, max_depth: Optional[int] = None) -> None:
    """
    Imprime el árbol de controles con marcas especiales.
    
    Args:
        component: Componente raíz
        depth: Profundidad actual (para indentación)
        max_depth: Profundidad máxima (None = sin límite)
    """
    if max_depth is not None and depth > max_depth:
        return
        
    indent = "  " * depth
    info = get_component_info(component)
    
    # Construir etiquetas
    tags = []
    if info["is_alv"]:
        tags.append("[ALV]")
    if info["is_button"]:
        tags.append("[BTN]")
    if info["is_textfield"]:
        tags.append("[TXT]")
    
    tags_str = " ".join(tags)
    
    # Construir línea de salida
    comp_type = info["Type"] or type(component).__name__
    comp_id = info["Id"] or "(sin Id)"
    comp_name = info["Name"] or ""
    comp_text = info["Text"] or ""
    
    output = f"{indent}{comp_type} | {comp_name} | {comp_id}"
    if tags_str:
        output += f" {tags_str}"
    if comp_text:
        output += f" [Text: {comp_text[:30]}...]" if len(comp_text) > 30 else f" [Text: {comp_text}]"
    
    print(output)

    for child in iter_children(component):
        dump_tree(child, depth + 1, max_depth)


def build_tree_structure(component, depth: int = 0, max_depth: Optional[int] = None) -> Dict[str, Any]:
    """
    Construye una estructura de árbol en formato diccionario (para exportar a JSON).
    
    Args:
        component: Componente raíz
        depth: Profundidad actual
        max_depth: Profundidad máxima (None = sin límite)
        
    Returns:
        Diccionario con la estructura del árbol
    """
    if max_depth is not None and depth > max_depth:
        return {}
    
    info = get_component_info(component)
    
    structure = {
        "type": info["Type"],
        "id": info["Id"],
        "name": info["Name"],
        "text": info["Text"],
        "is_alv": info["is_alv"],
        "is_button": info["is_button"],
        "is_textfield": info["is_textfield"],
        "children": []
    }
    
    # Agregar info adicional para ALV
    if info["is_alv"]:
        structure["row_count"] = info.get("RowCount")
        structure["column_count"] = info.get("ColumnCount")
    
    # Recursión en hijos
    for child in iter_children(component):
        child_structure = build_tree_structure(child, depth + 1, max_depth)
        if child_structure:
            structure["children"].append(child_structure)
    
    return structure


def inspect_window(session, window_id: str = "wnd[0]", max_depth: Optional[int] = None) -> Dict[str, Any]:
    """
    Inspecciona una ventana SAP y retorna su estructura.
    
    Args:
        session: Sesión SAP GUI activa
        window_id: ID de la ventana a inspeccionar (default: "wnd[0]")
        max_depth: Profundidad máxima a explorar
        
    Returns:
        Diccionario con la estructura de la ventana
    """
    root = session.findById(window_id)
    return build_tree_structure(root, max_depth=max_depth)


def export_structure(structure: Dict[str, Any], output_file: str, format: str = "json") -> None:
    """
    Exporta la estructura a un archivo.
    
    Args:
        structure: Estructura del árbol
        output_file: Ruta del archivo de salida
        format: Formato de salida ("json" o "txt")
    """
    if format == "json":
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(structure, f, indent=2, ensure_ascii=False)
        print(f"Estructura exportada a: {output_file}")
    elif format == "txt":
        with open(output_file, "w", encoding="utf-8") as f:
            _write_tree_text(structure, f, depth=0)
        print(f"Estructura exportada a: {output_file}")
    else:
        raise ValueError(f"Formato no soportado: {format}")


def _write_tree_text(node: Dict[str, Any], file, depth: int = 0) -> None:
    """Escribe el árbol en formato texto (helper para export_structure)."""
    indent = "  " * depth
    
    # Construir etiquetas
    tags = []
    if node.get("is_alv"):
        tags.append("[ALV]")
    if node.get("is_button"):
        tags.append("[BTN]")
    if node.get("is_textfield"):
        tags.append("[TXT]")
    
    tags_str = " ".join(tags)
    
    # Escribir línea
    line = f"{indent}{node['type']} | {node['name']} | {node['id']}"
    if tags_str:
        line += f" {tags_str}"
    if node.get("text"):
        line += f" [Text: {node['text']}]"
    
    file.write(line + "\n")
    
    # Recursión en hijos
    for child in node.get("children", []):
        _write_tree_text(child, file, depth + 1)


def main():
    """Función principal para ejecutar como script standalone."""
    parser = argparse.ArgumentParser(
        description="Inspector de interfaz SAP GUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python -m src.utils.sap_inspector
  python -m src.utils.sap_inspector --output structure.json
  python -m src.utils.sap_inspector --output structure.txt --format txt
  python -m src.utils.sap_inspector --window-id "wnd[1]" --max-depth 5
        """
    )
    parser.add_argument("--output", "-o", type=str, help="Archivo de salida para exportar la estructura")
    parser.add_argument("--format", "-f", type=str, choices=["json", "txt"], default="json", 
                        help="Formato de exportación (default: json)")
    parser.add_argument("--window-id", "-w", type=str, default="wnd[0]", 
                        help="ID de ventana a inspeccionar (default: wnd[0])")
    parser.add_argument("--max-depth", "-d", type=int, help="Profundidad máxima del árbol")
    
    args = parser.parse_args()
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    try:
        # Conectar a SAP
        session = get_session()
        logger.info(f"Conectado a: {session.Info.SystemName} Mandante: {session.Info.Client}")
        
        # Inspeccionar ventana
        logger.info(f"Inspeccionando ventana: {args.window_id}")
        root = session.findById(args.window_id)
        
        # Imprimir árbol en consola
        print("\n" + "="*80)
        print(f"ESTRUCTURA DE {args.window_id}")
        print("="*80 + "\n")
        dump_tree(root, max_depth=args.max_depth)
        print("\n" + "="*80 + "\n")
        
        # Exportar si se especificó archivo de salida
        if args.output:
            structure = build_tree_structure(root, max_depth=args.max_depth)
            export_structure(structure, args.output, format=args.format)
        
    except Exception as e:
        logger.error(f"Error durante la inspección: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
