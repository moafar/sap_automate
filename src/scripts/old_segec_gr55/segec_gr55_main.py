
import os
import sys
import yaml
# Permitir imports desde cualquier ubicación
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from src.core.sap_connection import SAPConnection
from segec_gr55 import SegecGR55
from src.utils.logger import setup_logger

def load_global_config():
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../config/settings.yaml'))
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_local_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():

    logger = setup_logger()
    global_config = load_global_config()
    local_config = load_local_config()

    # Obtener modo de conexión y parámetros globales
    sap_cfg = global_config.get('sap', {})
    # Forzar modo sesión existente
    connection_mode = 'existing_session'
    logger.info(f"Connection mode: {connection_mode}")

    # Conectar a SAP
    try:
        if connection_mode == "existing_session":
            sap_conn = SAPConnection(
                connection_index=sap_cfg.get('connection_index', 0),
                session_index=sap_cfg.get('session_index', 0),
                connection_mode="existing_session"
            )
            session = sap_conn.connect()
        elif connection_mode == "credentials":
            from src.utils.credential_manager import get_credentials, validate_credentials
            credentials = get_credentials(use_keyring=True)
            if not validate_credentials(credentials, require_all=False):
                logger.critical("Invalid or missing credentials.")
                sys.exit(1)
            connection_string = sap_cfg.get('connection_string')
            if not connection_string:
                logger.critical("connection_string not found in config for credentials mode")
                sys.exit(1)
            sap_conn = SAPConnection(
                connection_mode="credentials",
                connection_string=connection_string,
                credentials=credentials
            )
            session = sap_conn.connect()
        else:
            logger.critical(f"Invalid connection_mode in config: {connection_mode}")
            sys.exit(1)
    except Exception as e:
        logger.critical(f"Could not connect to SAP: {e}")
        sys.exit(1)

    # Mostrar configuración (solo informativo, sin confirmación)
    print("\nConfiguración para SEGEC GR55:")
    try:
        import yaml as _yaml
        print(_yaml.dump(local_config, allow_unicode=True, sort_keys=False))
    except Exception:
        import pprint
        pprint.pprint(local_config)

    # Extraer configuración específica para el script
    segec_cfg = local_config.get('segec_gr55', {})

    # Log de la configuración completa y específica para depuración
    print("\n[DEBUG] local_config cargado:")
    try:
        import yaml as _yaml
        print(_yaml.dump(local_config, allow_unicode=True, sort_keys=False))
    except Exception:
        import pprint
        pprint.pprint(local_config)

    print("\n[DEBUG] segec_cfg extraído:")
    try:
        print(_yaml.dump(segec_cfg, allow_unicode=True, sort_keys=False))
    except Exception:
        pprint.pprint(segec_cfg)

    # Ejecutar el script principal
    script = SegecGR55(session, local_config)
    success = script.run(segec_cfg)
    if success:
        logger.info("Script SEGEC GR55 ejecutado correctamente.")
    else:
        logger.error("Error en la ejecución de SEGEC GR55.")
        sys.exit(1)

    # Cleanup
    try:
        if connection_mode == "credentials":
            sap_conn.disconnect()
    except Exception as e:
        logger.warning(f"Error durante la limpieza: {e}")

if __name__ == "__main__":
    main()
