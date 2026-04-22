import sys
from PyQt5.QtWidgets import QApplication
from modules.ui.app import BarcodeApp

def main():
    """Main entry point for the Barcode Printer application."""
    app = QApplication(sys.argv)
    
    # Initialize and show the main window
    window = BarcodeApp()
    window.showMaximized()
    
    # Execute the application event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()