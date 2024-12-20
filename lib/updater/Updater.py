import os
import subprocess
import sys
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QLabel
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5 import uic


class Updater(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi(self.resource_path("updater.ui"), self)  # Load the .ui file
        self.et_version.setText("Not available!")
        self.et_name.setText("Not available!")
        self.et_published.setText("Not available!")

        # GitHub repository information
        self.repo_owner = "PersonX-46"
        self.repo_name = "BarcodePrinter"
        self.download_url = f"https://github.com/{self.repo_owner}/{self.repo_name}/releases/latest/download/BarcodePrinter.exe"
        self.api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"

        # Connect buttons
        self.btn_close.clicked.connect(self.close_application)
        self.btn_check.clicked.connect(self.check_version)
        self.btn_update.clicked.connect(self.download_update)
        self.lbl_iconTable.setPixmap(QPixmap(self.resource_path("updateicon.png")))
        self.setWindowIcon(QIcon(self.resource_path("logo.ico")))
        self.lbl_iconLogo = self.findChild(QLabel, 'lbl_iconLogo')
        self.lbl_iconLogo.setPixmap(QPixmap(self.resource_path("logo.jpeg")))

    def close_application(self):
        """Close the updater application."""
        subprocess.Popen([r"C:\barcode\BarcodePrinter.exe"])
        self.close()
        self.close()

    def check_version(self):
        """Fetch the latest release details from GitHub."""
        try:
            self.log_message("Fetching version details from GitHub...")
            response = requests.get(self.api_url)
            response.raise_for_status()

            release_data = response.json()
            tag_name = release_data["tag_name"]
            tag_title = release_data["name"]
            published_at = release_data["published_at"]

            # Display version details in the text fields
            self.et_version.setText(tag_name)
            self.et_name.setText(tag_title)
            self.et_published.setText(published_at)

            self.log_message("Version details updated successfully.")
        except requests.RequestException as e:
            error_message = f"Failed to fetch version details:\n{e}"
            self.log_message(error_message)
            QMessageBox.critical(self, "Version Check Error", error_message)

    def download_update(self):
        """Download the latest version of the BarcodePrinter.exe from GitHub."""
        try:
            self.log_message("Starting update download...")
            response = requests.get(self.download_url, stream=True)
            response.raise_for_status()

            # Save the file to the desired location
            file_path = os.path.join(os.getcwd(), "BarcodePrinter.exe")
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)

            self.log_message(f"Update downloaded successfully to {file_path}.")
            QMessageBox.information(self, "Update Complete", f"BarcodePrinter.exe has been updated successfully.")
        except requests.RequestException as e:
            error_message = f"Failed to download update:\n{e}"
            self.log_message(error_message)
            QMessageBox.critical(self, "Download Error", error_message)

    def log_message(self, message):
        """Log messages to the console or a logger."""
        print(message)  # Replace with a proper logger if needed

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
    updater = Updater()
    updater.show()
    sys.exit(app.exec_())
