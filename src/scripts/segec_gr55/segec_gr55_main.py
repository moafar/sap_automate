import os
import sys
import yaml

# Permitir imports desde cualquier ubicación
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.core.sap_connection import SAPConnection
from src.utils.logger import setup_logger
from segec_gr55 import SegecGR55


def load_global_config():
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../config/settings.yaml'))
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main():
    logger = setup_logger()
    global_config = load_global_config()

    sap_cfg = global_config.get('sap', {})
    connection_mode = 'existing_session'
    logger.info(f"Connection mode: {connection_mode}")

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

    script = SegecGR55(session, global_config)
    success = script.run()

    if success:
        logger.info("Script SEGEC GR55 ejecutado correctamente.")
    else:
        logger.error("Error en la ejecución de SEGEC GR55.")
        sys.exit(1)


if __name__ == "__main__":
    main()
