"""Automatización modular de la transacción SAP SEGEC GR55.

Flujo ejecutado:
    1. Abre la transacción GR55.
    2. Carga el grupo de informes.
    3. Completa los filtros de selección.
    4. Ejecuta el informe.
    5. Abre el detalle de centros de coste.
    6. Configura la disposición de columnas.
    7. Elimina las agregaciones sigma.
    8. Exporta el resultado al formato configurado.

Ejecución directa:
    python src/scripts/segec_gr55_v2/segec_gr55.py

Ejecución desde main.py:
    python main.py --task segec_gr55_v2
"""

from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

import yaml
import win32com.client


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.sap_connection import SAPConnection
from src.utils.logger import setup_logger


logger = logging.getLogger("SAP_Automation")

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.yaml"
GLOBAL_CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"
SECRETS_PATH = PROJECT_ROOT / "config" / "secrets.yaml"


class SapIds:
    """Centraliza los identificadores utilizados por SAP GUI Scripting."""

    MAIN_WINDOW = "wnd[0]"
    MAIN_COMMAND = "wnd[0]/tbar[0]/okcd"
    MAIN_STATUS_BAR = "wnd[0]/sbar"

    REPORT_GROUP = "wnd[0]/usr/ctxtRGRWJ-JOB"

    SOCIEDAD_CO = "wnd[0]/usr/ctxt$1KOKRE"
    EJERCICIO = "wnd[0]/usr/txt$1GJAHLJ"
    PERIODO_DESDE = "wnd[0]/usr/ctxt$0FRPMAF"
    PERIODO_HASTA = "wnd[0]/usr/ctxt$0FRPMAT"
    GRUPO_CLASES_COSTE = "wnd[0]/usr/ctxt$1KSTAR"

    COST_CENTERS_DETAIL = "wnd[0]/usr/lbl[5,2]"

    LAYOUT_MENU = "wnd[0]/mbar/menu[3]"
    LAYOUT_SUBMENU = "wnd[0]/mbar/menu[3]/menu[0]"
    LAYOUT_MODIFY = "wnd[0]/mbar/menu[3]/menu[0]/menu[0]"

    LAYOUT_POPUP = "wnd[1]"

    LAYOUT_TAB_SELECTION = "wnd[1]/usr/tabsG_TS_ALV/tabpALV_M_R1"

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

    LAYOUT_VISIBLE_GRID = (
        "wnd[1]/usr/tabsG_TS_ALV/tabpALV_M_R1/"
        "ssubSUB_CONFIGURATION:SAPLSALV_CUL_COLUMN_SELECTION:0620/"
        "cntlCONTAINER2_LAYO/shellcont/shell"
    )

    LAYOUT_TRANSFER = "wnd[1]/tbar[0]/btn[0]"

    EXPORT_MENU = "wnd[0]/mbar/menu[0]/menu[3]/menu[1]"

    EXPORT_POPUP_BASE = (
        "wnd[1]/usr/"
        "ssubSUB_CONFIGURATION:SAPLSALV_GUI_CUL_EXPORT_AS:0512"
    )

    EXPORT_FILENAME = (
        f"{EXPORT_POPUP_BASE}/txtGS_EXPORT-FILE_NAME"
    )

    EXPORT_FORMAT = (
        f"{EXPORT_POPUP_BASE}/cmbGS_EXPORT-FORMAT"
    )

    EXPORT_DESTINATION = (
        f"{EXPORT_POPUP_BASE}/cmbGS_EXPORT-DESTINATION"
    )

    EXPORT_CONFIRM = "wnd[1]/tbar[0]/btn[20]"

    SAVE_POPUP = "wnd[1]"
    SAVE_DIRECTORY = "wnd[1]/usr/ctxtDY_PATH"
    SAVE_FILENAME = "wnd[1]/usr/ctxtDY_FILENAME"
    SAVE_CONFIRM = "wnd[1]/tbar[0]/btn[11]"
    INFORMATION_CONFIRM = "wnd[1]/tbar[0]/btn[0]"


