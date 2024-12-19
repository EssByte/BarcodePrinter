# update_manager.py
import os
import sys
import requests
import shutil
from PyQt5.QtWidgets import QMessageBox

# GitHub API URL for your repository's latest release
GITHUB_API_URL = "https://api.github.com/repos/PersonX-46/BarcodePrinter/releases/latest"
# URL to download the latest executable from GitHub release
GITHUB_DOWNLOAD_URL = "https://github.com/PersonX-46/BarcodePrinter/releases/download/latest/BarcodePrinter.exe"

def check_for_update(current_version, window):
    """
    Checks for updates on GitHub and initiates the update process if a new version is available.
    :param current_version: The current version of the app
    :param window: The main window to show message boxes
    """
    try:
        # Fetch the latest release data from GitHub API
        response = requests.get(GITHUB_API_URL)
        release_data = response.json()
        
        # Get the latest version from the release
        latest_version = release_data['tag_name']  # Tag name is usually the version
        
        # Compare the versions
        if latest_version > current_version:
            reply = QMessageBox.question(window, 'Update Available', 
                                         "A new update is available. Do you want to update?", 
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                download_new_version(GITHUB_DOWNLOAD_URL, window)
        else:
            QMessageBox.information(window, 'No Updates', "Your app is up-to-date!")
    except Exception as e:
        QMessageBox.critical(window, 'Error', f"Error checking for updates: {e}")


def download_new_version(download_url, window):
    """
    Downloads the new version from the provided URL and replaces the old executable.
    :param download_url: The URL to download the new executable
    :param window: The main window to show message boxes
    """
    try:
        # Download the new executable from GitHub
        response = requests.get(download_url, stream=True)
        new_version_path = "new_app.exe"  # Temp path to save the downloaded file
        
        with open(new_version_path, "wb") as f:
            shutil.copyfileobj(response.raw, f)
        
        # Replace the old executable with the new one
        app_path = sys.argv[0]  # Current executable path
        os.rename(new_version_path, app_path)  # Replace old app with the new one
        
        QMessageBox.information(window, 'Update Successful', "The app has been updated. Restarting the app...")
        
        # Restart the app to apply the update
        os.execv(app_path, sys.argv)  # Restart the app to apply the update

    except Exception as e:
        QMessageBox.critical(window, 'Error', f"Error downloading or updating the app: {e}")
