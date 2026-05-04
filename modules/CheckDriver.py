import winreg
from modules.logger_config import setup_logger

class CheckDrivers:
    def __init__(self):
        self.logger = setup_logger("CheckDrivers")
        self.logger.info("Initializing CheckDrivers")

    def check_printer_driver(self):
        """
        Check for installed printer drivers and return status and printer list.

        Returns:
            tuple: (bool, list)
                - bool: True if printers are found, False otherwise.
                - list: List of printer names if available, empty list otherwise.
        """
        self.logger.info("Checking for installed printer drivers.")
        printers = []
        try:
            reg_path = r"SYSTEM\CurrentControlSet\Control\Print\Printers"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                # Enumerate installed printers
                for i in range(0, winreg.QueryInfoKey(key)[0]):
                    installed_printer = winreg.EnumKey(key, i)
                    printers.append(installed_printer)
                    self.logger.debug(f"Found installed printer: {installed_printer}")

            if printers:
                self.logger.info(f"Printers found: {printers}")
                return True, printers
            else:
                self.logger.warning("No printers found in the registry.")
                return False, []

        except FileNotFoundError:
            self.logger.error("No printers found in the registry path.")
            return False, []

        except Exception as e:
            self.logger.exception(f"Error checking printer drivers: {e}")
            return False, []

    def check_odbc_driver(self, driver_name):
        self.logger.info(f"Checking for ODBC driver '{driver_name}'")
        odbc_inst_ini_path = r"SOFTWARE\ODBC\ODBCINST.INI"
        driver_key_path = f"{odbc_inst_ini_path}\\{driver_name}"

        try:
            reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, driver_key_path)
            self.logger.info(f"ODBC driver '{driver_name}' found in registry.")

            driver_details = {}
            i = 0
            while True:
                try:
                    value_name, value_data, _ = winreg.EnumValue(reg_key, i)
                    driver_details[value_name] = value_data
                    self.logger.debug(f"Found registry entry: {value_name} = {value_data}")
                    i += 1
                except OSError:  # No more values
                    self.logger.debug("All registry entries fetched for ODBC driver.")
                    break
            winreg.CloseKey(reg_key)

            self.logger.info(f"Driver '{driver_name}' details fetched successfully.")
            return True, driver_details

        except FileNotFoundError:
            self.logger.warning(f"ODBC driver '{driver_name}' not found in the registry.")
            return False, "-1"
        except Exception as e:
            self.logger.exception(f"Error checking ODBC driver '{driver_name}': {e}")
            return False, "-1"

    def get_installed_odbc_drivers(self):
        """Lists all installed ODBC drivers from the registry."""
        self.logger.info("Listing all installed ODBC drivers.")
        drivers = []
        try:
            reg_path = r"SOFTWARE\ODBC\ODBCINST.INI\ODBC Drivers"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                for i in range(0, winreg.QueryInfoKey(key)[1]):
                    driver_name, _, _ = winreg.EnumValue(key, i)
                    drivers.append(driver_name)
            return drivers
        except Exception as e:
            self.logger.error(f"Error listing ODBC drivers: {e}")
            return []

    def find_best_sql_driver(self):
        """Finds the most recent SQL Server ODBC driver installed."""
        installed = self.get_installed_odbc_drivers()
        # Order of preference (Newest to Oldest)
        candidates = [
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
            "ODBC Driver 13 for SQL Server",
            "ODBC Driver 11 for SQL Server",
            "SQL Server Native Client 11.0",
            "SQL Server"
        ]
        for candidate in candidates:
            if candidate in installed:
                self.logger.info(f"Auto-detected best driver: {candidate}")
                return candidate
        
        # Fallback: find any driver containing "SQL Server"
        for driver in installed:
            if "SQL Server" in driver:
                return driver
        
        return None
