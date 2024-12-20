import os
import shutil
import sys
import ctypes
import requests  # To download files from GitHub
from PyQt5.QtWidgets import QApplication, QWizard, QFileDialog, QMessageBox, QLabel
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5 import uic
import win32com.client  # For creating desktop shortcuts


class InstallerWizard(QWizard):
    def __init__(self):
        super().__init__()
        uic.loadUi(self.resource_path("qwizard.ui"), self)  # Load the .ui file

        # GitHub file URLs (Replace these with your actual URLs)
        self.main_exe_url = "https://github.com/PersonX-46/BarcodePrinter/releases/latest/download/BarcodePrinter.exe"
        self.updater_exe_url = "https://github.com/PersonX-46/BarcodePrinter/releases/latest/download/Updater.exe"

        self.setWindowIcon(QIcon(self.resource_path("logo.ico")))

        self.lbl_iconLogo = self.findChild(QLabel, 'lbl_iconLogo')
        self.lbl_iconLogo.setPixmap(QPixmap(self.resource_path("logo.jpeg")))
        self.lbl_iconLogo = self.findChild(QLabel, 'lbl_iconLogo_2')
        self.lbl_iconLogo.setPixmap(QPixmap(self.resource_path("logo.jpeg")))   

        # Temporary download location
        self.temp_dir = os.path.join(os.getenv("TEMP"), "BarcodeInstaller")

        # Connect buttons
        self.btn_selectFolder.clicked.connect(self.browse_folder)
        self.button(QWizard.FinishButton).clicked.disconnect()  # Disconnect default behavior
        self.button(QWizard.FinishButton).clicked.connect(self.on_finish_button_clicked)
        self.progressBar.setVisible(False)

    def browse_folder(self):
        """Open a folder dialog to select the installation directory."""
        folder = QFileDialog.getExistingDirectory(self, "Select Installation Folder")
        if folder:
            self.et_folderPath.setText(folder)
            self.progressBar.setVisible(True)
        

    def download_file(self, url, destination):
        """Download a file from the given URL to the specified destination."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Raise an error for HTTP issues
            with open(destination, "wb") as f:
                shutil.copyfileobj(response.raw, f)
        except requests.RequestException as e:
            QMessageBox.critical(self, "Download Error", f"Failed to download {url}:\n{e}")
            raise

    def install_files(self):
        """Download, copy files to the selected folder, and create a desktop shortcut."""
        folder = self.et_folderPath.text()

        if not folder:
            QMessageBox.warning(self, "Error", "Please select a valid installation folder.")
            return

        try:
            # Ensure the folder exists
            os.makedirs(folder, exist_ok=True)

            # Set progress bar to 0
            self.progressBar.setValue(0)

            # Download files to a temporary location
            os.makedirs(self.temp_dir, exist_ok=True)
            main_exe_temp = os.path.join(self.temp_dir, "BarcodePrinter.exe")
            updater_exe_temp = os.path.join(self.temp_dir, "Updater.exe")

            # Update progress: Downloading files
            self.progressBar.setValue(10)
            self.download_file(self.main_exe_url, main_exe_temp)
            self.progressBar.setValue(50)
            self.download_file(self.updater_exe_url, updater_exe_temp)

            # Copy files to the selected folder
            self.progressBar.setValue(70)
            shutil.copy(main_exe_temp, os.path.join(folder, "BarcodePrinter.exe"))
            shutil.copy(updater_exe_temp, os.path.join(folder, "Updater.exe"))

            # Create a desktop shortcut for BarcodePrinter.exe
            self.progressBar.setValue(90)
            self.create_shortcut(os.path.join(folder, "BarcodePrinter.exe"))

            # Finalize progress
            self.progressBar.setValue(100)

            QMessageBox.information(self, "Success", "Program installed successfully!")

        except Exception as e:
            self.progressBar.setValue(0)  # Reset progress on error
            QMessageBox.critical(self, "Installation Error", f"An error occurred during installation:\n{e}")

    def on_finish_button_clicked(self):
        """Custom behavior for the Finish button."""
        folder = self.et_folderPath.text()
        if not folder:
            QMessageBox.warning(self, "Error", "Please select a valid installation folder.")
            return

        # Call the install_files method to proceed with installation
        self.install_files()

        # Keep the wizard visible
        QMessageBox.information(self, "Installation Complete", "Installation is complete. You may close the installer when ready.")


    def create_shortcut(self, target_path):
        """Create a desktop shortcut for the program."""
        try:
            desktop = os.path.join(os.path.join(os.environ["USERPROFILE"]), "Desktop")
            shortcut_path = os.path.join(desktop, "BarcodePrinter.lnk")

            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(shortcut_path)
            shortcut.TargetPath = target_path
            shortcut.WorkingDirectory = os.path.dirname(target_path)
            shortcut.IconLocation = target_path  # Use the program's icon
            shortcut.save()
        except Exception as e:
            QMessageBox.warning(self, "Shortcut Error", f"Could not create desktop shortcut:\n{e}")

    def resource_path(self, relative_path):
        try:
            # Attempt to get the PyInstaller base path
            base_path = sys._MEIPASS
        except AttributeError:
            # Fall back to the current working directory in development mode
            base_path = os.path.abspath(".")
        except Exception as e:
            raise

        # Construct the absolute path to the resource
        absolute_path = os.path.join(base_path, relative_path)
        return absolute_path


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Ensure the script is run with administrative privileges
    if not ctypes.windll.shell32.IsUserAnAdmin():
        QMessageBox.critical(None, "Admin Rights Required", "Please run the installer as an administrator.")
        sys.exit()

    wizard = InstallerWizard()
    wizard.show()
    sys.exit(app.exec_())
