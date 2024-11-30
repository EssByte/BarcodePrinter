import winreg

def check_printer_driver(printer_name):
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

# Example usage
printer_name = "TSC_TA200"
if check_printer_driver(printer_name):
    print(f"The driver for '{printer_name}' is installed.")
else:
    print(f"The driver for '{printer_name}' is not installed.")
