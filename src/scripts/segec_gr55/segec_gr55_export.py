"""
segec_gr55_export.py — Procesamiento post-transacción GR55.

Script independiente que se conecta a una sesión SAP ya posicionada
en la pantalla de detalle de centres de cost (tras ejecutar segec_gr55.py)
y realiza las operaciones de exportación/procesamiento.

Uso:
    python src/scripts/segec_gr55/segec_gr55_export.py

Requisitos:
    - SAP GUI abierto en la pantalla de detalle de centres de cost
      (resultado de ejecutar segec_gr55 hasta el paso 5)
"""
import os
import sys
import time
import logging

# Permitir imports desde cualquier ubicación
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.core.sap_connection import SAPConnection
from src.utils.logger import setup_logger


logger = logging.getLogger("SAP_Automation")


class SegecGR55Export:
    """
    Procesamiento de la pantalla de detalle de centres de cost (post-GR55).
    Asume que SAP ya está en la pantalla de detalle.
    """

    def __init__(self, session, global_config):
        self.session = session
        self.global_config = global_config
        self.timeout = global_config.get('timeouts', {}).get('default_wait', 0.5)
        # Cargar config específica del script
        script_config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
        import yaml
        with open(script_config_path, 'r', encoding='utf-8') as f:
            self.script_config = yaml.safe_load(f)
        self.export_config = self.script_config.get('export', {})

    def run(self) -> bool:
        """Ejecuta el procesamiento sobre la pantalla de detalle actual."""
        logger.info("Iniciando procesamiento post-GR55 (export)")

        try:
            self._abrir_modificar_disposicio()
            self._seleccionar_todas_columnas()
            self._mostrar_camps_seleccionats()
            logger.info("Columnas movidas a 'Columnes visualitzades'.")
            self._limpiar_sigma()
            self._transferir()
            self._exportar_excel()
            return True
        except Exception as e:
            logger.error(f"Error en procesamiento post-GR55: {e}")
            return False

    # ── Paso 6: Abrir popup "Modificar disposició" (Ctrl+F8) ──

    def _abrir_modificar_disposicio(self):
        """Navega por menú Opcions > Disposició > Modificar para abrir el popup."""
        logger.info("Abriendo menú: Opcions > Disposició > Modificar...")

        # Opcions (menu[3])
        self.session.findById("wnd[0]/mbar/menu[3]").select()
        time.sleep(0.3)

        # Disposició (menu[3]/menu[0])
        self.session.findById("wnd[0]/mbar/menu[3]/menu[0]").select()
        time.sleep(0.3)

        # Modificar (menu[3]/menu[0]/menu[0])
        self.session.findById("wnd[0]/mbar/menu[3]/menu[0]/menu[0]").select()
        time.sleep(1)

        # Verificar que el popup se abrió
        try:
            popup = self.session.findById("wnd[1]")
            title = getattr(popup, 'Text', '')
            logger.info(f"Popup detectado: '{title}'")
        except Exception:
            raise RuntimeError("No se detectó el popup 'Modificar disposició' tras abrir el menú")

    # ── Paso 7: Seleccionar todas las columnas en "Llista columnes" ──

    _TAB_SELECCIO = "wnd[1]/usr/tabsG_TS_ALV/tabpALV_M_R1"
    _GRID_LLISTA = (
        "wnd[1]/usr/tabsG_TS_ALV/tabpALV_M_R1/"
        "ssubSUB_CONFIGURATION:SAPLSALV_CUL_COLUMN_SELECTION:0620/"
        "cntlCONTAINER1_LAYO/shellcont/shell"
    )

    def _seleccionar_todas_columnas(self):
        """Selecciona todas las filas del grid derecho (Llista columnes) en la solapa 'Selecció columna'."""
        # Asegurar que estamos en la solapa correcta
        tab = self.session.findById(self._TAB_SELECCIO)
        tab.select()
        time.sleep(0.3)

        # Localizar el grid derecho (Llista columnes)
        grid = self.session.findById(self._GRID_LLISTA)
        row_count = grid.RowCount
        logger.info(f"Grid 'Llista columnes' encontrado: {row_count} columnas disponibles")

        # Seleccionar todas las filas
        all_rows = ",".join(str(i) for i in range(row_count))
        grid.SelectedRows = all_rows
        time.sleep(0.3)

        logger.info(f"Seleccionadas {row_count} filas en 'Llista columnes'")

    # ── Paso 8: Mostrar camps seleccionats (F7) ──

    _BTN_MOSTRAR = (
        "wnd[1]/usr/tabsG_TS_ALV/tabpALV_M_R1/"
        "ssubSUB_CONFIGURATION:SAPLSALV_CUL_COLUMN_SELECTION:0620/"
        "btnAPP_WL_SING"
    )

    def _mostrar_camps_seleccionats(self):
        """Pulsa el botón '>' (Mostrar camps selec. / F7) para mover columnas a visualitzades."""
        logger.debug("Pulsando botón 'Mostrar camps selec. (F7)'")
        self.session.findById(self._BTN_MOSTRAR).press()
        time.sleep(0.5)
        logger.info("Botón 'Mostrar camps selec.' pulsado")

    # ── Paso 9: Limpiar valores "Total (Σ)" en bloque izquierdo ──

    _GRID_VISUALITZADES = (
        "wnd[1]/usr/tabsG_TS_ALV/tabpALV_M_R1/"
        "ssubSUB_CONFIGURATION:SAPLSALV_CUL_COLUMN_SELECTION:0620/"
        "cntlCONTAINER2_LAYO/shellcont/shell"
    )

    def _limpiar_sigma(self):
        """Busca la columna Sigma en el grid izquierdo y limpia las celdas con 'Total (Σ)'."""
        grid = self.session.findById(self._GRID_VISUALITZADES)
        row_count = grid.RowCount
        cols = grid.ColumnOrder
        col_names = [cols(i) for i in range(cols.Count)]
        logger.info(f"Grid izquierdo: {row_count} filas, columnas: {col_names}")

        # Identificar la columna que contiene los valores de sigma/total
        sigma_col = None
        for col in col_names:
            for row in range(min(row_count, 20)):
                val = grid.GetCellValue(row, col)
                if "Σ" in str(val) or "Total" in str(val):
                    sigma_col = col
                    break
            if sigma_col:
                break

        if not sigma_col:
            logger.warning("No se encontró columna con valores 'Total (Σ)' — nada que limpiar.")
            return

        logger.info(f"Columna sigma identificada: '{sigma_col}'")

        cleared = 0
        for row in range(row_count):
            val = str(grid.GetCellValue(row, sigma_col))
            if val and val.strip():
                logger.debug(f"  Fila {row}: '{val}' → vacío")
                grid.ModifyCell(row, sigma_col, "")
                time.sleep(0.2)
                cleared += 1

        logger.info(f"Limpiados {cleared} valores sigma en columna '{sigma_col}'.")

    # ── Paso 10: Transferir (Enter) ──

    def _transferir(self):
        """Pulsa 'Transferir (Enter)' para confirmar la disposición y cerrar el popup."""
        logger.info("Pulsando 'Transferir (Enter)' en popup...")
        self.session.findById("wnd[1]/tbar[0]/btn[0]").press()
        time.sleep(1)
        logger.info("Disposición transferida. Popup cerrado.")

    # ── Paso 11: Exportar a Excel (Ctrl+Shift+F7) ──

    _POPUP_EXPORT_BASE = (
        "wnd[1]/usr/ssubSUB_CONFIGURATION:SAPLSALV_GUI_CUL_EXPORT_AS:0512"
    )

    def _exportar_excel(self):
        """Llista > Exportar > Full de càlcul... y rellenar popup de exportación."""
        logger.info("Menú: Llista > Exportar > Full de càlcul...")
        self.session.findById("wnd[0]/mbar/menu[0]/menu[3]/menu[1]").select()
        time.sleep(1)

        # Rellenar nombre del fichero
        from datetime import datetime
        prefix = self.export_config.get('filename_prefix', 'SEGEC_GR55')
        filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        txt_filename = self.session.findById(f"{self._POPUP_EXPORT_BASE}/txtGS_EXPORT-FILE_NAME")
        txt_filename.Text = filename
        logger.info(f"Nom fitxer: {filename}")

        # Listar entries de los combos para diagnóstico
        cmb_format = self.session.findById(f"{self._POPUP_EXPORT_BASE}/cmbGS_EXPORT-FORMAT")
        cmb_dest = self.session.findById(f"{self._POPUP_EXPORT_BASE}/cmbGS_EXPORT-DESTINATION")

        fmt_entries = {cmb_format.Entries(i).Key.strip(): cmb_format.Entries(i).Value.strip()
                       for i in range(cmb_format.Entries.Count)}
        dest_entries = {cmb_dest.Entries(i).Key.strip(): cmb_dest.Entries(i).Value.strip()
                        for i in range(cmb_dest.Entries.Count)}
        logger.info(f"Format entries: {fmt_entries}")
        logger.info(f"Destination entries: {dest_entries}")

        # Seleccionar formato
        fmt = str(self.export_config.get('format', 'csv-LEAN-STANDARD'))
        if fmt not in fmt_entries:
            logger.warning(f"Key format '{fmt}' no encontrado. Keys disponibles: {list(fmt_entries.keys())}")
            raise RuntimeError(f"Key de formato '{fmt}' no válido. Opciones: {fmt_entries}")
        current_fmt = cmb_format.Key.strip()
        if current_fmt != fmt:
            cmb_format.Key = fmt
        logger.info(f"Format seleccionado: {fmt} = {fmt_entries[fmt]}")
        time.sleep(0.5)

        # Seleccionar destino (solo si difiere del actual)
        dest = str(self.export_config.get('destination', 'L'))
        if dest not in dest_entries:
            logger.warning(f"Key destino '{dest}' no encontrado. Keys disponibles: {list(dest_entries.keys())}")
            raise RuntimeError(f"Key de destino '{dest}' no válido. Opciones: {dest_entries}")
        current_dest = cmb_dest.Key.strip()
        if current_dest != dest:
            cmb_dest.Key = dest
        logger.info(f"Destinació: {dest} = {dest_entries[dest]}")

        time.sleep(0.3)

        # Pulsar "Exportar a..."
        self.session.findById("wnd[1]/tbar[0]/btn[20]").press()
        time.sleep(3)
        logger.info("Botón 'Exportar a...' pulsado.")

        self._guardar_fitxer(filename)

    # ── Paso 12: Guardar fitxer (popup "Emmagatzemar fitxer") ──

    def _guardar_fitxer(self, filename):
        """Rellena el popup de guardado con directorio y nombre, y pulsa Substituir."""
        popup = self.session.findById("wnd[1]")
        title = getattr(popup, 'Text', '')
        logger.info(f"Popup guardado detectado: '{title}'")

        # Directorio
        directory = self.export_config.get('directory', 'C:\\TEMP')
        self.session.findById("wnd[1]/usr/ctxtDY_PATH").Text = directory
        logger.info(f"Directori: {directory}")

        # Nombre del fichero
        fmt = str(self.export_config.get('format', 'csv-LEAN-STANDARD'))
        ext = 'csv' if 'csv' in fmt.lower() else 'xlsx'
        full_filename = f"{filename}.{ext}"
        self.session.findById("wnd[1]/usr/ctxtDY_FILENAME").Text = full_filename
        logger.info(f"NomFitxer: {full_filename}")

        time.sleep(0.3)

        # Pulsar "Substituir" para guardar (sobreescribir si existe)
        self.session.findById("wnd[1]/tbar[0]/btn[11]").press()
        time.sleep(2)
        logger.info(f"Fitxer guardat: {directory}\\{full_filename}")


def load_global_config():
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../config/settings.yaml'))
    with open(config_path, 'r', encoding='utf-8') as f:
        import yaml
        return yaml.safe_load(f)


def main():
    logger = setup_logger()
    global_config = load_global_config()

    sap_cfg = global_config.get('sap', {})
    logger.info("Conectando a sesión SAP existente (pantalla de detalle GR55)...")

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

    export = SegecGR55Export(session, global_config)
    success = export.run()

    if success:
        logger.info("Procesamiento post-GR55 completado.")
    else:
        logger.error("Error en procesamiento post-GR55.")
        sys.exit(1)


if __name__ == "__main__":
    main()
