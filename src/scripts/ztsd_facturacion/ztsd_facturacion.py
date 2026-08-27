"""Extractor de SAP para ZTSD_FACTURACION - Facturació ALV.

Flujo automatizado a partir de una grabación SAP GUI:
    1. Abre /nZTSD_FACTURACION.
    2. Selecciona como fecha el día calendario anterior.
    3. Ejecuta el informe.
    4. Añade todas las columnas disponibles al ALV.
    5. Exporta el ALV a Excel.
    6. Guarda el archivo con fecha de datos y UUID corto.
    7. Cierra el libro de Excel exportado y la sesión SAP.

Ejecución directa:
    python src/scripts/ztsd_facturacion/ztsd_facturacion.py
"""

from __future__ import annotations

import logging
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

import win32com.client
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.sap_connection import SAPConnection
from src.utils.logger import setup_logger


logger = logging.getLogger("SAP_Automation")

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.yaml"
GLOBAL_CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"


class SapIds:
    """Identificadores observados en la grabación SAP GUI."""

    MAIN_WINDOW = "wnd[0]"
    MAIN_COMMAND = "wnd[0]/tbar[0]/okcd"
    STATUS_BAR = "wnd[0]/sbar"

    DATE_LOW = "wnd[0]/usr/ctxtS_IENDT-LOW"
    DATE_CALENDAR = "wnd[1]/usr/cntlCONTAINER/shellcont/shell"

    ALV_GRID = "wnd[0]/usr/cntlALV_CONTAINER/shellcont/shell"

    LAYOUT_AVAILABLE_GRID = (
        "wnd[1]/usr/tabsG_TS_ALV/tabpALV_M_R1/"
        "ssubSUB_CONFIGURATION:SAPLSALV_CUL_COLUMN_SELECTION:0620/"
        "cntlCONTAINER1_LAYO/shellcont/shell"
    )
    LAYOUT_MOVE_SELECTED = (
        "wnd[1]/usr/tabsG_TS_ALV/tabpALV_M_R1/"
        "ssubSUB_CONFIGURATION:SAPLSALV_CUL_COLUMN_SELECTION:0620/"
        "btnAPP_WL_SING"
    )
    LAYOUT_TRANSFER = "wnd[1]/tbar[0]/btn[0]"

    EXPORT_CONFIRM = "wnd[1]/tbar[0]/btn[20]"
    SAVE_DIRECTORY = "wnd[1]/usr/ctxtDY_PATH"
    SAVE_FILENAME = "wnd[1]/usr/ctxtDY_FILENAME"
    SAVE_CONFIRM = "wnd[1]/tbar[0]/btn[11]"
    INFORMATION_CONFIRM = "wnd[1]/tbar[0]/btn[0]"

    EXIT_CONFIRM_YES = "wnd[1]/usr/btnSPOP-OPTION1"


