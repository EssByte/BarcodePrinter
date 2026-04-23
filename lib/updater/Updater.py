import os
import subprocess
import sys
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QProgressBar, QFrame, QMessageBox, QStackedWidget)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter, QLinearGradient

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
        self.repo_owner = "PersonX-46"
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
        self.main_frame = QFrame(self)
        self.main_frame.setGeometry(0, 0, 500, 350)
        self.main_frame.setStyleSheet("""
            QFrame { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f172a, stop:1 #1e293b);
                border-radius: 15px; border: 1px solid #334155;
            }
        """)
        
        self.layout = QVBoxLayout(self.main_frame)
        self.layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        self.header = QLabel("System Updater")
        self.header.setStyleSheet("color: #3b82f6; font-size: 22px; font-weight: 800;")
        self.header.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.header)
        
        self.layout.addSpacing(20)
        
        # Stacked Widget
        self.stack = QStackedWidget()
        
        # Page 1: Checking/Info
        self.page_info = QWidget()
        info_lay = QVBoxLayout(self.page_info)
        info_lay.setAlignment(Qt.AlignCenter)
        
        self.lbl_status = QLabel("Checking for updates...")
        self.lbl_status.setStyleSheet("color: #94a3b8; font-size: 16px;")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        info_lay.addWidget(self.lbl_status)
        
        self.lbl_version = QLabel("")
        self.lbl_version.setStyleSheet("color: #3b82f6; font-weight: bold; font-size: 14px;")
        self.lbl_version.setAlignment(Qt.AlignCenter)
        info_lay.addWidget(self.lbl_version)
        
        self.stack.addWidget(self.page_info)
        
        # Page 2: Downloading
        self.page_dl = QWidget()
        dl_lay = QVBoxLayout(self.page_dl)
        dl_lay.setAlignment(Qt.AlignCenter)
        
        self.lbl_dl_status = QLabel("Downloading...")
        self.lbl_dl_status.setStyleSheet("color: #3b82f6; font-weight: bold;")
        self.lbl_dl_status.setAlignment(Qt.AlignCenter)
        dl_lay.addWidget(self.lbl_dl_status)
        
        self.pbar = QProgressBar()
        self.pbar.setFixedHeight(10)
        self.pbar.setStyleSheet("""
            QProgressBar { border: none; border-radius: 5px; background: #334155; text-align: center; color: transparent; }
            QProgressBar::chunk { background: #3b82f6; border-radius: 5px; }
        """)
        dl_lay.addWidget(self.pbar)
        
        self.stack.addWidget(self.page_dl)
        
        self.layout.addWidget(self.stack)
        
        # Footer
        self.footer = QHBoxLayout()
        self.btn_close = QPushButton("Later")
        self.btn_close.setStyleSheet("QPushButton { background: transparent; color: #64748b; border: 1px solid #334155; padding: 10px 20px; border-radius: 8px; } QPushButton:hover { color: white; border-color: #475569; }")
        self.btn_close.clicked.connect(self.close)
        
        self.btn_action = QPushButton("Check Now")
        self.btn_action.setEnabled(False)
        self.btn_action.setStyleSheet("""
            QPushButton { 
                background: #3b82f6; color: white; border: none; padding: 10px 25px; border-radius: 8px; font-weight: bold;
            }
            QPushButton:hover { background: #2563eb; }
            QPushButton:disabled { background: #334155; color: #64748b; }
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
        self.lbl_status.setStyleSheet("color: #f1f5f9; font-size: 18px; font-weight: bold;")
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
        self.lbl_status.setStyleSheet("color: #ef4444; font-size: 14px;")
        self.btn_action.setEnabled(True)
        self.btn_action.setText("Retry")
        self.btn_close.setVisible(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Updater()
    win.show()
    sys.exit(app.exec_())
