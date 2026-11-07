"""Module for handling logging"""

import traceback
from bcsfe import core
import time


class Logger:
    def __init__(self, path: core.Path | None):
        """
        Initializes a Logger object
        """
        if path is None:
            path = Logger.get_log_path()
        self.log_file = path
        try:
            self.log_data = self.log_file.read(True).split(b"\n")
        except Exception as _:
            self.log_data = None

    @staticmethod
    def get_log_path() -> core.Path:
        return core.Path.get_state_folder().add("bcsfe.log")

    def get_time(self) -> str:
        """
        Returns the current time in the format: "HH:MM:SS"

        Returns:
            str: The current time
        """
        return time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())

    def log_info(self, message: str):
        """
        Logs an info message

        Args:
            message (str): The message to log
        """
        if self.log_data is None:
            return
        self.log_data.append(core.Data(f"[INFO]::{self.get_time()} - {message}"))
        self.write()

    def log_error(self, message: str):
        """
        Logs an error message

        Args:
            message (str): The message to log
        """
        if self.log_data is None:
            return
        self.log_data.append(core.Data(f"[ERROR]::{self.get_time()} - {message}"))
        self.write()

    def write(self):
        """
        Writes the log data to the log file
        """
        if self.log_data is None:
            return
        self.log_file.write(core.Data.from_many(self.log_data, core.Data("\n")).strip())

    @staticmethod
    def get_traceback() -> str:
        """
        Gets the traceback of the last exception

        Returns:
            str: The traceback
        """
        tb = traceback.format_exc()
        if tb == "NoneType: None\n":
            return ""
        return tb
