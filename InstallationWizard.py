import os
import sys
import requests
import subprocess
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QProgressBar, QFrame, QStackedWidget)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QTimer, pyqtProperty, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor, QPainter, QLinearGradient

# Same "label stock" identity used across the rest of the app: same ink
# tone as the sidebar/menu bar chrome (not a different navy), and the
# stamped price-tag red as the one accent. Kept dark/frameless here since
# that's an appropriate look for a first-run installer, unlike the light
# canvas used in the main app windows.
WIZ_INK = "#191b1f"
WIZ_INK_LIGHT = "#262930"
WIZ_BORDER = "#2f3238"
WIZ_TEXT_MUTED = "#9a9d9f"
WIZ_ACCENT = "#c81d31"
WIZ_ACCENT_HOVER = "#a91729"
WIZ_SUCCESS = "#2f7d55"
WIZ_SUCCESS_HOVER = "#256844"
WIZ_DANGER = "#c81d31"

class InstallThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, repo_owner, repo_name, install_path):
        super().__init__()
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.install_path = install_path

    def run(self):
        try:
            self.status.emit("Connecting to GitHub...")
            self.progress.emit(5)
            
            os.makedirs(self.install_path, exist_ok=True)
            
            # Download Files
            files = ["BarcodePrinter.exe", "Updater.exe", "libusb-1.0.dll"]
            for i, filename in enumerate(files):
                self.status.emit(f"Downloading {filename}...")
                url = f"https://github.com/{self.repo_owner}/{self.repo_name}/releases/latest/download/{filename}"
                path = os.path.join(self.install_path, filename)
                
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                # Update progress per file
                self.progress.emit(20 + i * 20)
                with open(path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk: f.write(chunk)
                
            self.status.emit("Creating shortcuts...")
            self.create_shortcut()
            self.progress.emit(95)
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))

    def create_shortcut(self):
        try:
            import winshell
            from win32com.client import Dispatch
            desktop = winshell.desktop()
            path = os.path.join(desktop, "Barcode Printer.lnk")
            target = os.path.join(self.install_path, "BarcodePrinter.exe")
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = target
            shortcut.WorkingDirectory = self.install_path
            shortcut.IconLocation = target
            shortcut.save()
        except: pass

class AnimatedLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._opacity = 1.0
        
    @pyqtProperty(float)
    def opacity(self): return self._opacity
    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.setStyleSheet(f"color: rgba(255, 255, 255, {value});")

