import argparse
import yaml
import sys
import os
from src.utils.logger import setup_logger
from src.core.sap_connection import SAPConnection
from src.scripts.export_invoice import InvoiceExporter
from src.scripts.export_multi_client import MultiClientExporter

def load_config(config_path="config/settings.yaml"):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    # Setup Logger
    logger = setup_logger()
    
    # Parse Args
    parser = argparse.ArgumentParser(description="SAP Automation Scripts")
    parser.add_argument("--task", type=str, required=True, 
                        choices=["export_invoice", "export_multi_client"], 
                        help="Task to run")
    
    # Export Invoice arguments
    parser.add_argument("--invoice", type=str, help="Invoice number for export task")
    
    # Export Multi-Client arguments
    parser.add_argument("--clients-file", type=str, 
                        help="Path to file with client codes (one per line)")
    parser.add_argument("--month-from", type=int, default=1, 
                        help="Start month for billing period (default: 1)")
    parser.add_argument("--month-to", type=int, default=10, 
                        help="End month for billing period (default: 10)")
    parser.add_argument("--year", type=int, default=2025, 
                        help="Billing year (default: 2025)")
    parser.add_argument("--status", type=str, default="F", 
                        help="Billing status (default: F)")
    args = parser.parse_args()

    # Load Config
    try:
        config = load_config()
    except Exception as e:
        logger.critical(f"Failed to load config: {e}")
        sys.exit(1)

    # Get connection mode from config
    connection_mode = config['sap'].get('connection_mode', 'existing_session')
    logger.info(f"Connection mode: {connection_mode}")

    # Connect to SAP based on mode
    try:
        if connection_mode == "existing_session":
            # Connect to existing open session (default behavior)
            sap_conn = SAPConnection(
                connection_index=config['sap']['connection_index'],
                session_index=config['sap']['session_index'],
                connection_mode="existing_session"
            )
            session = sap_conn.connect()
            
        elif connection_mode == "credentials":
            # Login using credentials (lazy import)
            try:
                from src.utils.credential_manager import get_credentials, validate_credentials
            except ImportError as e:
                logger.critical("Credentials mode requires additional dependencies.")
                logger.critical("Install with: pip install python-dotenv keyring")
                sys.exit(1)
            
            logger.info("Loading credentials from credential manager...")
            credentials = get_credentials(use_keyring=True)
            
            # Validate credentials
            if not validate_credentials(credentials, require_all=False):
                logger.critical("Invalid or missing credentials. Please configure credentials using:")
                logger.critical("  python -m src.utils.credential_manager set --username USER --password PASS --client 100 --system-id SYS")
                sys.exit(1)
            
            # Get connection string from config
            connection_string = config['sap'].get('connection_string')
            if not connection_string:
                logger.critical("connection_string not found in config for credentials mode")
                logger.critical("Add 'connection_string' to config/settings.yaml under 'sap' section")
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

    # Dispatch Task
    if args.task == "export_invoice":
        if not args.invoice:
            logger.error("Invoice number is required for export_invoice task.")
            sys.exit(1)
        
        exporter = InvoiceExporter(session, config)
        success = exporter.run(args.invoice)
        if success:
            logger.info("Task finished successfully.")
        else:
            logger.error("Task failed.")
            sys.exit(1)
    
    elif args.task == "export_multi_client":
        if not args.clients_file:
            logger.error("Client list file is required for export_multi_client task.")
            logger.error("Usage: --task export_multi_client --clients-file config/clients.txt")
            sys.exit(1)
        
        # Import the helper function
        from src.scripts.export_multi_client import read_client_list
        
        # Read client list from file
        try:
            client_list = read_client_list(args.clients_file)
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"Error reading client list: {e}")
            sys.exit(1)
        
        logger.info(f"Processing {len(client_list)} clients from {args.clients_file}")
        
        # Create exporter and run
        exporter = MultiClientExporter(session, config)
        results = exporter.run(
            client_list=client_list,
            month_from=args.month_from,
            month_to=args.month_to,
            year=args.year,
            status=args.status
        )
        
        # Check overall success
        failed_clients = [k for k, v in results.items() if not v["success"]]
        if not failed_clients:
            logger.info("All clients exported successfully.")
        else:
            logger.warning(f"Some clients failed: {failed_clients}")
            sys.exit(1)

    # Cleanup (disconnect if using credentials mode)
    try:
        if connection_mode == "credentials":
            sap_conn.disconnect()
    except Exception as e:
        logger.warning(f"Error during cleanup: {e}")

if __name__ == "__main__":
    main()
