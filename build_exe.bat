@echo off
REM PyInstaller build script for BarcodePrinter

REM Activate virtual environment (optional, only if needed)
call venv1\Scripts\activate.bat

REM Run PyInstaller with all necessary options
pyinstaller --noconfirm --onefile --console ^
--icon=images/logo.ico ^
--add-data "ui;ui" ^
--add-data "images;images" ^
--add-binary "libusb-1.0.dll;." ^
--hidden-import=win32print ^
--hidden-import=pyodbc ^
--hidden-import=PyQt5 ^
--hidden-import=libusb ^
--hidden-import=usb ^
--hidden-import=pyusb ^
main.py

REM Notify when done
echo.
echo ✅ Build complete! Check the dist\ folder.
pause