class InstallationWizard(QWidget):
    def __init__(self):
        super().__init__()
        self.repo_owner = "EssByte"
        self.repo_name = "BarcodePrinter"
        self.install_path = r"C:\barcode"
        
        self.initUI()
        
    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(600, 400)
        
        # Main Background Frame
        # NOTE: QLabel and QStackedWidget both inherit from QFrame in Qt, so
        # a bare "QFrame { ... }" selector here would cascade this frame's
        # background/border onto every label and the step stack too --
        # scope it to this widget specifically via objectName instead.
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("main_frame")
        self.main_frame.setGeometry(0, 0, 600, 400)
        self.main_frame.setStyleSheet(f"""
            QFrame#main_frame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {WIZ_INK}, stop:1 {WIZ_INK_LIGHT});
                border-radius: 20px;
                border: 1px solid {WIZ_BORDER};
            }}
        """)

        self.layout = QVBoxLayout(self.main_frame)
        self.layout.setContentsMargins(40, 36, 40, 36)

        # Header
        self.lbl_logo = QLabel()
        self.lbl_logo.setPixmap(QIcon(self.resource_path("images/logo.ico")).pixmap(40, 40))
        self.lbl_logo.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.lbl_logo)
        self.layout.addSpacing(10)

        self.header = QLabel("Barcode Printer")
        self.header.setStyleSheet(f"color: {WIZ_ACCENT}; font-family: 'Segoe UI Semibold'; font-size: 24px; font-weight: 700;")
        self.header.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.header)

        self.subheader = QLabel("Installation Wizard")
        self.subheader.setStyleSheet(f"color: {WIZ_TEXT_MUTED}; font-family: 'Segoe UI'; font-size: 13px; font-weight: 600;")
        self.subheader.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.subheader)

        self.layout.addSpacing(26)

        # Stacked Widget for Steps
        self.stack = QStackedWidget()

        # Step 1: Welcome
        self.page_welcome = QWidget()
        welcome_lay = QVBoxLayout(self.page_welcome)
        msg = QLabel("Welcome to the modern Barcode Printer experience.\nClick begin to start the installation process.")
        msg.setStyleSheet("color: #f1f0ec; font-family: 'Segoe UI'; font-size: 14px;")
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignCenter)
        welcome_lay.addWidget(msg)
        self.stack.addWidget(self.page_welcome)

        # Step 2: Installing
        self.page_install = QWidget()
        install_lay = QVBoxLayout(self.page_install)
        self.lbl_status = QLabel("Preparing...")
        self.lbl_status.setStyleSheet(f"color: {WIZ_ACCENT}; font-family: 'Segoe UI'; font-weight: 700; font-size: 13px;")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        install_lay.addWidget(self.lbl_status)

        self.pbar = QProgressBar()
        self.pbar.setFixedHeight(10)
        self.pbar.setStyleSheet(f"""
            QProgressBar {{ border: none; border-radius: 5px; background: {WIZ_INK_LIGHT}; text-align: center; color: transparent; }}
            QProgressBar::chunk {{ background: {WIZ_ACCENT}; border-radius: 5px; }}
        """)
        install_lay.addWidget(self.pbar)
        self.stack.addWidget(self.page_install)

        # Step 3: Finished
        self.page_finish = QWidget()
        finish_lay = QVBoxLayout(self.page_finish)
        f_msg = QLabel("Success!\nBarcode Printer is now installed and ready.")
        f_msg.setStyleSheet(f"color: {WIZ_SUCCESS}; font-family: 'Segoe UI'; font-size: 16px; font-weight: 700;")
        f_msg.setAlignment(Qt.AlignCenter)
        finish_lay.addWidget(f_msg)
        self.stack.addWidget(self.page_finish)

        self.layout.addWidget(self.stack)

        # Footer Buttons
        self.btn_layout = QHBoxLayout()
        self.btn_close = QPushButton("Cancel")
        self.btn_close.setStyleSheet(f"QPushButton {{ background: transparent; color: {WIZ_TEXT_MUTED}; border: 1px solid {WIZ_BORDER}; padding: 10px 20px; border-radius: 7px; font-family: 'Segoe UI'; font-weight: 600; }} QPushButton:hover {{ color: #f1f0ec; border-color: #3a3d44; }}")
        self.btn_close.clicked.connect(self.close)

        self.btn_action = QPushButton("Begin Installation")
        self.btn_action.setCursor(Qt.PointingHandCursor)
        self.btn_action.setStyleSheet(f"""
            QPushButton {{
                background: {WIZ_ACCENT}; color: white; border: none; padding: 12px 30px; border-radius: 7px;
                font-family: 'Segoe UI'; font-weight: 700; font-size: 13px;
            }}
            QPushButton:hover {{ background: {WIZ_ACCENT_HOVER}; }}
        """)
        self.btn_action.clicked.connect(self.next_step)
        
        self.btn_layout.addWidget(self.btn_close)
        self.btn_layout.addStretch()
        self.btn_layout.addWidget(self.btn_action)
        self.layout.addLayout(self.btn_layout)
        
        self.current_step = 0

    def next_step(self):
        if self.current_step == 0:
            self.current_step = 1
            self.stack.setCurrentIndex(1)
            self.btn_action.setEnabled(False)
            self.btn_close.setVisible(False)
            QTimer.singleShot(500, self.start_installation)
        elif self.current_step == 2:
            self.run_app()

    def start_installation(self):
        self.thread = InstallThread(self.repo_owner, self.repo_name, self.install_path)
        self.thread.progress.connect(self.pbar.setValue)
        self.thread.status.connect(self.lbl_status.setText)
        self.thread.finished.connect(self.finish_install)
        self.thread.error.connect(self.on_error)
        self.thread.start()

    def on_error(self, message):
        self.lbl_status.setText(f"Error: {message}")
        self.lbl_status.setStyleSheet(f"color: {WIZ_DANGER}; font-family: 'Segoe UI'; font-weight: 700; font-size: 13px;")
        self.btn_close.setVisible(True)

    def create_shortcut(self):
        # Programmatic shortcut creation (Windows only)
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            path = os.path.join(desktop, "Barcode Printer.lnk")
            target = os.path.join(self.install_path, "BarcodePrinter.exe")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = target
            shortcut.WorkingDirectory = self.install_path
            shortcut.IconLocation = target
            shortcut.save()
        except: pass

    def finish_install(self):
        self.pbar.setValue(100)
        self.current_step = 2
        self.stack.setCurrentIndex(2)
        self.btn_action.setText("Launch Application")
        self.btn_action.setEnabled(True)
        self.btn_action.setStyleSheet(f"""
            QPushButton {{
                background: {WIZ_SUCCESS}; color: white; border: none; padding: 12px 30px; border-radius: 7px;
                font-family: 'Segoe UI'; font-weight: 700; font-size: 13px;
            }}
            QPushButton:hover {{ background: {WIZ_SUCCESS_HOVER}; }}
        """)

    def run_app(self):
        subprocess.Popen([os.path.join(self.install_path, "BarcodePrinter.exe")])
        self.close()

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    wizard = InstallationWizard()
    wizard.show()
    sys.exit(app.exec_())
