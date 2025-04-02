import logging
from datetime import datetime


class AppLogger:
    def __init__(self, name: str, log_file: str = 'app.log'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # File handler
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def log(self, level: str, message: str, context: dict = None):
        log_message = f"{message} | Context: {context}" if context else message
        getattr(self.logger, level)(log_message)