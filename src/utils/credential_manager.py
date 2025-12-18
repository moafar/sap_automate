"""
Credential Manager
==================
Gestión segura de credenciales SAP usando variables de entorno y keyring del sistema.

Uso:
    from src.utils.credential_manager import get_credentials, set_credentials
    
    # Obtener credenciales
    creds = get_credentials()
    
    # Establecer credenciales en keyring
    set_credentials(username="user", password="pass", client="100", system_id="DEV")
"""

import os
import logging
from typing import Optional, Dict

logger = logging.getLogger("SAP_Automation")

# Intentar importar dotenv (opcional)
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    logger.debug("python-dotenv module not available. Using only secrets.yaml or keyring for credentials.")

# Intentar importar keyring (opcional)
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    logger.debug("keyring module not available. Using only secrets.yaml or environment variables for credentials.")


# Constantes para keyring
KEYRING_SERVICE_NAME = "SAP_Automation"
KEYRING_USERNAME_KEY = "sap_username"
KEYRING_PASSWORD_KEY = "sap_password"
KEYRING_CLIENT_KEY = "sap_client"
KEYRING_SYSTEM_KEY = "sap_system_id"


def load_env_file(env_path: str = ".env") -> None:
    """
    Carga variables de entorno desde archivo .env
    
    Args:
        env_path: Ruta al archivo .env (default: ".env" en directorio actual)
    """
    if not DOTENV_AVAILABLE:
        logger.debug("dotenv not available, skipping .env file loading")
        return
        
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger.debug(f"Loaded environment variables from {env_path}")
    else:
        logger.debug(f"No .env file found at {env_path}")


def get_credentials(use_keyring: bool = False, env_path: str = ".env", secrets_path: str = "config/secrets.yaml") -> Dict[str, Optional[str]]:
    """
    Obtiene credenciales SAP desde archivo secrets.yaml, variables de entorno o keyring.
    
    Orden de prioridad:
    1. Archivo secrets.yaml (más simple para desarrollo)
    2. Variables de entorno (SAP_USERNAME, SAP_PASSWORD, SAP_CLIENT, SAP_SYSTEM_ID)
    3. Keyring del sistema (si está disponible y use_keyring=True)
    
    Args:
        use_keyring: Si True, intenta obtener credenciales del keyring si no están en otros lugares
        env_path: Ruta al archivo .env a cargar
        secrets_path: Ruta al archivo secrets.yaml
        
    Returns:
        Diccionario con claves: username, password, client, system_id, language
        Los valores pueden ser None si no se encuentran
    """
    import yaml
    
    credentials = {
        "username": None,
        "password": None,
        "client": None,
        "system_id": None,
        "language": None
    }
    
    # 1. Intentar leer desde secrets.yaml primero (más simple)
    if os.path.exists(secrets_path):
        try:
            with open(secrets_path, 'r', encoding='utf-8') as f:
                secrets_data = yaml.safe_load(f)
                if secrets_data and 'sap_credentials' in secrets_data:
                    creds = secrets_data['sap_credentials']
                    credentials["username"] = creds.get("username") or None
                    credentials["password"] = creds.get("password") or None
                    credentials["client"] = creds.get("client") or None
                    credentials["system_id"] = creds.get("system_id") or None
                    credentials["language"] = creds.get("language") or None
                    logger.debug(f"Credentials loaded from {secrets_path}")
        except Exception as e:
            logger.warning(f"Could not load credentials from {secrets_path}: {e}")
    
    # 2. Si falta algo, intentar desde variables de entorno
    load_env_file(env_path)
    
    if not credentials["username"]:
        credentials["username"] = os.getenv("SAP_USERNAME")
    if not credentials["password"]:
        credentials["password"] = os.getenv("SAP_PASSWORD")
    if not credentials["client"]:
        credentials["client"] = os.getenv("SAP_CLIENT")
    if not credentials["system_id"]:
        credentials["system_id"] = os.getenv("SAP_SYSTEM_ID")
    if not credentials["language"]:
        credentials["language"] = os.getenv("SAP_LANGUAGE")
    
    # 3. Si aún falta algo y keyring está disponible, intentar desde keyring
    if use_keyring and KEYRING_AVAILABLE:
        if not credentials["username"]:
            try:
                credentials["username"] = keyring.get_password(KEYRING_SERVICE_NAME, KEYRING_USERNAME_KEY)
            except Exception as e:
                logger.debug(f"Could not retrieve username from keyring: {e}")
        
        if not credentials["password"]:
            try:
                credentials["password"] = keyring.get_password(KEYRING_SERVICE_NAME, KEYRING_PASSWORD_KEY)
            except Exception as e:
                logger.debug(f"Could not retrieve password from keyring: {e}")
        
        if not credentials["client"]:
            try:
                credentials["client"] = keyring.get_password(KEYRING_SERVICE_NAME, KEYRING_CLIENT_KEY)
            except Exception as e:
                logger.debug(f"Could not retrieve client from keyring: {e}")
        
        if not credentials["system_id"]:
            try:
                credentials["system_id"] = keyring.get_password(KEYRING_SERVICE_NAME, KEYRING_SYSTEM_KEY)
            except Exception as e:
                logger.debug(f"Could not retrieve system_id from keyring: {e}")
    
    return credentials