class ZtsdFacturacionExtractor:
    """Coordina la extracción diaria de Facturació ALV."""

    def __init__(
        self,
        session: Any,
        script_config: Mapping[str, Any],
        global_config: Mapping[str, Any],
    ) -> None:
        self.session = session
        self.global_config = dict(global_config)
        self.report_config = dict(script_config.get("ztsd_facturacion", {}))
        self.export_config = dict(script_config.get("export", {}))

        timeout_config = self.global_config.get("timeouts", {})
        self.default_wait = float(timeout_config.get("default_wait", 0.5))
        self.report_timeout = int(self.report_config.get("report_timeout", 300))
        self.poll_interval = float(self.report_config.get("poll_interval", 2))

        self.transaction = str(
            self.report_config.get("transaction", "/nZTSD_FACTURACION")
        )
        self.date_offset_days = int(self.report_config.get("date_offset_days", 1))
        self.export_directory = Path(
            str(self.export_config.get("directory", r"C:\sap_automate\exports"))
        )
        self.filename_prefix = str(
            self.export_config.get("filename_prefix", "ZTSD_FACTURACION")
        )
        self.extension = str(self.export_config.get("extension", "xlsx")).lstrip(".")
        self.run_id_length = int(self.export_config.get("run_id_length", 8))

        if self.date_offset_days < 0:
            raise ValueError("date_offset_days no puede ser negativo.")
        if self.run_id_length < 4 or self.run_id_length > 32:
            raise ValueError("run_id_length debe estar entre 4 y 32.")

    def run(self) -> bool:
        """Ejecuta el extractor completo."""
        target_date = date.today() - timedelta(days=self.date_offset_days)
        run_id = uuid4().hex[: self.run_id_length]
        filename = self._build_filename(target_date, run_id)

        logger.info("=== ZTSD_FACTURACION - Inicio ===")
        logger.info("Fecha de datos: %s", target_date.isoformat())
        logger.info("Run ID: %s", run_id)
        logger.info("Archivo de salida: %s", filename)

        try:
            self._launch_transaction()
            self._select_date(target_date)
            self._execute_report()
            self._show_all_columns()
            exported_file = self._export_alv(filename)
            self._close_exported_workbook(exported_file)
            self._close_sap_session()
        except Exception:
            logger.exception("ZTSD_FACTURACION terminó con error.")
            return False

        logger.info("=== ZTSD_FACTURACION - Finalizado correctamente ===")
        return True

    def _launch_transaction(self) -> None:
        logger.info("Abriendo transacción %s", self.transaction)
        self._find(SapIds.MAIN_WINDOW).maximize()
        command = self._find(SapIds.MAIN_COMMAND)
        command.Text = self.transaction
        self._send_key(0)
        self._wait_for_element(SapIds.DATE_LOW, timeout=30)

    def _select_date(self, target_date: date) -> None:
        """Selecciona la fecha mediante el calendario, igual que la grabación SAP."""
        sap_date = target_date.strftime("%Y%m%d")
        logger.info("Seleccionando fecha SAP: %s", sap_date)

        date_field = self._find(SapIds.DATE_LOW)
        date_field.setFocus()
        try:
            date_field.caretPosition = 0
        except Exception:
            pass

        self._send_key(4)
        calendar = self._wait_for_element(SapIds.DATE_CALENDAR, timeout=30)
        calendar.focusDate = sap_date
        calendar.selectionInterval = f"{sap_date},{sap_date}"
        self._sleep()

    def _execute_report(self) -> None:
        logger.info("Ejecutando Facturació ALV.")
        self._send_key(8)
        self._wait_for_element(SapIds.ALV_GRID, timeout=self.report_timeout)
        logger.info("ALV cargado.")

    def _show_all_columns(self) -> None:
        """Añade al ALV todas las columnas disponibles."""
        logger.info("Abriendo configuración de columnas del ALV.")
        alv = self._find(SapIds.ALV_GRID)
        alv.pressToolbarButton("&MB_VARIANT")

        available = self._wait_for_element(
            SapIds.LAYOUT_AVAILABLE_GRID,
            timeout=30,
        )

        row_count = int(getattr(available, "RowCount", 0))
        logger.info("Columnas adicionales disponibles: %s", row_count)

        if row_count > 0:
            try:
                available.setCurrentCell(-1, "")
            except Exception:
                pass
            available.selectAll()
            self._find(SapIds.LAYOUT_MOVE_SELECTED).press()
            self._sleep()

        self._find(SapIds.LAYOUT_TRANSFER).press()
        self._wait_for_element(SapIds.ALV_GRID, timeout=30)
        logger.info("Disposición del ALV aplicada.")

    def _export_alv(self, filename: str) -> Path:
        """Exporta el ALV al directorio configurado."""
        self.export_directory.mkdir(parents=True, exist_ok=True)
        target_file = self.export_directory / filename

        if target_file.exists():
            raise FileExistsError(f"El archivo ya existe: {target_file}")

        logger.info("Iniciando exportación ALV a %s", target_file)
        alv = self._find(SapIds.ALV_GRID)

        try:
            alv.currentCellColumn = "FRAGE"
        except Exception:
            logger.debug("No fue posible fijar FRAGE como columna actual.")

        alv.contextMenu()
        alv.selectContextMenuItem("&XXL")

        self._wait_for_element(SapIds.EXPORT_CONFIRM, timeout=30).press()

        path_field = self._wait_for_element(SapIds.SAVE_DIRECTORY, timeout=30)
        filename_field = self._find(SapIds.SAVE_FILENAME)

        path_field.Text = str(self.export_directory)
        filename_field.Text = filename
        self._find(SapIds.SAVE_CONFIRM).press()

        self._wait_for_file(target_file, timeout=60)
        self._dismiss_information_popup_if_present()

        logger.info("Archivo exportado correctamente: %s", target_file)
        return target_file

    def _build_filename(self, target_date: date, run_id: str) -> str:
        return (
            f"{self.filename_prefix}_"
            f"{target_date.strftime('%Y%m%d')}_"
            f"{run_id}.{self.extension}"
        )

    def _wait_for_element(self, element_id: str, timeout: float) -> Any:
        deadline = time.monotonic() + timeout
        last_error: Exception | None = None

        while time.monotonic() < deadline:
            try:
                return self.session.findById(element_id)
            except Exception as exc:
                last_error = exc
                time.sleep(self.poll_interval)

        status = self._status_text()
        message = f"Timeout esperando el elemento SAP: {element_id}"
        if status:
            message += f". Barra de estado: {status}"
        raise TimeoutError(message) from last_error

    def _wait_for_file(self, file_path: Path, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if file_path.exists() and file_path.stat().st_size > 0:
                return
            time.sleep(1)
        raise TimeoutError(f"SAP no creó el archivo esperado: {file_path}")

    def _close_exported_workbook(self, file_path: Path, timeout: int = 30) -> None:
        """Cierra únicamente el libro exportado y Excel si queda sin libros."""
        logger.info("Buscando el libro exportado para cerrarlo.")
        deadline = time.monotonic() + timeout
        workbook = None
        excel_app = None

        while time.monotonic() < deadline and workbook is None:
            try:
                workbook = win32com.client.GetObject(str(file_path))
                excel_app = workbook.Application
                break
            except Exception:
                pass

            try:
                excel_app = win32com.client.GetActiveObject("Excel.Application")
                for index in range(1, excel_app.Workbooks.Count + 1):
                    candidate = excel_app.Workbooks(index)
                    try:
                        if Path(candidate.FullName).resolve() == file_path.resolve():
                            workbook = candidate
                            break
                    except Exception:
                        continue
            except Exception:
                excel_app = None

            if workbook is None:
                time.sleep(1)

        if workbook is None:
            logger.info("El archivo no está abierto en Excel; no hay libro que cerrar.")
            return

        workbook.Close(SaveChanges=False)
        logger.info("Libro exportado cerrado.")

        try:
            if excel_app is not None and excel_app.Workbooks.Count == 0:
                excel_app.Quit()
                logger.info("Excel cerrado.")
        except Exception as exc:
            logger.warning("No fue posible cerrar Excel: %s", exc)

    def _close_sap_session(self) -> None:
        """Cierra la sesión SAP utilizada y confirma el diálogo de salida."""
        logger.info("Cerrando sesión SAP.")
        command = self._find(SapIds.MAIN_COMMAND)
        command.Text = "/i"
        self._send_key(0)

        try:
            self._wait_for_element(SapIds.EXIT_CONFIRM_YES, timeout=10).press()
            logger.info("Confirmación de salida SAP aceptada.")
        except TimeoutError:
            logger.info("SAP no mostró diálogo de confirmación de salida.")

        time.sleep(2)
        logger.info("Sesión SAP cerrada.")

    def _dismiss_information_popup_if_present(self) -> None:
        try:
            self.session.findById(SapIds.INFORMATION_CONFIRM).press()
        except Exception:
            pass

    def _status_text(self) -> str:
        try:
            return str(self.session.findById(SapIds.STATUS_BAR).Text).strip()
        except Exception:
            return ""

    def _find(self, element_id: str) -> Any:
        try:
            return self.session.findById(element_id)
        except Exception as exc:
            status = self._status_text()
            message = f"No se encontró el elemento SAP: {element_id}"
            if status:
                message += f". Barra de estado: {status}"
            raise RuntimeError(message) from exc

    def _send_key(self, key: int) -> None:
        self._find(SapIds.MAIN_WINDOW).sendVKey(key)

    def _sleep(self, seconds: float | None = None) -> None:
        time.sleep(self.default_wait if seconds is None else seconds)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def build_sap_connection(global_config: Mapping[str, Any]) -> SAPConnection:
    sap_config = dict(global_config.get("sap", {}))
    connection_mode = str(sap_config.get("connection_mode", "existing_session"))

    if connection_mode == "existing_session":
        return SAPConnection(
            connection_index=int(sap_config.get("connection_index", 0)),
            session_index=int(sap_config.get("session_index", 0)),
            connection_mode="existing_session",
        )

    if connection_mode == "credentials":
        from src.utils.credential_manager import get_credentials, validate_credentials

        credentials = get_credentials(use_keyring=True)
        if not validate_credentials(credentials, require_all=False):
            raise RuntimeError("Las credenciales SAP no están configuradas correctamente.")

        connection_string = sap_config.get("connection_string")
        if not connection_string:
            raise ValueError(
                "connection_string no está definido en config/settings.yaml."
            )

        return SAPConnection(
            connection_mode="credentials",
            connection_string=str(connection_string),
            credentials=credentials,
        )

    raise ValueError(f"Modo de conexión SAP no soportado: {connection_mode}")


def main() -> int:
    setup_logger()

    try:
        global_config = load_yaml(GLOBAL_CONFIG_PATH)
        script_config = load_yaml(CONFIG_PATH)
        sap_connection = build_sap_connection(global_config)
        session = sap_connection.connect()

        extractor = ZtsdFacturacionExtractor(
            session=session,
            script_config=script_config,
            global_config=global_config,
        )
        success = extractor.run()
        return 0 if success else 1
    except Exception:
        logger.exception("No fue posible ejecutar ZTSD_FACTURACION.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
