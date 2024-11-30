from PyQt5.QtWidgets import QMessageBox
import socket
import subprocess
import os
from logger_config import setup_logger
import win32print

class SendCommand:
    def __init__(self):
        self.logger = setup_logger('SendCommand')
        self.logger.info("Initializing SendCommand class...")

    def send_wireless_command(self, ip_address, port, command):
        try:
            # Validate IP address
            self.logger.info(f"Validating IP address: {ip_address}")
            try:
                socket.inet_aton(ip_address)
            except socket.error:
                self.logger.error(f"Invalid IP address: {ip_address}")
                QMessageBox.critical(None, 'Error', f"Invalid IP address: {ip_address}")
                return

            # Ping the IP address to check if it's reachable
            self.logger.info(f"Pinging {ip_address} to check connectivity...")
            ping_command = ["ping", "-n", "1", ip_address] if os.name == "nt" else ["ping", "-c", "1", ip_address]
            ping_result = subprocess.run(ping_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if ping_result.returncode != 0:
                self.logger.error(f"Ping failed for {ip_address}. Device may be unreachable.")
                QMessageBox.critical(None, 'Error', f"Ping failed for {ip_address}. Device may be unreachable.")
                return

            # Log connection attempt
            self.logger.info(f"Attempting to connect to {ip_address}:{port}")

            # Check if the port is open
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(3)  # Set a timeout for the connection attempt
                if sock.connect_ex((ip_address, int(port))) != 0:
                    self.logger.error(f"Port {port} on {ip_address} is not open.")
                    QMessageBox.critical(None, 'Error', f"Port {port} on {ip_address} is not open.")
                    return

            # Create a socket and connect
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((ip_address, int(port)))
                self.logger.info(f"Connected to {ip_address}:{port}")

                # Send the command
                client_socket.sendall(command.encode('utf-8'))
                self.logger.info(f"Command sent successfully: {command}")

        except Exception as e:
            # Log the error
            self.logger.error(f"Error while sending command to {ip_address}:{port}: {e}")
            QMessageBox.critical(None, 'Error', f"Error: {e}")

    def send_win32print(self, printer_name, raw_data):
        self.logger.info(f"Attempting to send raw data to printer '{printer_name}' using win32print.")
        try:
            # Open the printer
            self.logger.debug(f"Opening printer: {printer_name}")
            printer = win32print.OpenPrinter(printer_name)

            # Start a print job
            job_info = ("Print Job", None, "RAW")
            job_id = win32print.StartDocPrinter(printer, 1, job_info)
            self.logger.info(f"Print job started with ID: {job_id}")

            # Start a new page
            win32print.StartPagePrinter(printer)
            self.logger.debug("Page started.")

            # Send raw data to the printer
            win32print.WritePrinter(printer, raw_data.encode())
            self.logger.info(f"Data sent to printer '{printer_name}': {raw_data}")

            # End the page and the job
            win32print.EndPagePrinter(printer)
            self.logger.debug("Page ended.")
            win32print.EndDocPrinter(printer)
            self.logger.info("Print job ended successfully.")

        except Exception as e:
            self.logger.error(f"Error while printing to '{printer_name}': {e}")
            QMessageBox.critical(None, 'Error', f"Error: {e}")

        finally:
            # Close the printer connection
            win32print.ClosePrinter(printer)
            self.logger.info(f"Printer connection closed for '{printer_name}'.")
