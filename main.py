import sys
from PyQt5.QtWidgets import QApplication, QDialog
from modules.ui.app import BarcodeApp
from modules.Configurations import BarcodeConfig
from modules.licensing import is_licensed
from modules.ui.license_dialog import LicenseDialog

def main():
    """Main entry point for the Barcode Printer application."""
    app = QApplication(sys.argv)

    config = BarcodeConfig()
    if not is_licensed(config):
        license_dialog = LicenseDialog(config)
        if license_dialog.exec_() != QDialog.Accepted:
            sys.exit(0)  # user closed/cancelled -- never open the main window

    # Initialize and show the main window
    window = BarcodeApp()
    window.showMaximized()
    
    # Execute the application event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()