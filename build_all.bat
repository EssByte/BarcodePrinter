@echo off
echo ========================================
echo Barcode Printer - Suite Build Script
echo ========================================

echo [1/4] Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [2/4] Building Barcode Printer...
pyinstaller --noconfirm --onefile --console --name "BarcodePrinter" --icon=images/logo.ico --add-data "ui;ui" --add-data "images;images" --add-binary "libusb-1.0.dll;." --hidden-import=win32print --hidden-import=pyodbc --hidden-import=PyQt5 --hidden-import=libusb --hidden-import=usb --hidden-import=pyusb main.py

echo.
echo [3/4] Building Updater...
pyinstaller --noconfirm --onefile --console --name "Updater" --icon=images/logo.ico --hidden-import=PyQt5 --hidden-import=requests lib/updater/Updater.py

echo.
echo [4/4] Building Installation Wizard...
pyinstaller --noconfirm --onefile --console --name "InstallationWizard" --icon=images/logo.ico --hidden-import=PyQt5 --hidden-import=requests --hidden-import=winshell --hidden-import=win32com InstallationWizard.py

echo.
echo ========================================
echo Build Complete! EXEs are in the 'dist' folder.
echo ========================================
pause