class SegecGR55:
    """Coordina la automatización completa del informe SAP SEGEC GR55."""

    FORMAT_EXTENSIONS = {
        "csv-LEAN-STANDARD": "csv",
        "xlsx-LEAN-STANDARD": "xlsx",
        "8-TT-STANDARD": "xls",
    }

    REQUIRED_REPORT_CONFIG = (
        "sociedad_co",
        "ejercicio",
        "periodo_de",
        "periodo_fins",
        "grupo_clases_costo",
    )

    def __init__(
        self,
        session: Any,
        script_config: Mapping[str, Any],
        global_config: Mapping[str, Any],
    ) -> None:
        """Inicializa la automatización y valida su configuración."""
        self.session = session
        self.global_config = dict(global_config)

        self.segec_config = dict(
            script_config.get("segec_gr55", {})
        )
        self.export_config = dict(
            script_config.get("export", {})
        )

        timeout_config = self.global_config.get("timeouts", {})

        self.default_wait = float(
            timeout_config.get("default_wait", 0.5)
        )

        self.detail_timeout = int(
            timeout_config.get("report_wait", 600)
        )

        self.poll_interval = int(
            timeout_config.get("poll_interval", 10)
        )

        self._validate_config()

    def run(self) -> bool:
        """Ejecuta las fases principales de la automatización."""
        logger.info("=== SEGEC GR55 v2 - Inicio ===")

        try:
            self._run_report_phase()
            self._run_layout_phase()
            self._run_export_phase()
        except Exception:
            logger.exception("SEGEC GR55 v2 terminó con error.")
            return False

        logger.info(
            "=== SEGEC GR55 v2 - Finalizado correctamente ==="
        )
        return True

    def _run_report_phase(self) -> None:
        """Ejecuta la consulta y abre el detalle del informe."""
        logger.info("Iniciando fase de consulta del informe.")

        self._launch_transaction()
        self._open_selection_screen()
        self._fill_filters()
        self._execute_report()
        self._open_cost_centers_detail()

        logger.info("Fase de consulta completada.")

    def _run_layout_phase(self) -> None:
        """Configura las columnas visibles del informe."""
        logger.info("Iniciando fase de configuración de disposición.")

        self._open_layout_dialog()
        self._select_all_available_columns()
        self._move_selected_columns()
        self._clear_sigma_values()
        self._transfer_layout()

        logger.info("Fase de disposición completada.")

    def _run_export_phase(self) -> None:
        """Exporta, guarda y cierra las aplicaciones utilizadas."""
        logger.info("Iniciando fase de exportación.")

        filename = self._build_export_filename()
        self._open_export_dialog()
        self._configure_export(filename)
        self._confirm_export()

        exported_file = self._save_file(filename)

        self._close_exported_workbook(exported_file)
        self._close_sap_session()

        logger.info("Fase de exportación completada.")

    def _validate_config(self) -> None:
        """Comprueba que la configuración mínima esté disponible."""
        missing_report_values = [
            key
            for key in self.REQUIRED_REPORT_CONFIG
            if self.segec_config.get(key) in (None, "")
        ]

        if missing_report_values:
            missing = ", ".join(missing_report_values)
            raise ValueError(
                "Faltan valores obligatorios en "
                f"segec_gr55: {missing}"
            )

        export_format = str(
            self.export_config.get(
                "format",
                "csv-LEAN-STANDARD",
            )
        )

        if export_format not in self.FORMAT_EXTENSIONS:
            valid_formats = ", ".join(
                self.FORMAT_EXTENSIONS
            )
            raise ValueError(
                f"Formato de exportación no soportado: "
                f"{export_format}. Opciones: {valid_formats}"
            )

    def _launch_transaction(self) -> None:
        """Abre GR55 y completa el grupo de informes."""
        transaction = str(
            self.segec_config.get("transaction", "/nGR55")
        )
        report_group = str(
            self.segec_config.get("report_group", "Z002")
        )

        logger.info("Abriendo transacción %s.", transaction)

        command_field = self._find(SapIds.MAIN_COMMAND)
        command_field.Text = transaction

        self._send_key(0)
        self._sleep()

        report_group_field = self._find(
            SapIds.REPORT_GROUP
        )
        report_group_field.Text = report_group

        logger.info(
            "Grupo de informes configurado: %s.",
            report_group,
        )

    def _open_selection_screen(self) -> None:
        """Avanza a la pantalla de selección del informe."""
        logger.info("Abriendo pantalla de selección.")

        self._send_key(8)
        self._sleep()

    def _fill_filters(self) -> None:
        """Completa los filtros definidos en config.yaml."""
        logger.info("Completando filtros del informe.")

        fields = (
            (
                SapIds.SOCIEDAD_CO,
                "sociedad_co",
                "Sociedad CO",
            ),
            (
                SapIds.EJERCICIO,
                "ejercicio",
                "Ejercicio",
            ),
            (
                SapIds.PERIODO_DESDE,
                "periodo_de",
                "Periodo desde",
            ),
            (
                SapIds.PERIODO_HASTA,
                "periodo_fins",
                "Periodo hasta",
            ),
            (
                SapIds.GRUPO_CLASES_COSTE,
                "grupo_clases_costo",
                "Grupo de clases de coste",
            ),
        )

        for element_id, config_key, label in fields:
            value = self.segec_config[config_key]
            self._set_text_field(
                element_id=element_id,
                value=value,
                label=label,
            )

    def _execute_report(self) -> None:
        """Ejecuta el informe mediante F8."""
        logger.info("Ejecutando informe GR55.")

        self._send_key(8)
        self._sleep(multiplier=4)

    def _open_cost_centers_detail(self) -> None:
        """Abre el detalle de centros de coste."""
        logger.info(
            "Abriendo detalle de centros de coste."
        )

        target = self._find(
            SapIds.COST_CENTERS_DETAIL
        )

        target.setFocus()
        self._send_key(2)

        logger.info(
            "Esperando la carga del detalle."
        )

        self._wait_until_element_disappears(
            element_id=SapIds.COST_CENTERS_DETAIL,
            timeout=self.detail_timeout,
            interval=self.poll_interval,
            description=(
                "pantalla inicial del informe"
            ),
        )

        logger.info(
            "Detalle de centros de coste cargado."
        )

    def _open_layout_dialog(self) -> None:
        """Abre Opciones > Disposición > Modificar."""
        logger.info(
            "Abriendo diálogo de modificación de disposición."
        )

        self._find(SapIds.LAYOUT_MENU).select()
        self._sleep(0.3)

        self._find(SapIds.LAYOUT_SUBMENU).select()
        self._sleep(0.3)

        self._find(SapIds.LAYOUT_MODIFY).select()
        self._sleep(1)

        popup = self._find(SapIds.LAYOUT_POPUP)
        popup_title = str(
            getattr(popup, "Text", "")
        )

        logger.info(
            "Diálogo de disposición detectado: %s.",
            popup_title or "<sin título>",
        )

    def _select_all_available_columns(self) -> None:
        """Selecciona todas las columnas disponibles."""
        tab = self._find(
            SapIds.LAYOUT_TAB_SELECTION
        )
        tab.select()
        self._sleep(0.3)

        grid = self._find(
            SapIds.LAYOUT_AVAILABLE_GRID
        )
        row_count = int(grid.RowCount)

        if row_count <= 0:
            logger.info(
                "No hay columnas adicionales disponibles."
            )
            return

        selected_rows = ",".join(
            str(row)
            for row in range(row_count)
        )
        grid.SelectedRows = selected_rows

        self._sleep(0.3)

        logger.info(
            "%s columnas disponibles seleccionadas.",
            row_count,
        )

    def _move_selected_columns(self) -> None:
        """Mueve las columnas seleccionadas al listado visible."""
        button = self._find(
            SapIds.LAYOUT_MOVE_SELECTED
        )
        button.press()

        self._sleep(0.5)

        logger.info(
            "Columnas transferidas al listado visible."
        )

    def _clear_sigma_values(self) -> None:
        """Elimina las agregaciones configuradas en el grid de columnas visibles."""
        grid = self._find(SapIds.LAYOUT_VISIBLE_GRID)
        row_count = int(grid.RowCount)
        column_names = self._get_grid_column_names(grid)

        sigma_column = "AGGREGATION_TYPE"

        if sigma_column not in column_names:
            raise RuntimeError(
                f"No existe la columna '{sigma_column}'. "
                f"Columnas disponibles: {column_names}"
            )

        modified_rows: list[int] = []

        for row in range(row_count):
            value = str(
                grid.GetCellValue(row, sigma_column)
            ).strip()

            if not value:
                continue

            logger.info(
                "Eliminando agregación de la fila %s: %s",
                row,
                value,
            )

            grid.ModifyCell(row, sigma_column, " ")
            modified_rows.append(row)

        if modified_rows:
            last_modified_row = modified_rows[-1]
            grid.SetCurrentCell(last_modified_row, sigma_column)
            self._sleep(0.3)

        logger.info(
            "Se eliminaron %s valores de agregación.",
            len(modified_rows),
        )

    def _transfer_layout(self) -> None:
        """Confirma la disposición seleccionada."""
        logger.info("Confirmando disposición.")

        button = self._find(
            SapIds.LAYOUT_TRANSFER
        )
        button.press()

        self._sleep(1)

    def _build_export_filename(self) -> str:
        """Construye el nombre base del archivo exportado."""
        prefix = str(
            self.export_config.get(
                "filename_prefix",
                "SEGEC_GR55",
            )
        ).strip()

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        return f"{prefix}_{timestamp}"

    def _open_export_dialog(self) -> None:
        """Abre Lista > Exportar > Hoja de cálculo."""
        logger.info(
            "Abriendo diálogo de exportación."
        )

        self._find(SapIds.EXPORT_MENU).select()
        self._sleep(1)

    def _configure_export(
        self,
        filename: str,
    ) -> None:
        """Configura nombre, formato y destino."""
        filename_field = self._find(
            SapIds.EXPORT_FILENAME
        )
        filename_field.Text = filename

        format_combo = self._find(
            SapIds.EXPORT_FORMAT
        )

        format_entries = self._read_combo_entries(
            format_combo
        )

        configured_format = str(
            self.export_config.get(
                "format",
                "csv-LEAN-STANDARD",
            )
        ).strip()

        self._select_combo_value(
            combo=format_combo,
            entries=format_entries,
            configured_key=configured_format,
            label="formato",
        )

        self._sleep(0.5)

        destination_combo = self._find(
            SapIds.EXPORT_DESTINATION
        )

        destination_entries = (
            self._read_combo_entries(
                destination_combo
            )
        )

        configured_destination = str(
            self.export_config.get(
                "destination",
                "L",
            )
        ).strip()

        self._select_combo_value(
            combo=destination_combo,
            entries=destination_entries,
            configured_key=configured_destination,
            label="destino",
        )

        self._sleep(0.3)

        logger.info(
            "Exportación configurada: archivo=%s, "
            "formato=%s, destino=%s.",
            filename,
            configured_format,
            configured_destination,
        )

    def _confirm_export(self) -> None:
        """Confirma la exportación configurada."""
        button = self._find(
            SapIds.EXPORT_CONFIRM
        )
        button.press()

        self._sleep(3)

    def _save_file(
        self,
        filename: str,
    ) -> str:
        """Gestiona el diálogo de guardado del archivo."""
        popup = self._find(
            SapIds.SAVE_POPUP
        )
        popup_title = str(
            getattr(popup, "Text", "")
        ).strip()

        if popup_title == "Informació":
            logger.info(
                "Confirmando aviso informativo previo."
            )

            self._find(
                SapIds.INFORMATION_CONFIRM
            ).press()

            self._sleep(3)

            popup = self._find(
                SapIds.SAVE_POPUP
            )
            popup_title = str(
                getattr(popup, "Text", "")
            ).strip()

        logger.info(
            "Diálogo de guardado detectado: %s.",
            popup_title or "<sin título>",
        )

        directory = str(
            self.export_config.get(
                "directory",
                r"C:\TEMP",
            )
        )

        export_format = str(
            self.export_config.get(
                "format",
                "csv-LEAN-STANDARD",
            )
        )

        extension = self.FORMAT_EXTENSIONS[
            export_format
        ]

        full_filename = (
            f"{filename}.{extension}"
        )

        directory_field = self._find(
            SapIds.SAVE_DIRECTORY
        )
        directory_field.Text = directory

        filename_field = self._find(
            SapIds.SAVE_FILENAME
        )
        filename_field.Text = full_filename

        self._sleep(0.3)

        self._find(
            SapIds.SAVE_CONFIRM
        ).press()

        self._sleep(2)

        full_path = os.path.join(
            directory,
            full_filename,
        )

        logger.info(
            "Archivo guardado: %s.",
            full_path,
        )

        return full_path

    def _set_text_field(
        self,
        element_id: str,
        value: Any,
        label: str,
    ) -> None:
        """Completa un campo SAP y registra su valor."""
        field = self._find(element_id)
        field.setFocus()
        field.Text = str(value)

        logger.info(
            "%s = %s.",
            label,
            value,
        )

    def _find(
        self,
        element_id: str,
    ) -> Any:
        """Obtiene un elemento SAP y añade contexto al error."""
        try:
            return self.session.findById(
                element_id
            )
        except Exception as exc:
            raise RuntimeError(
                "No se encontró el elemento SAP "
                f"'{element_id}'."
            ) from exc

    def _send_key(
        self,
        key: int,
    ) -> None:
        """Envía una tecla virtual a la ventana principal."""
        try:
            main_window = self._find(
                SapIds.MAIN_WINDOW
            )
            main_window.sendVKey(key)
        except Exception as exc:
            raise RuntimeError(
                f"No se pudo enviar la tecla SAP {key}."
            ) from exc

    def _sleep(
        self,
        seconds: float | None = None,
        multiplier: float = 1,
    ) -> None:
        """Espera el tiempo configurado o uno explícito."""
        wait_seconds = (
            self.default_wait * multiplier
            if seconds is None
            else seconds
        )

        time.sleep(wait_seconds)

    def _wait_until_element_disappears(
        self,
        element_id: str,
        timeout: int,
        interval: int,
        description: str,
    ) -> None:
        """Espera hasta que un elemento deje de estar disponible."""
        started_at = time.monotonic()

        while True:
            elapsed = int(
                time.monotonic() - started_at
            )

            if elapsed >= timeout:
                status_text = (
                    self._get_status_bar_text()
                )

                raise TimeoutError(
                    f"No desapareció {description} "
                    f"después de {timeout} segundos. "
                    f"Estado SAP: {status_text}"
                )

            try:
                self.session.findById(
                    element_id
                )
            except Exception:
                return

            status_text = (
                self._get_status_bar_text()
            )

            logger.debug(
                "Esperando %s: %ss/%ss. Estado: %s",
                description,
                elapsed,
                timeout,
                status_text,
            )

            time.sleep(interval)

    def _get_status_bar_text(self) -> str:
        """Obtiene el mensaje actual de la barra de estado."""
        try:
            status_bar = self.session.findById(
                SapIds.MAIN_STATUS_BAR
            )
            return str(
                getattr(status_bar, "Text", "")
            )
        except Exception:
            return "<no disponible>"

    @staticmethod
    def _get_grid_column_names(
        grid: Any,
    ) -> list[str]:
        """Devuelve los nombres internos de las columnas."""
        column_order = grid.ColumnOrder

        return [
            str(column_order(index))
            for index in range(
                int(column_order.Count)
            )
        ]

    @staticmethod
    def _find_sigma_column(
        grid: Any,
        row_count: int,
        column_names: list[str],
    ) -> str | None:
        """Inspecciona las columnas visibles para identificar la columna sigma."""
        rows_to_inspect = min(row_count, 20)

        for column_name in column_names:
            values = []

            for row in range(rows_to_inspect):
                value = str(
                    grid.GetCellValue(row, column_name)
                ).strip()

                values.append(value)

            logger.info(
                "Columna disposición '%s': %s",
                column_name,
                values,
            )

            for value in values:
                if "Σ" in value or "Total" in value:
                    return column_name

        return None

    @staticmethod
    def _read_combo_entries(
        combo: Any,
    ) -> dict[str, dict[str, str]]:
        """Lee las claves y etiquetas disponibles de un combo SAP."""
        entries: dict[
            str,
            dict[str, str],
        ] = {}

        for index in range(
            int(combo.Entries.Count)
        ):
            entry = combo.Entries(index)
            raw_key = str(entry.Key)
            normalized_key = raw_key.strip()

            entries[normalized_key] = {
                "raw_key": raw_key,
                "label": str(
                    entry.Value
                ).strip(),
            }

        return entries

    @staticmethod
    def _select_combo_value(
        combo: Any,
        entries: Mapping[
            str,
            Mapping[str, str],
        ],
        configured_key: str,
        label: str,
    ) -> None:
        """Selecciona una opción conservando la clave SAP original."""
        if configured_key not in entries:
            available = ", ".join(
                f"{key}={value['label']}"
                for key, value in entries.items()
            )

            raise RuntimeError(
                f"Clave de {label} no válida: "
                f"'{configured_key}'. "
                f"Opciones disponibles: {available}"
            )

        current_key = str(
            combo.Key
        ).strip()

        if current_key != configured_key:
            raw_key = entries[
                configured_key
            ]["raw_key"]

            combo.Key = raw_key

        logger.info(
            "%s seleccionado: %s = %s.",
            label.capitalize(),
            configured_key,
            entries[configured_key]["label"],
        )

    def _close_report(self) -> None:
        """Cierra la transacción actual y vuelve a la pantalla principal de SAP."""
        logger.info("Cerrando el informe GR55.")

        command_field = self._find(SapIds.MAIN_COMMAND)
        command_field.Text = "/n"

        self._send_key(0)
        self._sleep(1)

        logger.info("Informe GR55 cerrado.")

    def _close_sap_session(self) -> None:
        """Finaliza la sesión actual de SAP sin mostrar confirmación."""
        logger.info("Cerrando la sesión de SAP.")

        command_field = self._find(SapIds.MAIN_COMMAND)
        command_field.Text = "/nex"

        self._send_key(0)
        time.sleep(2)

        logger.info("Sesión de SAP cerrada.")

    def _close_exported_workbook(
        self,
        file_path: str,
        timeout: int = 30,
    ) -> None:
        """Cierra el libro exportado conectándose directamente a su archivo."""
        logger.info("Cerrando el libro exportado en Excel.")

        expected_path = os.path.normcase(
            os.path.abspath(file_path)
        )
        started_at = time.monotonic()
        last_error: Exception | None = None

        while time.monotonic() - started_at < timeout:
            try:
                workbook = win32com.client.GetObject(expected_path)
                excel = workbook.Application

                opened_path = os.path.normcase(
                    os.path.abspath(str(workbook.FullName))
                )

                if opened_path != expected_path:
                    raise RuntimeError(
                        "Excel devolvió un libro diferente: "
                        f"{opened_path}"
                    )

                workbook.Close(SaveChanges=False)

                logger.info(
                    "Libro de Excel cerrado: %s.",
                    file_path,
                )

                if excel.Workbooks.Count == 0:
                    excel.Quit()
                    logger.info("Sesión de Excel cerrada.")

                return

            except Exception as exc:
                last_error = exc
                logger.debug(
                    "Esperando acceso al libro de Excel: %s",
                    exc,
                )
                time.sleep(1)

        raise TimeoutError(
            "No se pudo conectar con el libro exportado en Excel: "
            f"{file_path}. Último error: {last_error}"
        )


