"""
Exportador multi-cliente (CLI)
================================

Nuevo script que contiene un mapa completo de campos (`FIELD_MAP`) y
permite pasar filtros por línea de comandos a la función `run`.

Modo de uso (ejemplo):
python3 -m src.scripts.export_multi_client_cli --clients src/scripts/clientes.txt --filter date_end_service=01/01/2025:31/12/2025 --filter status=F --connection-mode credentials

Soporta filtros en formato `key=value` (LOW) o `key=low:high`.
Si se pasa `--simulate`, no requiere sesión SAP y sólo emula la ejecución.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, Optional, Tuple
import yaml
from src.core.sap_utils import find_alv_shell, handle_security_popup, close_excel_workbook

logger = logging.getLogger("SAP_Automation")
logging.basicConfig(level=logging.INFO)


# =========================================================
# 1) MAPA HARDcodeado COMPLETO (todos los campos editables)
# =========================================================
# Claves lógicas => IDs SAP GUI para LOW/HIGH
FIELD_MAP = {
    "auth_1": {  # Autorització 1 (S_AUTNR)
        "low": "wnd[0]/usr/txtS_AUTNR-LOW",
        "high": "wnd[0]/usr/txtS_AUTNR-HIGH",
    },
    "centre_idi": {  # Codi centre sanitari del IDI (S_CENTRE)
        "low": "wnd[0]/usr/ctxtS_CENTRE-LOW",
        "high": "wnd[0]/usr/ctxtS_CENTRE-HIGH",
    },
    "generic_code": {  # Codi genérica (S_COD_GE)
        "low": "wnd[0]/usr/ctxtS_COD_GE-LOW",
        "high": "wnd[0]/usr/ctxtS_COD_GE-HIGH",
    },
    "trial_study_code": {  # Codi de l’assaig/estudi (S_COD_PR)
        "low": "wnd[0]/usr/ctxtS_COD_PR-LOW",
        "high": "wnd[0]/usr/ctxtS_COD_PR-HIGH",
    },
    "requesting_entity": {  # Entitat sol•licitant (S_ENTIT)
        "low": "wnd[0]/usr/ctxtS_ENTIT-LOW",
        "high": "wnd[0]/usr/ctxtS_ENTIT-HIGH",
    },
    "auth_2": {  # Autorització 2 (S_FRAGE)
        "low": "wnd[0]/usr/txtS_FRAGE-LOW",
        "high": "wnd[0]/usr/txtS_FRAGE-HIGH",
    },
    "year": {  # Any període facturació (S_GJAHR)
        "low": "wnd[0]/usr/txtS_GJAHR-LOW",
        "high": "wnd[0]/usr/txtS_GJAHR-HIGH",
    },
    "hospital": {  # Hospital (S_HOSP)
        "low": "wnd[0]/usr/ctxtS_HOSP-LOW",
        "high": "wnd[0]/usr/ctxtS_HOSP-HIGH",
    },
    "date_end_service": {  # Data final realització prestac (S_IENDT)
        "low": "wnd[0]/usr/ctxtS_IENDT-LOW",
        "high": "wnd[0]/usr/ctxtS_IENDT-HIGH",
    },
    "client_group": {  # Grup de clients (S_KTOKD)
        "low": "wnd[0]/usr/ctxtS_KTOKD-LOW",
        "high": "wnd[0]/usr/ctxtS_KTOKD-HIGH",
    },
    "client": {  # Client (S_KUNNR)
        "low": "wnd[0]/usr/ctxtS_KUNNR-LOW",
        "high": "wnd[0]/usr/ctxtS_KUNNR-HIGH",
    },
    "activity_no": {  # Num. activitat (S_LNRLS)
        "low": "wnd[0]/usr/txtS_LNRLS-LOW",
        "high": "wnd[0]/usr/txtS_LNRLS-HIGH",
    },
    "billable_concept": {  # Codi concepte facturable (S_MATNR)
        "low": "wnd[0]/usr/ctxtS_MATNR-LOW",
        "high": "wnd[0]/usr/ctxtS_MATNR-HIGH",
    },
    "month": {  # Mes període facturació (S_MES)
        "low": "wnd[0]/usr/ctxtS_MES-LOW",
        "high": "wnd[0]/usr/ctxtS_MES-HIGH",
    },
    "billable_flag": {  # Facturables/no facturables (S_NO_F)
        "low": "wnd[0]/usr/ctxtS_NO_F-LOW",
        "high": "wnd[0]/usr/ctxtS_NO_F-HIGH",
    },
    "factura_no": {  # Núm. factura (S_NUM_F)
        "low": "wnd[0]/usr/txtS_NUM_F-LOW",
        "high": "wnd[0]/usr/txtS_NUM_F-HIGH",
    },
    "requesting_up": {  # UP solicitant (S_ORGZU)
        "low": "wnd[0]/usr/ctxtS_ORGZU-LOW",
        "high": "wnd[0]/usr/ctxtS_ORGZU-HIGH",
    },
    "patient_dni_nie": {  # DNI/NIE pacient (S_PASSNR)
        "low": "wnd[0]/usr/txtS_PASSNR-LOW",
        "high": "wnd[0]/usr/txtS_PASSNR-HIGH",
    },
    "patient_history_no": {  # Núm. Hist. Clínica pacient (S_PATNR)
        "low": "wnd[0]/usr/txtS_PATNR-LOW",
        "high": "wnd[0]/usr/txtS_PATNR-HIGH",
    },
    "date_start_service": {  # Data inici realització prestac (S_PBGDT)
        "low": "wnd[0]/usr/ctxtS_PBGDT-LOW",
        "high": "wnd[0]/usr/ctxtS_PBGDT-HIGH",
    },
    "agenda_code": {  # Codi d’agenda (S_POBNR)
        "low": "wnd[0]/usr/ctxtS_POBNR-LOW",
        "high": "wnd[0]/usr/ctxtS_POBNR-HIGH",
    },
    "prefactura_no": {  # Núm. prefactura (S_PRE_F)
        "low": "wnd[0]/usr/txtS_PRE_F-LOW",
        "high": "wnd[0]/usr/txtS_PRE_F-HIGH",
    },
    "status": {  # Status (S_STATUS)
        "low": "wnd[0]/usr/ctxtS_STATUS-LOW",
        "high": "wnd[0]/usr/ctxtS_STATUS-HIGH",
    },
    "exploration_type": {  # Tipus d’exploració (S_TIP_EX)
        "low": "wnd[0]/usr/ctxtS_TIP_EX-LOW",
        "high": "wnd[0]/usr/ctxtS_TIP_EX-HIGH",
    },
    "billing_ut_ceco": {  # UT de facturació (CECO) (S_UT_FAC)
        "low": "wnd[0]/usr/ctxtS_UT_FAC-LOW",
        "high": "wnd[0]/usr/ctxtS_UT_FAC-HIGH",
    },
    "performing_ut": {  # UT realitzador (S_UT_REA)
        "low": "wnd[0]/usr/ctxtS_UT_REA-LOW",
        "high": "wnd[0]/usr/ctxtS_UT_REA-HIGH",
    },
}


def parse_filter_arg(arg: str) -> Tuple[str, Tuple[Optional[str], Optional[str]]]:
    """Parses a single filter argument like `key=value` or `key=low:high`.

    Returns (key, (low, high)) where high may be None.
    """
    if '=' not in arg:
        raise ValueError("Filter must be in form key=value or key=low:high")
    key, val = arg.split('=', 1)
    if ':' in val:
        low, high = val.split(':', 1)
        return key, (low or None, high or None)
    return key, (val or None, None)


def read_client_list(file_path: str) -> list[str]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)
    clients: list[str] = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            clients.append(line)
    if not clients:
        raise ValueError(f"No clients in {file_path}")
    return clients


class MultiClientExporterV2:
    """Exporter that applies filters using FIELD_MAP.

    If `simulate` is True, SAP interactions are not performed and actions are logged.
    """

    def __init__(self, session=None, config: Optional[dict] = None, simulate: bool = True):
        self.session = session
        self.config = config or {}
        self.simulate = simulate

    def run(self, client_list: list[str], filters: Dict[str, Tuple[Optional[str], Optional[str]]]) -> dict:
        logger.info(f"Running exporter for {len(client_list)} clients (simulate={self.simulate})")
        results = {}
        for i, client in enumerate(client_list, 1):
            logger.info(f"[{i}/{len(client_list)}] {client}")
            # Build a per-client copy of filters so we don't reuse/mutate the same dict
            per_client_filters = dict(filters) if filters is not None else {}
            per_client_filters['client'] = (client, None)

            try:
                ok = self._export_single_client(client, per_client_filters)
                results[client] = {"success": ok, "timestamp": datetime.now().isoformat()}
            except Exception as e:
                logger.exception("Error exporting client %s", client)
                results[client] = {"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}

        successful = sum(1 for r in results.values() if r.get('success'))
        logger.info(f"Summary: {successful} succeeded / {len(results)-successful} failed")
        return results

    def _export_single_client(self, client_code: str, filters: Dict[str, Tuple[Optional[str], Optional[str]]]) -> bool:
        # 1) Navigate to transaction if config provided (optional)
        tcode = self.config.get('sap', {}).get('transaction_code') if self.config else None
        if tcode and not self.simulate:
            self.session.findById("wnd[0]/tbar[0]/okcd").Text = tcode
            self.session.findById("wnd[0]").sendVKey(0)
            time.sleep(self.config.get('timeouts', {}).get('long_wait', 2))

        # 2) Apply filters
        self._apply_filters_by_map(filters)

        # 3) Trigger search / export - real flow
        if self.simulate:
            logger.info(f"Simulated export for client {client_code} with filters: {filters}")
            return True

        try:
            # Execute search
            self.session.findById("wnd[0]/tbar[1]/btn[8]").press()
            time.sleep(self.config.get('timeouts', {}).get('long_wait', 2))

            # Find ALV
            wnd0 = self.session.findById("wnd[0]")
            alv = find_alv_shell(wnd0)
            if not alv:
                logger.warning(f"No ALV found for client {client_code} - possibly no data")
                return False

            # Export via context menu
            try:
                alv.ContextMenu()
                alv.SelectContextMenuItem("&XXL")
            except Exception:
                logger.warning("Could not invoke ALV context menu/export action")

            time.sleep(self.config.get('timeouts', {}).get('default_wait', 0.5))

            # Handle export dialog
            self._handle_export_dialog()

            # Prepare filename and save
            extension = self.config.get('export', {}).get('extension', 'csv')
            prefix = self.config.get('export', {}).get('default_filename_prefix', 'EXPORT')
            export_dir = self.config.get('export', {}).get('default_directory', '.')
            filename = f"{prefix}{client_code}_{datetime.now():%Y%m%d_%H%M%S}.{extension}"
            full_path = os.path.join(export_dir, filename)

            self._handle_save_dialog(export_dir, filename)

            # Handle security popup
            handle_security_popup(self.session)

            # Wait and close Excel workbook
            time.sleep(self.config.get('timeouts', {}).get('long_wait', 2))
            close_excel_workbook(full_path)
            # Attempt to close the SAP results window for this client
            try:
                # Prefer closing a secondary window if present
                try:
                    self.session.findById("wnd[1]").close()
                    logger.debug("Closed SAP results window wnd[1].")
                except Exception:
                    try:
                        self.session.findById("wnd[0]").close()
                        logger.debug("Closed SAP main window wnd[0].")
                    except Exception:
                        try:
                            # As fallback, send a close VKey
                            self.session.findById("wnd[0]").sendVKey(15)
                            logger.debug("Sent close VKey(15) to wnd[0].")
                        except Exception:
                            logger.debug("Could not close any SAP window for this client.")
            except Exception as e:
                logger.warning("Error when attempting to close SAP window: %s", e)

            logger.info(f"Export saved: {filename}")
            return True

        except Exception:
            logger.exception("SAP export failed for %s", client_code)
            return False

    def _handle_export_dialog(self):
        """Mimic the export dialog handling from original exporter."""
        try:
            wnd1 = self.session.findById("wnd[1]")

            # Try to select format combo
            try:
                cmb = wnd1.findById("usr/ssubSUB_CONFIGURATION:SAPLSALV_GUI_CUL_EXPORT_AS:0512/cmbGS_EXPORT-FORMAT")
                export_format = self.config.get('export', {}).get('format', 'csv-LEAN-STANDARD')
                try:
                    cmb.Key = export_format
                    logger.debug("Export format set to: %s", export_format)
                except Exception as fe:
                    logger.warning("Could not set export format %s: %s", export_format, fe)
            except Exception:
                logger.debug("Format combo box not found in export dialog")

            # Press export button - try known buttons
            try:
                wnd1.findById("tbar[0]/btn[20]").press()
            except Exception:
                try:
                    wnd1.findById("tbar[0]/btn[0]").press()
                except Exception:
                    logger.warning("Could not press export button in dialog")

            logger.debug("Export dialog handled")

        except Exception as e:
            logger.error("Error in export dialog: %s", e)
            raise

    def _handle_save_dialog(self, directory: str, filename: str):
        time.sleep(self.config.get('timeouts', {}).get('default_wait', 0.5))
        try:
            wnd1 = self.session.findById("wnd[1]")
            try:
                wnd1.findById("usr/ctxtDY_PATH").Text = directory
            except Exception:
                logger.debug("Save dialog path field not found")
            try:
                wnd1.findById("usr/ctxtDY_FILENAME").Text = filename
            except Exception:
                logger.debug("Save dialog filename field not found")
            try:
                wnd1.findById("tbar[0]/btn[0]").press()
            except Exception:
                logger.debug("Save dialog OK button not found/press failed")
            logger.debug("Save dialog handled")
        except Exception as e:
            logger.error("Error in save dialog: %s", e)
            raise

    def _apply_filters_by_map(self, filters: Dict[str, Tuple[Optional[str], Optional[str]]]):
        """Applies the provided logical filters to the current SAP screen using FIELD_MAP.

        `filters` is a dict: logical_key -> (low, high)
        """
        for logical_key, (low_val, high_val) in filters.items():
            mapping = FIELD_MAP.get(logical_key)
            if not mapping:
                logger.warning("Unknown filter key: %s", logical_key)
                continue

            low_id = mapping.get('low')
            high_id = mapping.get('high')

            try:
                if self.simulate:
                    logger.debug("Simulate set %s = %r", low_id, low_val)
                    logger.debug("Simulate set %s = %r", high_id, high_val)
                else:
                    if low_val is not None and low_id:
                        self.session.findById(low_id).Text = str(low_val)
                    if high_val is not None and high_id:
                        self.session.findById(high_id).Text = str(high_val)
            except Exception as e:
                logger.warning("Could not set filter %s (ids %s/%s): %s", logical_key, low_id, high_id, e)


def build_filters_from_args(filter_args: list[str]) -> Dict[str, Tuple[Optional[str], Optional[str]]]:
    filters: Dict[str, Tuple[Optional[str], Optional[str]]] = {}
    for fa in filter_args:
        key, (low, high) = parse_filter_arg(fa)
        filters[key] = (low, high)
    return filters


def main(argv: Optional[list[str]] = None) -> int:

    p = argparse.ArgumentParser(description="Multi-client export using FIELD_MAP to apply filters")
    p.add_argument("--clients", required=True, help="Path to clients file (one code per line)")
    p.add_argument("--filter", action='append', default=[], help="Filter in form key=value or key=low:high. Repeatable.")
    p.add_argument("--simulate", action='store_true', help="Don't talk to SAP, just simulate actions")
    p.add_argument("--connection-mode", choices=["existing_session", "credentials"], default="existing_session",
                   help="How to obtain SAP session when not simulating")
    p.add_argument("--connection-index", type=int, default=0, help="Connection index for existing session")
    p.add_argument("--session-index", type=int, default=0, help="Session index for existing session")
    p.add_argument("--connection-string", help="Connection string (for credentials mode)")
    p.add_argument("--username", help="Username for credentials mode")
    p.add_argument("--password", help="Password for credentials mode")
    p.add_argument("--client", help="Client (mandante) for credentials mode")
    p.add_argument("--output", help="If provided, write JSON summary to this file")
    p.add_argument("--config", default="config/settings.yaml", help="Path to settings YAML file")
    args = p.parse_args(argv)

    # Load configuration
    config_path = args.config
    config: dict = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as cf:
                config = yaml.safe_load(cf) or {}
            logger.info("Loaded configuration from %s", config_path)
        except Exception as e:
            logger.warning("Could not load config %s: %s", config_path, e)
    else:
        logger.info("Config file not found at %s, using defaults", config_path)

    clients = read_client_list(args.clients)
    filters = build_filters_from_args(args.filter)

    session = None
    sap_conn = None
    if not args.simulate:
        try:
            from src.core.sap_connection import SAPConnection
            # Prefer CLI-specified connection_mode, otherwise use config
            conn_mode = args.connection_mode or config.get('sap', {}).get('connection_mode')

            creds = None
            if conn_mode == 'credentials':
                # precedence: CLI args > secrets.yaml > config
                # Try loading secrets.yaml
                secrets_path = os.path.join(os.path.dirname(config_path), 'secrets.yaml')
                secrets: dict = {}
                if os.path.exists(secrets_path):
                    try:
                        with open(secrets_path, 'r', encoding='utf-8') as sf:
                            secrets = yaml.safe_load(sf) or {}
                        logger.info("Loaded secrets from %s", secrets_path)
                    except Exception as se:
                        logger.warning("Could not load secrets file %s: %s", secrets_path, se)

                # precedence: CLI args > secrets file > config
                username = args.username or secrets.get('sap_credentials', {}).get('username') or config.get('sap', {}).get('username')
                password = args.password or secrets.get('sap_credentials', {}).get('password') or config.get('sap', {}).get('password')
                client_mandt = args.client or secrets.get('sap_credentials', {}).get('client') or config.get('sap', {}).get('client')
                creds = {"username": username, "password": password, "client": client_mandt}

            connection_string = args.connection_string or config.get('sap', {}).get('connection_string')

            sap_conn = SAPConnection(connection_index=args.connection_index,
                                     session_index=args.session_index,
                                     connection_mode=conn_mode,
                                     connection_string=connection_string,
                                     credentials=creds)
            session = sap_conn.connect()
        except Exception as e:
            logger.warning("Could not obtain SAP session (%s). Falling back to simulate. Error: %s", args.connection_mode, e)
            args.simulate = True

    exporter = MultiClientExporterV2(session=session, config=config, simulate=args.simulate)
    results = exporter.run(clients, filters)

    summary = {"generated_at": datetime.now().isoformat(), "results": results}
    out = json.dumps(summary, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(out)
        logger.info("Wrote summary to %s", args.output)
    else:
        print(out)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
