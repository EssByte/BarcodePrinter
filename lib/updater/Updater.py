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
        self.progressBar.setVisible(False)

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
            self.progressBar.setVisible(True)
            self.log_message("Starting update download...")
            
            # Define the target directory
            target_dir = r"C:\barcode"
            
            # Create directory if it doesn't exist
            os.makedirs(target_dir, exist_ok=True)
            
            # Download BarcodePrinter.exe
            barcode_printer_url = f"https://github.com/{self.repo_owner}/{self.repo_name}/releases/latest/download/BarcodePrinter.exe"
            barcode_printer_path = os.path.join(target_dir, "BarcodePrinter.exe")
            
            self.download_file_with_progress(barcode_printer_url, barcode_printer_path, "Barcode Printer", 0, 50)
            
            # Download Updater.exe
            updater_url = f"https://github.com/{self.repo_owner}/{self.repo_name}/releases/latest/download/Updater.exe"
            updater_path = os.path.join(target_dir, "Updater.exe")
            
            self.download_file_with_progress(updater_url, updater_path, "Updater", 50, 100)
            
            self.progressBar.setValue(100)
            self.log_message(f"Update downloaded successfully to {target_dir}.")
            
            QMessageBox.information(self, "Update Complete", 
                                "Both BarcodePrinter.exe and Updater.exe have been updated successfully!")
            
            # Restart the main application
            self.restart_application()
            
        except requests.RequestException as e:
            error_message = f"Failed to download update:\n{e}"
            self.log_message(error_message)
            self.progressBar.setVisible(False)
            QMessageBox.critical(self, "Download Error", error_message)
        except Exception as e:
            error_message = f"Unexpected error during download:\n{e}"
            self.log_message(error_message)
            self.progressBar.setVisible(False)
            QMessageBox.critical(self, "Download Error", error_message)

    def download_file_with_progress(self, url, file_path, display_name, progress_start, progress_end):
        """Download a single file with progress tracking"""
        self.log_message(f"Downloading {display_name}...")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    if total_size > 0:
                        file_progress = (downloaded_size / total_size)
                        overall_progress = progress_start + (file_progress * (progress_end - progress_start))
                        self.progressBar.setValue(int(overall_progress))
                    
                    QApplication.processEvents()
        
        self.log_message(f"{display_name} downloaded successfully to {file_path}")

    def restart_application(self):
        """Restart the main BarcodePrinter application"""
        try:
            main_app_path = r"C:\barcode\BarcodePrinter.exe"
            if os.path.exists(main_app_path):
                subprocess.Popen([main_app_path])
            self.close()
        except Exception as e:
            self.log_message(f"Error restarting application: {e}")
            self.close()

    def update_download_status(self, downloaded, total, progress):
        """Update the download status display."""
        status_text = f"Downloading... {self.format_bytes(downloaded)}"
        if total > 0:
            status_text += f" / {self.format_bytes(total)} ({progress}%)"
        
        # Update a status label if you have one
        if hasattr(self, 'lbl_status'):
            self.lbl_status.setText(status_text)
        
        self.log_message(status_text)

    def format_bytes(self, size):
        """Format bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def download_failed(self, error_message):
        """Handle download failure."""
        self.progressBar.setVisible(False)
        self.btn_update.setEnabled(True)
        self.btn_check.setEnabled(True)
        
        if hasattr(self, 'lbl_status'):
            self.lbl_status.setText("Download failed")
        
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
