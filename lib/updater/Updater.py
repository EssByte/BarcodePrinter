import os
import subprocess
import sys
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QProgressBar, QFrame, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QColor

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
        
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("System Update")
        self.setFixedSize(500, 350)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main Frame
        self.main_frame = QFrame(self)
        self.main_frame.setGeometry(0, 0, 500, 350)
        self.main_frame.setStyleSheet("""
            QFrame { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e293b, stop:1 #0f172a);
                border-radius: 15px; border: 1px solid #334155;
            }
        """)
        
        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Software Update")
        title.setStyleSheet("color: #3b82f6; font-size: 22px; font-weight: 800;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        # Details
        self.info_frame = QFrame()
        self.info_frame.setStyleSheet("background: rgba(255,255,255,0.05); border-radius: 10px; border: none;")
        info_lay = QVBoxLayout(self.info_frame)
        
        self.lbl_version = QLabel("Latest Version: Fetching...")
        self.lbl_version.setStyleSheet("color: #f1f5f9; font-weight: bold; border: none;")
        info_lay.addWidget(self.lbl_version)
        
        self.lbl_status = QLabel("Ready to check for updates.")
        self.lbl_status.setStyleSheet("color: #94a3b8; font-size: 13px; border: none;")
        info_lay.addWidget(self.lbl_status)
        
        layout.addWidget(self.info_frame)
        
        layout.addSpacing(20)
        
        # Progress
        self.pbar = QProgressBar()
        self.pbar.setFixedHeight(8)
        self.pbar.setVisible(False)
        self.pbar.setStyleSheet("""
            QProgressBar { border: none; border-radius: 4px; background: #334155; text-align: center; color: transparent; }
            QProgressBar::chunk { background: #3b82f6; border-radius: 4px; }
        """)
        layout.addWidget(self.pbar)
        
        layout.addStretch()
        
        # Buttons
        btn_lay = QHBoxLayout()
        self.btn_close = QPushButton("Later")
        self.btn_close.setStyleSheet("QPushButton { background: transparent; color: #64748b; border: 1px solid #334155; padding: 10px 20px; border-radius: 8px; } QPushButton:hover { color: white; border-color: #475569; }")
        self.btn_close.clicked.connect(self.close)
        
        self.btn_update = QPushButton("Check for Updates")
        self.btn_update.setStyleSheet("""
            QPushButton { 
                background: #3b82f6; color: white; border: none; padding: 10px 25px; border-radius: 8px; font-weight: bold;
            }
            QPushButton:hover { background: #2563eb; }
            QPushButton:disabled { background: #334155; color: #64748b; }
        """)
        self.btn_update.clicked.connect(self.handle_action)
        
        btn_lay.addWidget(self.btn_close)
        btn_lay.addStretch()
        btn_lay.addWidget(self.btn_update)
        layout.addLayout(btn_lay)
        
        self.is_checked = False
        
    def handle_action(self):
        if not self.is_checked:
            self.check_version()
        else:
            self.download_update()

    def check_version(self):
        self.btn_update.setEnabled(False)
        self.lbl_status.setText("Checking for updates...")
        self.thread = UpdateThread('check', self.repo_owner, self.repo_name, self.install_path)
        self.thread.version_found.connect(self.on_version_found)
        self.thread.error.connect(self.on_error)
        self.thread.start()

    def on_version_found(self, tag):
        self.btn_update.setEnabled(True)
        self.lbl_version.setText(f"Latest Version: {tag}")
        self.lbl_status.setText("A new update is available.")
        self.btn_update.setText("Update Now")
        self.is_checked = True

    def download_update(self):
        self.btn_update.setEnabled(False)
        self.pbar.setVisible(True)
        self.thread = UpdateThread('download', self.repo_owner, self.repo_name, self.install_path)
        self.thread.progress.connect(self.pbar.setValue)
        self.thread.status.connect(self.lbl_status.setText)
        self.thread.finished.connect(self.on_finished)
        self.thread.error.connect(self.on_error)
        self.thread.start()

    def on_finished(self):
        self.lbl_status.setText("Update complete!")
        QMessageBox.information(self, "Success", "Application updated successfully.")
        subprocess.Popen([os.path.join(self.install_path, "BarcodePrinter.exe")])
        self.close()

    def on_error(self, message):
        self.lbl_status.setText(f"Error: {message}")
        self.lbl_status.setStyleSheet("color: #ef4444;")
        self.btn_update.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Updater()
    win.show()
    sys.exit(app.exec_())
