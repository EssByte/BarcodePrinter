import subprocess
import os
from modules.logger_config import setup_logger

class DriverInstaller:
    def __init__(self):
        self.logger = setup_logger("DriverInstaller")
        self.logger.info("DriverInstaller initialized.")

    def install_driver(self, package_path, silent=True):
        """
        Installs a driver from the given MSI or EXE package.

        Args:
            package_path (str): Full path to the driver package (MSI or EXE).
            silent (bool): Whether to perform the installation silently.

        Returns:
            bool: True if the installation succeeded, False otherwise.
        """
        try:
            if not os.path.isfile(package_path):
                self.logger.error(f"Driver package not found: {package_path}")
                raise FileNotFoundError(f"Package not found: {package_path}")

            # Determine file extension and construct the appropriate command
            _, ext = os.path.splitext(package_path.lower())
            if ext == ".msi":
                cmd = ["msiexec", "/i", package_path]
                if silent:
                    cmd.extend(["/quiet", "/norestart"])
            elif ext == ".exe":
                cmd = [package_path]
                if silent:
                    cmd.extend(["/silent", "/norestart"])
            else:
                self.logger.error(f"Unsupported package type: {ext}")
                raise ValueError(f"Unsupported package type: {ext}")

            # Log the command to be executed
            self.logger.info(f"Executing installation command: {' '.join(cmd)}")

            # Run the command
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Log the output and errors
            if result.returncode == 0:
                self.logger.info("Driver installation completed successfully.")
                return True
            else:
                self.logger.error(f"Driver installation failed with error: {result.stderr.strip()}")
                return False

        except FileNotFoundError as e:
            self.logger.exception(f"File error: {e}")
        except ValueError as e:
            self.logger.exception(f"Value error: {e}")
        except Exception as e:
            self.logger.exception(f"Unexpected error during installation: {e}")

        return False


# Example usage
if __name__ == "__main__":
    installer = DriverInstaller()
    package_path = r"C:\path\to\driver.msi"  # Replace with your actual MSI/EXE path
    success = installer.install_driver(package_path)
    if success:
        print("Driver installed successfully.")
    else:
        print("Driver installation failed.")
