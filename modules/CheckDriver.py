import winreg
from logger_config import setup_logger

class CheckDrivers:
    def __init__(self):
        self.logger = setup_logger("CheckDrivers")
        self.logger.info("Initializing CheckDrivers")

    def check_printer_driver(self, printer_name):
        self.logger.info(f"Checking if printer driver is installed for '{printer_name}'")
        try:
            reg_path = r"SYSTEM\CurrentControlSet\Control\Print\Printers"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                for i in range(0, winreg.QueryInfoKey(key)[0]):  # Enumerate installed printers
                    installed_printer = winreg.EnumKey(key, i)
                    self.logger.debug(f"Found installed printer: {installed_printer}")
                    if printer_name.lower() == installed_printer.lower():
                        self.logger.info(f"Printer '{printer_name}' driver is installed.")
                        return True
            self.logger.warning(f"Printer '{printer_name}' driver is not installed.")
            return False
        except FileNotFoundError:
            self.logger.error("No printers found in the registry.")
            return False
        except Exception as e:
            self.logger.exception(f"Error checking printer driver: {e}")
            return False

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

