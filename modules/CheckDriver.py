import winreg

class CheckDrivers():
    def __init__(self):
        pass

    def check_printer_driver(self, printer_name):
        try:
            # Access the registry key for printers
            reg_path = r"SYSTEM\CurrentControlSet\Control\Print\Printers"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                # Check if the printer name exists
                for i in range(0, winreg.QueryInfoKey(key)[0]):
                    installed_printer = winreg.EnumKey(key, i)
                    if printer_name.lower() == installed_printer.lower():
                        print(f"Printer '{printer_name}' driver is installed.")
                        return True
            return False
        except FileNotFoundError:
            print("No printers found in the registry.")
            return False
        except Exception as e:
            print(f"Error checking printer driver: {e}")
            return False
        
    def check_odbc_driver(self, driver_name):
        odbc_inst_ini_path = r"SOFTWARE\ODBC\ODBCINST.INI"

        try:
            # Open the registry key for the specific driver
            driver_key_path = f"{odbc_inst_ini_path}\\{driver_name}"
            reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, driver_key_path)

            # Fetch and print all values associated with the driver
            driver_details = {}
            i = 0
            while True:
                try:
                    value_name, value_data, _ = winreg.EnumValue(reg_key, i)
                    driver_details[value_name] = value_data
                    i += 1
                except OSError:  # No more values
                    break
            winreg.CloseKey(reg_key)

            # Print driver details
            print(f"Driver '{driver_name}' found with the following details:")
            return driver_details

        except FileNotFoundError:
            print(f"Driver '{driver_name}' not found in the registry.")
        except Exception as e:
            print(f"Error checking driver: {e}")
