from PyQt5.QtWidgets import QMessageBox
import socket
import subprocess
import os
from logger_config import setup_logger
import win32print

class SendCommand():

    def __init__(self):
        self.logger = setup_logger('Send Command')
        self.logger.info("Initializing BarcodeApp...")

    def send_wireless_command(self, ip_address, port, command):
        try:
            # Validate IP address
            self.logger.info(f"Validating IP address: {ip_address}")
            try:
                socket.inet_aton(ip_address)
            except socket.error:
                self.logger.error(f"Invalid IP address: {ip_address}")
                QMessageBox.critical(self, 'Error', f"Invalid IP address: {ip_address}")
                return

            # Ping the IP address to check if it's reachable
            self.logger.info(f"Pinging {ip_address} to check connectivity...")
            ping_command = ["ping", "-n", "1", ip_address] if os.name == "nt" else ["ping", "-c", "1", ip_address]
            ping_result = subprocess.run(ping_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if ping_result.returncode != 0:
                self.logger.error(f"Ping failed for {ip_address}. Device may be unreachable.")
                QMessageBox.critical(self, 'Error', f"Ping failed for {ip_address}. Device may be unreachable.")
                return

            # Log connection attempt
            self.logger.info(f"Attempting to connect to {ip_address}:{port}")

            # Check if the port is open
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(3)  # Set a timeout for the connection attempt
                if sock.connect_ex((ip_address, int(port))) != 0:
                    self.logger.error(f"Port {port} on {ip_address} is not open.")
                    QMessageBox.critical(self, 'Error', f"Port {port} on {ip_address} is not open.")
                    return

            # Create a socket and connect
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((ip_address, int(port)))
                self.logger.info(f"Connected to {ip_address}:{port}")

                # Send the command
                client_socket.sendall(command.encode('utf-8'))
                self.logger.info(f"Command sent successfully: {command}")

                # No need to explicitly close as `with` context handles it
                self.logger.info("Connection closed.")

        except Exception as e:
            # Log the error
            self.logger.error(f"Error while sending command to {ip_address}:{port}: {e}")

            # Show error message to the user
            QMessageBox.critical(self, 'Error', f"Error: {e}")

    def send_win32print(printer_name, raw_data):
        # Open the printer
        printer = win32print.OpenPrinter(printer_name)
        try:
            # Start a print job
            job_info = ("Print Job", None, "RAW")
            job_id = win32print.StartDocPrinter(printer, 1, job_info)
            
            # Start a new page
            win32print.StartPagePrinter(printer)
            # Send raw data to the printer
            win32print.WritePrinter(printer, raw_data.encode())
            
            # End the page and the job
            win32print.EndPagePrinter(printer)
            win32print.EndDocPrinter(printer)
        finally:
            # Close the printer connection
            win32print.ClosePrinter(printer)