def load_yaml_file(
    path: Path,
) -> dict[str, Any]:
    """Carga un archivo YAML y garantiza un diccionario."""
    if not path.exists():
        raise FileNotFoundError(
            f"No existe el archivo de configuración: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        content = yaml.safe_load(file)

    if content is None:
        return {}

    if not isinstance(content, dict):
        raise TypeError(
            f"El archivo YAML debe contener un diccionario: {path}"
        )

    return content


def load_global_config() -> dict[str, Any]:
    """Carga la configuración global del proyecto."""
    return load_yaml_file(
        GLOBAL_CONFIG_PATH
    )


def load_script_config() -> dict[str, Any]:
    """Carga la configuración específica de SEGEC GR55 v2."""
    return load_yaml_file(
        CONFIG_PATH
    )


def load_credentials() -> dict[str, Any]:
    """Carga las credenciales SAP desde secrets.yaml."""
    secrets = load_yaml_file(
        SECRETS_PATH
    )

    credentials = secrets.get(
        "sap_credentials",
        {},
    )

    if not isinstance(credentials, dict):
        raise TypeError(
            "sap_credentials debe ser un diccionario."
        )

    return credentials


def create_sap_connection(
    global_config: Mapping[str, Any],
) -> SAPConnection:
    """Construye la conexión SAP según el modo configurado."""
    sap_config = dict(
        global_config.get("sap", {})
    )

    connection_mode = str(
        sap_config.get(
            "connection_mode",
            "credentials",
        )
    )

    logger.info(
        "Modo de conexión SAP: %s.",
        connection_mode,
    )

    if connection_mode == "credentials":
        credentials = load_credentials()

        connection_string = sap_config.get(
            "connection_string"
        )

        if not connection_string:
            raise ValueError(
                "connection_string no está definido "
                "en config/settings.yaml."
            )

        return SAPConnection(
            connection_mode="credentials",
            connection_string=connection_string,
            credentials=credentials,
        )

    if connection_mode == "existing_session":
        return SAPConnection(
            connection_index=int(
                sap_config.get(
                    "connection_index",
                    0,
                )
            ),
            session_index=int(
                sap_config.get(
                    "session_index",
                    0,
                )
            ),
            connection_mode="existing_session",
        )

    raise ValueError(
        "Modo de conexión SAP no soportado: "
        f"{connection_mode}"
    )


def main() -> int:
    """Ejecuta SEGEC GR55 v2 como script autónomo."""
    setup_logger()

    try:
        global_config = load_global_config()
        script_config = load_script_config()

        sap_connection = create_sap_connection(
            global_config
        )

        session = sap_connection.connect()

        automation = SegecGR55(
            session=session,
            script_config=script_config,
            global_config=global_config,
        )

        success = automation.run()

    except Exception:
        logger.exception(
            "No se pudo iniciar SEGEC GR55 v2."
        )
        return 1

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())