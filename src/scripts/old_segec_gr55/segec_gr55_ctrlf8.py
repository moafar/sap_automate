import os
import sys
import time
# Permitir imports desde cualquier ubicación
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from src.core.sap_connection import SAPConnection
from src.utils.logger import setup_logger

def load_global_config():
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../config/settings.yaml'))
    import yaml
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    logger = setup_logger()
    global_config = load_global_config()
    sap_cfg = global_config.get('sap', {})
    connection_mode = 'existing_session'
    logger.info(f"Connection mode: {connection_mode}")

    # Conectar a SAP
    try:
        sap_conn = SAPConnection(
            connection_index=sap_cfg.get('connection_index', 0),
            session_index=sap_cfg.get('session_index', 0),
            connection_mode="existing_session"
        )
        session = sap_conn.connect()
    except Exception as e:
        logger.critical(f"Could not connect to SAP: {e}")
        sys.exit(1)

    # --- INICIO DE PASOS AISLADOS DESDE LA PANTALLA ACTUAL ---
    try:
        import time
        print("Abriendo menú: Opcions > Disposició > Modificar...")
        menu_opcions = session.findById("wnd[0]/mbar/menu[3]")
        menu_opcions.select()
        time.sleep(0.3)
        menu_disposicio = session.findById("wnd[0]/mbar/menu[3]/menu[0]")
        menu_disposicio.select()
        time.sleep(0.3)
        menu_modificar = session.findById("wnd[0]/mbar/menu[3]/menu[0]/menu[0]")
        menu_modificar.select()
        print("Popup de 'Modificar disposició...' solicitado mediante menú. Esperando 1s para que cargue...")
        time.sleep(1)
        # Seleccionar el checkbox 'Nom de columna' en la sección derecha (Llista columnes)
        print("Buscando la solapa (tab) 'Selecció columna' en el popup y listando sus elementos hijos...")
        try:
            tab = session.findById("wnd[1]/usr/tabsG_TS_ALV/tabpALV_M_R1")
            print(f"Solapa encontrada: id={tab.Id}, name={tab.Name}, text={tab.Text}")
            if hasattr(tab, 'Children'):
                print(f"Elementos hijos de la solapa 'Selecció columna': {len(tab.Children)}")
                for idx, child in enumerate(tab.Children):
                    desc = f"  [{idx}] type={getattr(child, 'Type', '')}, id={getattr(child, 'Id', '')}, name={getattr(child, 'Name', '')}, text={getattr(child, 'Text', '')}"
                    print(desc)
                # Si hay un solo hijo, listar sus hijos
                if len(tab.Children) == 1:
                    unico_hijo = tab.Children[0]
                    print(f"\nListando hijos del hijo único (type={getattr(unico_hijo, 'Type', '')}, id={getattr(unico_hijo, 'Id', '')}):")
                    if hasattr(unico_hijo, 'Children'):
                        print(f"  Total hijos: {len(unico_hijo.Children)}")
                        for idx2, subchild in enumerate(unico_hijo.Children):
                            desc2 = f"    [{idx2}] type={getattr(subchild, 'Type', '')}, id={getattr(subchild, 'Id', '')}, name={getattr(subchild, 'Name', '')}, text={getattr(subchild, 'Text', '')}"
                            print(desc2)
                        # Buscar CONTAINER1_LAYO y listar sus hijos
                        container1 = next((c for c in unico_hijo.Children if getattr(c, 'Name', '') == 'CONTAINER1_LAYO'), None)
                        if container1:
                            print(f"\nListando hijos de CONTAINER1_LAYO (id={getattr(container1, 'Id', '')}):")
                            if hasattr(container1, 'Children'):
                                print(f"  Total hijos: {len(container1.Children)}")
                                for idx3, subsub in enumerate(container1.Children):
                                    desc3 = f"    [{idx3}] type={getattr(subsub, 'Type', '')}, id={getattr(subsub, 'Id', '')}, name={getattr(subsub, 'Name', '')}, text={getattr(subsub, 'Text', '')}"
                                    print(desc3)
                                # Buscar shellcont y listar sus hijos
                                shellcont = next((s for s in container1.Children if getattr(s, 'Name', '') == 'shellcont'), None)
                                if shellcont:
                                    print(f"\nListando hijos de shellcont (id={getattr(shellcont, 'Id', '')}):")
                                    if hasattr(shellcont, 'Children'):
                                        print(f"  Total hijos: {len(shellcont.Children)}")
                                        for idx4, subsub2 in enumerate(shellcont.Children):
                                            desc4 = f"    [{idx4}] type={getattr(subsub2, 'Type', '')}, id={getattr(subsub2, 'Id', '')}, name={getattr(subsub2, 'Name', '')}, text={getattr(subsub2, 'Text', '')}"
                                            print(desc4)
                                            # Si es el GuiShell (GridViewCtrl), intentar leer los títulos de los elementos
                                            if getattr(subsub2, 'Type', '') == 'GuiShell' and getattr(subsub2, 'Name', '') == 'shell':
                                                print("\nIntentando leer títulos de los elementos del GridViewCtrl:")
                                                try:
                                                    # Leer número de filas
                                                    row_count = getattr(subsub2, 'RowCount', None)
                                                    if row_count is not None:
                                                        print(f"  Total filas: {row_count}")
                                                        # Leer los textos de la primera columna de cada fila
                                                        for row in range(row_count):
                                                            try:
                                                                # El método GetCellValue suele estar disponible en GridViewCtrl
                                                                cell_value = subsub2.GetCellValue(row, 0)
                                                                print(f"    [{row}] {cell_value}")
                                                            except Exception as e:
                                                                print(f"    [{row}] <error al leer celda>: {e}")
                                                    else:
                                                        print("  No se pudo obtener RowCount del GridViewCtrl.")
                                                except Exception as e:
                                                    print(f"  Error al intentar leer títulos del GridViewCtrl: {e}")
                                    else:
                                        print("  shellcont no tiene atributo 'Children'.")
                                else:
                                    print("  No se encontró shellcont entre los hijos de CONTAINER1_LAYO.")
                            else:
                                print("  CONTAINER1_LAYO no tiene atributo 'Children'.")
                        else:
                            print("  No se encontró CONTAINER1_LAYO entre los hijos del GuiScrollContainer.")
                    else:
                        print("  El hijo único no tiene atributo 'Children'.")
            else:
                print("La solapa no tiene atributo 'Children'.")
        except Exception as e:
            print(f"No se pudo encontrar la solapa 'Selecció columna': {e}")
        input("Revisa la consola para ver el resultado y presiona Enter para finalizar la prueba...")
    except Exception as e:
        logger.error(f"Error al ejecutar menú Modificar disposició: {e}")
        print(f"Error al ejecutar menú Modificar disposició: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
