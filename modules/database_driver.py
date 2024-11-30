import winreg

def get_odbc_driver_details(driver_name=None):
    try:
        # Registry paths for ODBC drivers
        odbc_inst_ini_path = r"SOFTWARE\ODBC\ODBCINST.INI"
        odbc_drivers_path = odbc_inst_ini_path + r"\ODBC Drivers"

        drivers = {}
        reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, odbc_drivers_path)
        i = 0

        # List all drivers
        while True:
            try:
                driver = winreg.EnumValue(reg_key, i)[0]
                drivers[driver] = {}
                i += 1
            except OSError:
                break
        winreg.CloseKey(reg_key)

        # Get details for each driver
        for driver in drivers:
            if driver_name and driver != driver_name:
                continue  # Skip if filtering for a specific driver
            driver_key_path = f"{odbc_inst_ini_path}\\{driver}"
            try:
                reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, driver_key_path)
                j = 0
                while True:
                    try:
                        value_name, value_data, _ = winreg.EnumValue(reg_key, j)
                        drivers[driver][value_name] = value_data
                        j += 1
                    except OSError:
                        break
                winreg.CloseKey(reg_key)
            except FileNotFoundError:
                drivers[driver] = "Details not found in registry."

        # Print driver details
        for driver, details in drivers.items():
            print(f"Driver Name: {driver}")
            if isinstance(details, dict):
                for key, value in details.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {details}")
            print("-" * 50)

    except Exception as e:
        print(f"Error retrieving ODBC driver details: {e}")

# Example Usage
# Get all drivers' details
get_odbc_driver_details()

# Get details for a specific driver
get_odbc_driver_details("ODBC Driver")
