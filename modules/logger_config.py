import logging
import os
from logging.handlers import RotatingFileHandler
import json

class NoOpLogger:
    # This class will be used when logging is disabled, and it does nothing when methods are called
    def info(self, msg, *args, **kwargs):
        pass

    def debug(self, msg, *args, **kwargs):
        pass

    def warning(self, msg, *args, **kwargs):
        pass

    def error(self, msg, *args, **kwargs):
        pass

    def critical(self, msg, *args, **kwargs):
        pass

    def exception(self, msg, *args, **kwargs):
        pass


def setup_logger(window_name, log_file='C:/barcode/barcode_app.log'):
    config_path = r"C:\barcode\barcode.json"
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            
            if config.get('logging', False):  # Check if logging is enabled in the config file
                log_dir = os.path.dirname(log_file)  # Extract the directory from the full path
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)  # Create the directory if it doesn't exist

                # Create a logger for the specific window
                logger = logging.getLogger(window_name)
                logger.setLevel(logging.DEBUG)  # Set the minimum log level

                # Create handlers
                file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)  # 5MB per file
                file_handler.setLevel(logging.DEBUG)

                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.INFO)

                # Set a formatter for the handlers
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                file_handler.setFormatter(formatter)
                console_handler.setFormatter(formatter)

                # Add handlers to the logger
                if not logger.handlers:  # Prevent duplicate handlers
                    logger.addHandler(file_handler)
                    logger.addHandler(console_handler)

                return logger

            else:
                print("Logging is disabled in the configuration file.")
                return NoOpLogger()  # Return the NoOpLogger if logging is disabled

    except FileNotFoundError:
        print(f'Configuration file not found at {config_path}')
        return NoOpLogger()  # Return the NoOpLogger if the file doesn't exist
    except json.JSONDecodeError:
        print('Error parsing the configuration file.')
        return NoOpLogger()  # Return the NoOpLogger if there's a JSON error
    except KeyError as e:
        print(f'Missing key in configuration file: {e}')
        return NoOpLogger()  # Return the NoOpLogger if there's a missing key


