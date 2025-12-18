import logging
import os
import yaml

def setup_logger(config_path="config/settings.yaml"):
    """
    Sets up the logger based on the configuration file.
    """
    # Default config
    log_level = logging.INFO
    log_file = "logs/app.log"
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            if config and "logging" in config:
                log_config = config["logging"]
                level_str = log_config.get("level", "INFO").upper()
                log_level = getattr(logging, level_str, logging.INFO)
                log_file = log_config.get("file", log_file)
                log_format = log_config.get("format", log_format)
    except Exception as e:
        print(f"Warning: Could not load logging config from {config_path}: {e}")

    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger("SAP_Automation")
