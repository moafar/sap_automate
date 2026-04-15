"""
segec_gr55_full.py — Script unificado SEGEC GR55.

Automatización completa de la transacción GR55 en SAP:
  1. Login con credenciales
  2. Lanzar transacción /nGR55
  3. Rellenar grupo de informes Z002
  4. Rellenar filtros de selección
  5. Ejecutar búsqueda (F8)
  6. Navegar a detalle "Centres de cost"
  7. Modificar disposición (todas las columnas, limpiar sigma)
  8. Exportar a CSV

Uso:
    python src/scripts/segec_gr55/segec_gr55_full.py

    O vía main.py:
    python main.py --task segec_gr55
"""
import os
import sys
import time
import logging
import yaml
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.core.sap_connection import SAPConnection
from src.utils.logger import setup_logger

logger = logging.getLogger("SAP_Automation")

SCRIPT_DIR = os.path.dirname(__file__)


class SegecGR55Full:
    """
    Automatización completa de la transacción GR55 (Seguimiento Económico).
    Combina lanzamiento de transacción + export en un solo flujo.
    """

    def __init__(self, session, global_config):
        self.session = session
        self.global_config = global_config
        self.timeout = global_config.get('timeouts', {}).get('default_wait', 0.5)
        self._load_script_config()

    def _load_script_config(self):
        config_path = os.path.join(SCRIPT_DIR, 'config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.script_config = yaml.safe_load(f)
        self.segec_cfg = self.script_config.get('segec_gr55', {})
        self.export_config = self.script_config.get('export', {})

    def run(self) -> bool:
        """Ejecuta el flujo completo: transacción + disposición + export."""
        logger.info("=== SEGEC GR55 - Inicio flujo completo ===")
        logger.info(f"Config transacción: {self.segec_cfg}")
        logger.info(f"Config export: {self.export_config}")

        try:
            # Fase 1: Transacción
            self._lanzar_transaccion()
            self._avanzar_a_seleccion()
            self._rellenar_filtros()
            self._ejecutar_busqueda()
            self._navegar_detalle_centres()
            logger.info("-- Fase 1 completada: detalle de centres de cost cargado --")

            # Fase 2: Disposición
            self._abrir_modificar_disposicio()
            self._seleccionar_todas_columnas()
            self._mostrar_camps_seleccionats()
            self._limpiar_sigma()
            self._transferir()
            logger.info("-- Fase 2 completada: disposicion configurada --")

            # Fase 3: Export
            self._exportar_excel()
            logger.info("=== SEGEC GR55 - Flujo completo finalizado ===")
            return True

        except Exception as e:
            logger.error(f"Error en SEGEC GR55: {e}")
            return False

    # ══════════════════════════════════════════════════════════════
    # FASE 1: Transacción GR55
    # ══════════════════════════════════════════════════════════════

    def _lanzar_transaccion(self):
        """Lanza /nGR55 y rellena el campo 'Grup d'informes' con Z002."""
        logger.debug("Ejecutando transacción /nGR55")
        self.session.findById("wnd[0]/tbar[0]/okcd").Text = "/nGR55"
        self.session.findById("wnd[0]").sendVKey(0)
        time.sleep(self.timeout)

        campo_grup = self.session.findById("wnd[0]/usr/ctxtRGRWJ-JOB")
        campo_grup.Text = "Z002"
        logger.info("Campo 'Grup d'informes' = Z002")

    def _avanzar_a_seleccion(self):
        """Pulsa F8 para avanzar a la pantalla de selección."""
        logger.debug("Pulsando F8 para avanzar a pantalla de selección")
        self.session.findById("wnd[0]").sendVKey(8)
        time.sleep(self.timeout)
        logger.info("F8 ejecutado — pantalla de selección cargada")

    def _rellenar_filtros(self):
        """Rellena los campos de filtro con valores del config.yaml."""
        cfg = self.segec_cfg

        campo = self.session.findById("wnd[0]/usr/ctxt$1KOKRE")
        campo.setFocus()
        campo.Text = str(cfg.get('sociedad_co', ''))
        logger.info(f"Societat CO = {campo.Text}")

        campo = self.session.findById("wnd[0]/usr/txt$1GJAHLJ")
        campo.setFocus()
        campo.Text = str(cfg.get('ejercicio', ''))
        logger.info(f"Exercici = {campo.Text}")

        campo = self.session.findById("wnd[0]/usr/ctxt$0FRPMAF")
        campo.setFocus()
        campo.Text = str(cfg.get('periodo_de', ''))
        logger.info(f"Període de = {campo.Text}")

        campo = self.session.findById("wnd[0]/usr/ctxt$0FRPMAT")
        campo.setFocus()
        campo.Text = str(cfg.get('periodo_fins', ''))
        logger.info(f"Període fins = {campo.Text}")

        campo = self.session.findById("wnd[0]/usr/ctxt$1KSTAR")
        campo.setFocus()
        campo.Text = str(cfg.get('grupo_clases_costo', ''))
        logger.info(f"Grup de classes de cost = {campo.Text}")

    def _ejecutar_busqueda(self):
        """Pulsa F8 para ejecutar la búsqueda."""
        logger.debug("Pulsando F8 para ejecutar búsqueda")
        self.session.findById("wnd[0]").sendVKey(8)
        time.sleep(self.timeout * 4)
        logger.info("F8 ejecutado — resultados cargados")

    def _navegar_detalle_centres(self):
        """Hace doble clic en '* Centres de cost' y espera a que cargue el detalle."""
        logger.info("Navegando a detalle: '* Centres de cost' (lbl[5,2])")

        target = self.session.findById("wnd[0]/usr/lbl[5,2]")
        logger.debug(f"Elemento encontrado: Text='{getattr(target, 'Text', '')}'")

        target.setFocus()
        self.session.findById("wnd[0]").sendVKey(2)  # F2 = doble clic
        logger.info("Doble clic enviado. Esperando carga de detalle (hasta 10 min)...")

        max_wait = 600
        interval = 10
        elapsed = 0

        while elapsed < max_wait:
            time.sleep(interval)
            elapsed += interval

            try:
                status_bar = self.session.findById("wnd[0]/sbar")
                status_text = getattr(status_bar, 'Text', '')

                try:
                    self.session.findById("wnd[0]/usr/lbl[5,2]")
                    logger.debug(f"Esperando... ({elapsed}s / {max_wait}s) - Status: {status_text}")
                    continue
                except Exception:
                    logger.info(f"Pantalla de detalle cargada tras {elapsed}s")
                    return

            except Exception as e:
                logger.debug(f"Error verificando pantalla ({elapsed}s): {e}")
                continue

        raise TimeoutError(f"La pantalla de detalle no cargó en {max_wait}s (10 min)")

    # ══════════════════════════════════════════════════════════════
    # FASE 2: Disposición
    # ══════════════════════════════════════════════════════════════

    def _abrir_modificar_disposicio(self):
        """Navega por menú Opcions > Disposició > Modificar para abrir el popup."""
        logger.info("Abriendo menú: Opcions > Disposició > Modificar...")

        self.session.findById("wnd[0]/mbar/menu[3]").select()
        time.sleep(0.3)
        self.session.findById("wnd[0]/mbar/menu[3]/menu[0]").select()
        time.sleep(0.3)
        self.session.findById("wnd[0]/mbar/menu[3]/menu[0]/menu[0]").select()
        time.sleep(1)

        try:
            popup = self.session.findById("wnd[1]")
            title = getattr(popup, 'Text', '')
            logger.info(f"Popup detectado: '{title}'")
        except Exception:
            raise RuntimeError("No se detectó el popup 'Modificar disposició'")

    _TAB_SELECCIO = "wnd[1]/usr/tabsG_TS_ALV/tabpALV_M_R1"
    _GRID_LLISTA = (
        "wnd[1]/usr/tabsG_TS_ALV/tabpALV_M_R1/"
        "ssubSUB_CONFIGURATION:SAPLSALV_CUL_COLUMN_SELECTION:0620/"
        "cntlCONTAINER1_LAYO/shellcont/shell"
    )
    _BTN_MOSTRAR = (
        "wnd[1]/usr/tabsG_TS_ALV/tabpALV_M_R1/"
        "ssubSUB_CONFIGURATION:SAPLSALV_CUL_COLUMN_SELECTION:0620/"
        "btnAPP_WL_SING"
    )
    _GRID_VISUALITZADES = (
        "wnd[1]/usr/tabsG_TS_ALV/tabpALV_M_R1/"
        "ssubSUB_CONFIGURATION:SAPLSALV_CUL_COLUMN_SELECTION:0620/"
        "cntlCONTAINER2_LAYO/shellcont/shell"
    )

    def _seleccionar_todas_columnas(self):
        """Selecciona todas las filas del grid derecho (Llista columnes)."""
        tab = self.session.findById(self._TAB_SELECCIO)
        tab.select()
        time.sleep(0.3)

        grid = self.session.findById(self._GRID_LLISTA)
        row_count = grid.RowCount
        logger.info(f"Grid 'Llista columnes': {row_count} columnas disponibles")

        all_rows = ",".join(str(i) for i in range(row_count))
        grid.SelectedRows = all_rows
        time.sleep(0.3)
        logger.info(f"Seleccionadas {row_count} filas")

    def _mostrar_camps_seleccionats(self):
        """Pulsa '>' para mover columnas a visualitzades."""
        self.session.findById(self._BTN_MOSTRAR).press()
        time.sleep(0.5)
        logger.info("Columnas movidas a 'Columnes visualitzades'")

    def _limpiar_sigma(self):
        """Limpia las celdas con 'Total (Σ)' en el grid izquierdo."""
        grid = self.session.findById(self._GRID_VISUALITZADES)
        row_count = grid.RowCount
        cols = grid.ColumnOrder
        col_names = [cols(i) for i in range(cols.Count)]
        logger.info(f"Grid izquierdo: {row_count} filas, columnas: {col_names}")

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

        logger.info(f"Limpiados {cleared} valores sigma en columna '{sigma_col}'")

    def _transferir(self):
        """Pulsa 'Transferir (Enter)' para confirmar la disposición."""
        logger.info("Pulsando 'Transferir (Enter)'...")
        self.session.findById("wnd[1]/tbar[0]/btn[0]").press()
        time.sleep(1)
        logger.info("Disposición transferida. Popup cerrado.")

    # ══════════════════════════════════════════════════════════════
    # FASE 3: Export
    # ══════════════════════════════════════════════════════════════

    _POPUP_EXPORT_BASE = (
        "wnd[1]/usr/ssubSUB_CONFIGURATION:SAPLSALV_GUI_CUL_EXPORT_AS:0512"
    )

    def _exportar_excel(self):
        """Llista > Exportar > Full de càlcul... y rellenar popup."""
        logger.info("Menú: Llista > Exportar > Full de càlcul...")
        self.session.findById("wnd[0]/mbar/menu[0]/menu[3]/menu[1]").select()
        time.sleep(1)

        # Nombre del fichero
        prefix = self.export_config.get('filename_prefix', 'SEGEC_GR55')
        filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        txt_filename = self.session.findById(f"{self._POPUP_EXPORT_BASE}/txtGS_EXPORT-FILE_NAME")
        txt_filename.Text = filename
        logger.info(f"Nom fitxer: {filename}")

        # Leer entries disponibles
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
            raise RuntimeError(f"Key de formato '{fmt}' no válido. Opciones: {fmt_entries}")
        current_fmt = cmb_format.Key.strip()
        if current_fmt != fmt:
            cmb_format.Key = fmt
        logger.info(f"Format: {fmt} = {fmt_entries[fmt]}")
        time.sleep(0.5)

        # Seleccionar destino
        dest = str(self.export_config.get('destination', 'L'))
        if dest not in dest_entries:
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

    def _guardar_fitxer(self, filename):
        """Rellena el popup de guardado y pulsa Substituir."""
        popup = self.session.findById("wnd[1]")
        title = getattr(popup, 'Text', '')
        logger.info(f"Popup guardado: '{title}'")

        directory = self.export_config.get('directory', 'C:\\TEMP')
        self.session.findById("wnd[1]/usr/ctxtDY_PATH").Text = directory
        logger.info(f"Directori: {directory}")

        fmt = str(self.export_config.get('format', 'csv-LEAN-STANDARD'))
        ext = 'csv' if 'csv' in fmt.lower() else 'xlsx'
        full_filename = f"{filename}.{ext}"
        self.session.findById("wnd[1]/usr/ctxtDY_FILENAME").Text = full_filename
        logger.info(f"NomFitxer: {full_filename}")

        time.sleep(0.3)

        self.session.findById("wnd[1]/tbar[0]/btn[11]").press()
        time.sleep(2)
        logger.info(f"Fitxer guardat: {directory}\\{full_filename}")


# ══════════════════════════════════════════════════════════════
# Entry point autónomo (modo credentials)
# ══════════════════════════════════════════════════════════════

def load_global_config():
    config_path = os.path.join(SCRIPT_DIR, '..', '..', '..', 'config', 'settings.yaml')
    with open(os.path.abspath(config_path), 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_credentials():
    secrets_path = os.path.join(SCRIPT_DIR, '..', '..', '..', 'config', 'secrets.yaml')
    with open(os.path.abspath(secrets_path), 'r', encoding='utf-8') as f:
        secrets = yaml.safe_load(f)
    return secrets.get('sap_credentials', {})


def main():
    logger = setup_logger()
    global_config = load_global_config()
    sap_cfg = global_config.get('sap', {})

    connection_mode = sap_cfg.get('connection_mode', 'credentials')
    logger.info(f"Connection mode: {connection_mode}")

    try:
        if connection_mode == "credentials":
            credentials = load_credentials()
            connection_string = sap_cfg.get('connection_string')
            if not connection_string:
                logger.critical("connection_string no definido en config/settings.yaml")
                sys.exit(1)

            sap_conn = SAPConnection(
                connection_mode="credentials",
                connection_string=connection_string,
                credentials=credentials
            )
        else:
            sap_conn = SAPConnection(
                connection_index=sap_cfg.get('connection_index', 0),
                session_index=sap_cfg.get('session_index', 0),
                connection_mode="existing_session"
            )

        session = sap_conn.connect()
    except Exception as e:
        logger.critical(f"Could not connect to SAP: {e}")
        sys.exit(1)

    script = SegecGR55Full(session, global_config)
    success = script.run()

    if success:
        logger.info("SEGEC GR55 completado correctamente.")
    else:
        logger.error("Error en SEGEC GR55.")
        sys.exit(1)


if __name__ == "__main__":
    main()
