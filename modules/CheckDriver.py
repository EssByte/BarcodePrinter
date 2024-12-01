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

