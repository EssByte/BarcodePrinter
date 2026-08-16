import os
import subprocess
import sys
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QProgressBar, QFrame, QMessageBox, QStackedWidget)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter, QLinearGradient

# Same "label stock" identity used across the rest of the app.
UPD_INK = "#191b1f"
UPD_INK_LIGHT = "#262930"
UPD_BORDER = "#2f3238"
UPD_TEXT_MUTED = "#9a9d9f"
UPD_ACCENT = "#c81d31"
UPD_ACCENT_HOVER = "#a91729"
UPD_DANGER = "#c81d31"

class UpdateThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    version_found = pyqtSignal(str)

    def __init__(self, mode, repo_owner, repo_name, install_path):
        super().__init__()
        self.mode = mode # 'check' or 'download'
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.install_path = install_path

    def run(self):
        try:
            if self.mode == 'check':
                api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
                res = requests.get(api_url).json()
                tag = res.get("tag_name", "Unknown")
                self.version_found.emit(tag)
            else:
                os.makedirs(self.install_path, exist_ok=True)
                files = ["BarcodePrinter.exe", "Updater.exe", "libusb-1.0.dll"]
                for i, f_name in enumerate(files):
                    self.status.emit(f"Downloading {f_name}...")
                    url = f"https://github.com/{self.repo_owner}/{self.repo_name}/releases/latest/download/{f_name}"
                    path = os.path.join(self.install_path, f_name)
                    resp = requests.get(url, stream=True)
                    resp.raise_for_status()
                    self.progress.emit(10 + i * 30)
                    with open(path, "wb") as f:
                        for chunk in resp.iter_content(8192):
                            if chunk: f.write(chunk)
                self.progress.emit(100)
                self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class Updater(QWidget):
    def __init__(self):
        super().__init__()
        self.repo_owner = "EssByte"
        self.repo_name = "BarcodePrinter"
        self.install_path = r"C:\barcode"
        self.thread = None
        self.is_checked = False
        
        self.initUI()
        self.check_version() # Auto check on start
        
    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(500, 350)
        
        # Main Background
        # NOTE: QLabel and QStackedWidget both inherit from QFrame in Qt, so
        # a bare "QFrame { ... }" selector here would cascade this frame's
        # background/border onto every label and the page stack too --
        # scope it to this widget specifically via objectName instead.
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("main_frame")
        self.main_frame.setGeometry(0, 0, 500, 350)
        self.main_frame.setStyleSheet(f"""
            QFrame#main_frame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {UPD_INK}, stop:1 {UPD_INK_LIGHT});
                border-radius: 15px; border: 1px solid {UPD_BORDER};
            }}
        """)

        self.layout = QVBoxLayout(self.main_frame)
        self.layout.setContentsMargins(30, 28, 30, 28)

        # Header
        self.lbl_logo = QLabel()
        self.lbl_logo.setPixmap(QIcon(self.resource_path("images/logo.ico")).pixmap(32, 32))
        self.lbl_logo.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.lbl_logo)
        self.layout.addSpacing(8)

        self.header = QLabel("System Updater")
        self.header.setStyleSheet(f"color: {UPD_ACCENT}; font-family: 'Segoe UI Semibold'; font-size: 19px; font-weight: 700;")
        self.header.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.header)

        self.layout.addSpacing(18)

        # Stacked Widget
        self.stack = QStackedWidget()

        # Page 1: Checking/Info
        self.page_info = QWidget()
        info_lay = QVBoxLayout(self.page_info)
        info_lay.setAlignment(Qt.AlignCenter)

        self.lbl_status = QLabel("Checking for updates...")
        self.lbl_status.setStyleSheet(f"color: {UPD_TEXT_MUTED}; font-family: 'Segoe UI'; font-size: 14px; font-weight: 600;")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        info_lay.addWidget(self.lbl_status)

        self.lbl_version = QLabel("")
        self.lbl_version.setStyleSheet(f"color: {UPD_ACCENT}; font-family: 'Segoe UI'; font-weight: 700; font-size: 13px;")
        self.lbl_version.setAlignment(Qt.AlignCenter)
        info_lay.addWidget(self.lbl_version)

        self.stack.addWidget(self.page_info)

        # Page 2: Downloading
        self.page_dl = QWidget()
        dl_lay = QVBoxLayout(self.page_dl)
        dl_lay.setAlignment(Qt.AlignCenter)

        self.lbl_dl_status = QLabel("Downloading...")
        self.lbl_dl_status.setStyleSheet(f"color: {UPD_ACCENT}; font-family: 'Segoe UI'; font-weight: 700; font-size: 13px;")
        self.lbl_dl_status.setAlignment(Qt.AlignCenter)
        dl_lay.addWidget(self.lbl_dl_status)

        self.pbar = QProgressBar()
        self.pbar.setFixedHeight(10)
        self.pbar.setStyleSheet(f"""
            QProgressBar {{ border: none; border-radius: 5px; background: {UPD_INK_LIGHT}; text-align: center; color: transparent; }}
            QProgressBar::chunk {{ background: {UPD_ACCENT}; border-radius: 5px; }}
        """)
        dl_lay.addWidget(self.pbar)

        self.stack.addWidget(self.page_dl)

        self.layout.addWidget(self.stack)

        # Footer
        self.footer = QHBoxLayout()
        self.btn_close = QPushButton("Later")
        self.btn_close.setStyleSheet(f"QPushButton {{ background: transparent; color: {UPD_TEXT_MUTED}; border: 1px solid {UPD_BORDER}; padding: 10px 20px; border-radius: 7px; font-family: 'Segoe UI'; font-weight: 600; }} QPushButton:hover {{ color: #f1f0ec; border-color: #3a3d44; }}")
        self.btn_close.clicked.connect(self.close)

        self.btn_action = QPushButton("Check Now")
        self.btn_action.setEnabled(False)
        self.btn_action.setStyleSheet(f"""
            QPushButton {{
                background: {UPD_ACCENT}; color: white; border: none; padding: 10px 25px; border-radius: 7px;
                font-family: 'Segoe UI'; font-weight: 700; font-size: 13px;
            }}
            QPushButton:hover {{ background: {UPD_ACCENT_HOVER}; }}
            QPushButton:disabled {{ background: {UPD_INK_LIGHT}; color: {UPD_TEXT_MUTED}; }}
        """)
        self.btn_action.clicked.connect(self.handle_action)
        
        self.footer.addWidget(self.btn_close)
        self.footer.addStretch()
        self.footer.addWidget(self.btn_action)
        self.layout.addLayout(self.footer)

    def handle_action(self):
        if not self.is_checked:
            self.check_version()
        else:
            self.stack.setCurrentIndex(1)
            self.btn_action.setEnabled(False)
            self.btn_close.setVisible(False)
            self.download_update()

    def check_version(self):
        self.btn_action.setEnabled(False)
        self.lbl_status.setText("Scanning for updates...")
        self.thread = UpdateThread('check', self.repo_owner, self.repo_name, self.install_path)
        self.thread.version_found.connect(self.on_version_found)
        self.thread.error.connect(self.on_error)
        self.thread.start()

    def on_version_found(self, tag):
        self.btn_action.setEnabled(True)
        self.lbl_version.setText(f"Latest: {tag}")
        self.lbl_status.setText("Update Available")
        self.lbl_status.setStyleSheet("color: #f1f0ec; font-family: 'Segoe UI'; font-size: 15px; font-weight: 700;")
        self.btn_action.setText("Update Now")
        self.is_checked = True

    def download_update(self):
        self.thread = UpdateThread('download', self.repo_owner, self.repo_name, self.install_path)
        self.thread.progress.connect(self.pbar.setValue)
        self.thread.status.connect(self.lbl_dl_status.setText)
        self.thread.finished.connect(self.on_finished)
        self.thread.error.connect(self.on_error)
        self.thread.start()

    def on_finished(self):
        self.lbl_dl_status.setText("System Updated!")
        QMessageBox.information(self, "Success", "Application updated successfully.")
        subprocess.Popen([os.path.join(self.install_path, "BarcodePrinter.exe")])
        self.close()

    def on_error(self, message):
        self.stack.setCurrentIndex(0)
        self.lbl_status.setText(f"Error: {message}")
        self.lbl_status.setStyleSheet(f"color: {UPD_DANGER}; font-family: 'Segoe UI'; font-size: 13px; font-weight: 700;")
        self.btn_action.setEnabled(True)
        self.btn_action.setText("Retry")
        self.btn_close.setVisible(True)

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Updater()
    win.show()
    sys.exit(app.exec_())
