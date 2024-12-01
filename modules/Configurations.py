import json

class BarcodeConfig:
    def __init__(self, config_file="C:\\barcode\\barcode.json"):
        self.config_file = config_file
        self._load_config()

    def _load_config(self):
        """Load the configuration from the JSON file."""
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = {}  # In case the file is missing or invalid

    def _save_config(self):
        """Save the current configuration to the JSON file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    # Getters and Setters
    def get_server(self):
        return self.config.get("server", "localhost")

    def set_server(self, server):
        self.config["server"] = server
        self._save_config()

    def get_database(self):
        return self.config.get("database", "example_db")

    def set_database(self, database):
        self.config["database"] = database
        self._save_config()

    def get_username(self):
        return self.config.get("username", "admin")

    def set_username(self, username):
        self.config["username"] = username
        self._save_config()

    def get_password(self):
        return self.config.get("password", "admin123")

    def set_password(self, password):
        self.config["password"] = password
        self._save_config()

    def get_vid(self):
        return self.config.get("vid", "0x1234")

    def set_vid(self, vid):
        self.config["vid"] = vid
        self._save_config()

    def get_pid(self):
        return self.config.get("pid", "0x5678")

    def set_pid(self, pid):
        self.config["pid"] = pid
        self._save_config()

    def get_endpoint(self):
        return self.config.get("endpoint", "0x01")

    def set_endpoint(self, endpoint):
        self.config["endpoint"] = endpoint
        self._save_config()

    def get_company_name(self):
        return self.config.get("companyName", "Example Corp")

    def set_company_name(self, company_name):
        self.config["companyName"] = company_name
        self._save_config()

    def get_location(self):
        return self.config.get("location", "HQ")

    def set_location(self, location):
        self.config["location"] = location
        self._save_config()

    def get_use_zpl(self):
        return self.config.get("useZPL", True)

    def set_use_zpl(self, use_zpl):
        self.config["useZPL"] = use_zpl
        self._save_config()

    def get_ip_address(self):
        return self.config.get("ip_address", "192.168.1.100")

    def set_ip_address(self, ip_address):
        self.config["ip_address"] = ip_address
        self._save_config()

    def get_wireless_mode(self):
        return self.config.get("wireless_mode", False)

    def set_wireless_mode(self, wireless_mode):
        self.config["wireless_mode"] = wireless_mode
        self._save_config()

    def get_zpl_template(self):
        return self.config.get("zplTemplate", "")

    def set_zpl_template(self, zpl_template):
        self.config["zplTemplate"] = zpl_template
        self._save_config()

    def get_tpsl_template(self):
        return self.config.get("tpslTemplate", "")

    def set_tpsl_template(self, tpsl_template):
        self.config["tpslTemplate"] = tpsl_template
        self._save_config()

    def get_logging(self):
        return self.config.get("logging", True)

    def set_logging(self, logging):
        self.config["logging"] = logging
        self._save_config()

    def get_item_count(self):
        return self.config.get("itemCount", 100)

    def set_item_count(self, item_count):
        self.config["itemCount"] = item_count
        self._save_config()

    def get_enter_to_search(self):
        return self.config.get("enterToSearch", True)

    def set_enter_to_search(self, enter_to_search):
        self.config["enterToSearch"] = enter_to_search
        self._save_config()

    def get_use_generic_driver(self):
        return self.config.get("useGenericDriver", True)

    def set_use_generic_driver(self, use_generic_driver):
        self.config["useGenericDriver"] = use_generic_driver
        self._save_config()


# Example usage:
if __name__ == "__main__":
    config = BarcodeConfig()

    # Get some values
    print(config.get_server())  # Get the server
    print(config.get_database())  # Get the database

    # Set some values
    config.set_server("new_server")
    config.set_database("new_database")