def set_credentials(username: str, password: str, client: str, system_id: str) -> bool:
    """
    Almacena credenciales SAP en el keyring del sistema.
    
    Args:
        username: Nombre de usuario SAP
        password: Contraseña SAP
        client: Mandante SAP
        system_id: ID del sistema SAP
        
    Returns:
        True si se almacenaron correctamente, False en caso contrario
    """
    if not KEYRING_AVAILABLE:
        logger.error("keyring module not available. Cannot store credentials securely.")
        logger.info("Please install keyring: pip install keyring")
        return False
    
    try:
        keyring.set_password(KEYRING_SERVICE_NAME, KEYRING_USERNAME_KEY, username)
        keyring.set_password(KEYRING_SERVICE_NAME, KEYRING_PASSWORD_KEY, password)
        keyring.set_password(KEYRING_SERVICE_NAME, KEYRING_CLIENT_KEY, client)
        keyring.set_password(KEYRING_SERVICE_NAME, KEYRING_SYSTEM_KEY, system_id)
        logger.info("Credentials stored successfully in system keyring.")
        return True
    except Exception as e:
        logger.error(f"Failed to store credentials in keyring: {e}")
        return False


def delete_credentials() -> bool:
    """
    Elimina credenciales almacenadas en el keyring del sistema.
    
    Returns:
        True si se eliminaron correctamente, False en caso contrario
    """
    if not KEYRING_AVAILABLE:
        logger.error("keyring module not available.")
        return False
    
    try:
        keyring.delete_password(KEYRING_SERVICE_NAME, KEYRING_USERNAME_KEY)
        keyring.delete_password(KEYRING_SERVICE_NAME, KEYRING_PASSWORD_KEY)
        keyring.delete_password(KEYRING_SERVICE_NAME, KEYRING_CLIENT_KEY)
        keyring.delete_password(KEYRING_SERVICE_NAME, KEYRING_SYSTEM_KEY)
        logger.info("Credentials deleted from system keyring.")
        return True
    except Exception as e:
        logger.error(f"Failed to delete credentials from keyring: {e}")
        return False


def validate_credentials(credentials: Dict[str, Optional[str]], require_all: bool = True) -> bool:
    """
    Valida que las credenciales estén presentes.
    
    Args:
        credentials: Diccionario de credenciales
        require_all: Si True, requiere que todas las credenciales estén presentes
        
    Returns:
        True si las credenciales son válidas, False en caso contrario
    """
    required_keys = ["username", "password"]
    optional_keys = ["client", "system_id"]
    
    # Verificar claves requeridas
    for key in required_keys:
        if not credentials.get(key):
            logger.error(f"Missing required credential: {key}")
            return False
    
    # Verificar claves opcionales si require_all=True
    if require_all:
        for key in optional_keys:
            if not credentials.get(key):
                logger.warning(f"Missing optional credential: {key}")
    
    return True


# Función de utilidad para uso en scripts
def main():
    """Función principal para gestionar credenciales desde línea de comandos."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gestión de credenciales SAP")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")
    
    # Comando: set
    set_parser = subparsers.add_parser("set", help="Almacenar credenciales en keyring")
    set_parser.add_argument("--username", required=True, help="Nombre de usuario SAP")
    set_parser.add_argument("--password", required=True, help="Contraseña SAP")
    set_parser.add_argument("--client", required=True, help="Mandante SAP")
    set_parser.add_argument("--system-id", required=True, help="ID del sistema SAP")
    
    # Comando: get
    subparsers.add_parser("get", help="Obtener credenciales (sin mostrar password)")
    
    # Comando: delete
    subparsers.add_parser("delete", help="Eliminar credenciales del keyring")
    
    args = parser.parse_args()
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    if args.command == "set":
        success = set_credentials(
            username=args.username,
            password=args.password,
            client=args.client,
            system_id=args.system_id
        )
        if success:
            print("✓ Credenciales almacenadas correctamente")
        else:
            print("✗ Error al almacenar credenciales")
            
    elif args.command == "get":
        creds = get_credentials(use_keyring=True)
        print("\nCredenciales encontradas:")
        print(f"  Username:  {creds.get('username') or '(no encontrado)'}")
        print(f"  Password:  {'***' if creds.get('password') else '(no encontrado)'}")
        print(f"  Client:    {creds.get('client') or '(no encontrado)'}")
        print(f"  System ID: {creds.get('system_id') or '(no encontrado)'}")
        
    elif args.command == "delete":
        success = delete_credentials()
        if success:
            print("✓ Credenciales eliminadas correctamente")
        else:
            print("✗ Error al eliminar credenciales")
            
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
