import json
from modules.logger_config import setup_logger


class BarcodeConfig:
    def __init__(self, config_file="C:\\barcode\\barcode.json"):
        self.config_file = config_file
        self.logger = setup_logger("Configuration")
        self._load_config()

    def _load_config(self):
        """Load the configuration from the JSON file."""
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
                self.logger.info("Configuration loaded successfully.")
        except FileNotFoundError:
            self.logger.warning("Configuration file not found. Starting with an empty configuration.")
            self.config = {}
        except json.JSONDecodeError:
            self.logger.error("Error parsing configuration file. Starting with an empty configuration.")
            self.config = {}

    def _save_config(self):
        """Save the current configuration to the JSON file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
                self.logger.info("Configuration saved successfully.")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")

    # Generalized Getters and Setters
    def _get_value(self, key, default=None):
        value = self.config.get(key, default)
        self.logger.debug(f"Retrieved '{key}': {value}")
        return value

    def _set_value(self, key, value):
        self.logger.info(f"Setting '{key}' to: {value}")
        self.config[key] = value
        self._save_config()

    # Specific Getters and Setters
    def get_server(self):
        return self._get_value("server", "localhost")

    def set_server(self, server):
        self._set_value("server", server)

    def get_database(self):
        return self._get_value("database", "example_db")

    def set_database(self, database):
        self._set_value("database", database)

    def get_username(self):
        return self._get_value("username", "admin")

    def set_username(self, username):
        self._set_value("username", username)

    def get_password(self):
        return self._get_value("password", "admin123")

    def set_password(self, password):
        self._set_value("password", password)

    def get_vid(self):
        return self._get_value("vid", "0x1234")

    def set_vid(self, vid):
        self._set_value("vid", vid)

    def get_pid(self):
        return self._get_value("pid", "0x5678")

    def set_pid(self, pid):
        self._set_value("pid", pid)

    def get_endpoint(self):
        return self._get_value("endpoint", "0x01")

    def set_endpoint(self, endpoint):
        self._set_value("endpoint", endpoint)

    def get_company_name(self):
        return self._get_value("companyName", "Example Corp")

    def set_company_name(self, company_name):
        self._set_value("companyName", company_name)

    def get_location(self):
        return self._get_value("location", "HQ")

    def set_location(self, location):
        self._set_value("location", location)

    def get_use_zpl(self):
        return self._get_value("useZPL", True)

    def set_use_zpl(self, use_zpl):
        self._set_value("useZPL", use_zpl)

    def get_ip_address(self):
        return self._get_value("ip_address", "192.168.1.100")

    def set_ip_address(self, ip_address):
        self._set_value("ip_address", ip_address)

    def get_wireless_mode(self):
        return self._get_value("wireless_mode", False)

    def set_wireless_mode(self, wireless_mode):
        self._set_value("wireless_mode", wireless_mode)

    def get_zpl_template(self):
        return self._get_value("zplTemplate", "")

    def set_zpl_template(self, zpl_template):
        self._set_value("zplTemplate", zpl_template)

    def get_tpsl_template(self):
        return self._get_value("tpslTemplate", "")

    def set_tpsl_template(self, tpsl_template):
        self._set_value("tpslTemplate", tpsl_template)

    def get_logging(self):
        return self._get_value("logging", True)

    def set_logging(self, logging):
        self._set_value("logging", logging)

    def get_item_count(self):
        return self._get_value("itemCount", 100)

    def set_item_count(self, item_count):
        self._set_value("itemCount", item_count)

    def get_enter_to_search(self):
        return self._get_value("enterToSearch", True)

    def set_enter_to_search(self, enter_to_search):
        self._set_value("enterToSearch", enter_to_search)

    def get_use_generic_driver(self):
        return self._get_value("useGenericDriver", True)

    def set_use_generic_driver(self, use_generic_driver):
        self._set_value("useGenericDriver", use_generic_driver)

    def get_printer_name(self):
        return self._get_value("printerName", "Default Printer")

    def set_printer_name(self, printer_name):
        self._set_value("printerName", printer_name)

    def get_database_driver_name(self):
        return self._get_value("databaseDriverName", "ODBC Driver 18 for SQL Server")

    def set_database_driver_name(self, database_driver_name):
        self._set_value("databaseDriverName", database_driver_name)
