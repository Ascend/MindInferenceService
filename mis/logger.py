# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import getpass
import inspect
import logging
import os
import pwd
import re
import stat
import time
from enum import Enum
from logging import Logger
from logging.config import dictConfig
from logging.handlers import RotatingFileHandler
from typing import Optional, Callable

from mis import envs

MIS_LOG_LEVEL = envs.MIS_LOG_LEVEL
MIS_LOG_PREFIX = "log_mis_disk_"
MIS_LOG_PATH = "/home/HwHiAiUser/tmp/log"
DEFAULT_UMASK = 0o027
MIS_CALLER_INSPECT_DEPTH = 20
MIS_MAX_ARCHIVE_COUNT = 5
MIS_MAX_LOG_STORED = 36
MIS_ARCHIVE_SIZE = 50 * 1024 * 1024
MIS_DEFAULT_USER_ID = 1000

_FORMAT = "%(levelname)s %(asctime)s [MIS] [%(filename)s:%(lineno)d] %(funcName)s: %(message)s"
_DATE_FORMAT = "%m-%d %H:%M:%S"

DEFAULT_LOGGING_CONFIG = {
    "formatters": {
        "mis": {
            "class": "mis.utils.logger_utils.NewLineFormatter",
            "datefmt": _DATE_FORMAT,
            "format": _FORMAT,
        },
    },
    "handlers": {
        "mis": {
            "class": "logging.StreamHandler",
            "formatter": "mis",
            "level": MIS_LOG_LEVEL,
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "mis": {
            "handlers": ["mis"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
    "version": 1,
    "disable_existing_loggers": False
}


class LogType(Enum):
    DEFAULT = 0
    OPERATION = 1
    SERVICE = 2


class RotatingFileWithArchiveHandler(RotatingFileHandler):
    """Custom RotatingFileHandler that supports log rotation and limits the number of rotated files"""

    def __init__(self, filepath: str, mode: str = 'a', max_bytes: int = 0, backup_count: int = 0,
                 encoding: str = None, delay: bool = False, log_dir: str = MIS_LOG_PATH) -> None:
        """Initialize the RotatingFileWithArchiveHandler.
        Args:
            filepath (str): Name of the log file
            mode (str): File mode for opening the log file
            max_bytes (int): Maximum size of log file before rotation
            backup_count (int): Maximum number of backup files to keep
            encoding (str): Encoding to use for the file
            delay (bool): Whether to delay file opening until first write
            log_dir (str): Directory to store log files
        """
        super().__init__(filepath, mode, max_bytes, backup_count, encoding, delay)
        self.log_dir = log_dir
        self.base_filename = os.path.basename(filepath)
        self.backup_count = backup_count

        original_umask = os.umask(DEFAULT_UMASK)
        try:
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir)
            else:
                current_mode = os.stat(self.log_dir).st_mode
                desired_mode = stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP  # 750
                if stat.S_IMODE(current_mode) != desired_mode:
                    os.chmod(self.log_dir, desired_mode)
        except OSError as e:
            raise OSError(f"Error occurred while checking or creating log directory: {e}") from e
        finally:
            os.umask(original_umask)
        # Set permissions for current log file (read-write 640)
        self._set_file_permissions(filepath, is_archive=False)

        self._cleanup_old_log_files()

    @staticmethod
    def _get_current_uid():
        """Get the current user ID.
        Returns:
            int: The user ID of the current process
        """
        try:
            current_username = getpass.getuser()
            current_uid = pwd.getpwnam(current_username).pw_uid
        except KeyError:
            current_uid = MIS_DEFAULT_USER_ID
        return current_uid

    @staticmethod
    def _collect_log_files(log_dir, current_uid):
        """Collect log files in the specified directory that belong to the current user.
        Args:
            log_dir (str): Directory to search for log files
            current_uid (int): User ID of the current process
        Returns:
            list: List of tuples containing file paths and modification times
        """
        log_files = []
        for f in os.listdir(log_dir):
            if f.startswith(MIS_LOG_PREFIX):
                filepath = os.path.join(log_dir, f)
                stat_info = os.stat(filepath)
                file_uid = stat_info.st_uid
                mtime = stat_info.st_mtime  # modification time
                if file_uid == current_uid:
                    log_files.append((filepath, mtime))
        return log_files

    @staticmethod
    def _remove_excess_files(log_files, max_count):
        """Remove excess log files that exceed the maximum count.
        Args:
            log_files (list): List of tuples containing file paths and modification times
            max_count (int): Maximum number of log files to keep
        """
        excess_count = len(log_files) - max_count
        if excess_count > 0:
            for i in range(excess_count):
                filepath, _ = log_files[i]
                try:
                    os.remove(filepath)
                except OSError as e:
                    logger = logging.getLogger("mis")
                    logger.error(f"Error occurred while cleaning up old log files: {e}")

    @staticmethod
    def _set_file_owner(filepath: str) -> None:
        """Set file owner to current user or uid 1000.

        Args:
            filepath (str): Path to the file
        """
        try:
            username = getpass.getuser()
            uid = pwd.getpwnam(username).pw_uid
        except KeyError:
            # If we can't determine current user, use uid 1000
            uid = MIS_DEFAULT_USER_ID

        try:
            # Set file owner
            os.chown(filepath, uid, -1)
        except PermissionError as e:
            raise PermissionError(f"Error setting owner for log file: {e}") from e

    def doRollover(self) -> None:
        """Perform log rotation and remove excess rotated log files"""
        try:
            super().doRollover()
            self._set_file_permissions(self.baseFilename, is_archive=False)
        except PermissionError:
            rotated_files = []
            for i in range(1, self.backup_count + 1):
                rotated_filename = f"{self.baseFilename}.{i}"
                if os.path.exists(rotated_filename):
                    rotated_files.append(rotated_filename)
            for rotated_file in rotated_files:
                self._set_file_permissions(rotated_file, is_archive=True)

            super().doRollover()
        finally:
            self._set_file_permissions(self.baseFilename, is_archive=False)

        # Set permissions for rotated log files (read-only 440)
        self._set_rotated_files_permissions()

        self._cleanup_old_log_files()

    def _set_rotated_files_permissions(self) -> None:
        """Set read-only permissions for rotated log files"""
        try:
            for f in os.listdir(self.log_dir):
                # Check if file is a rotated log file (e.g., xxx.log.1, xxx.log.2, etc.)
                if (f.startswith(self.base_filename) and
                        f != os.path.basename(self.baseFilename) and  # Exclude current log file
                        len(f) > len(os.path.basename(self.baseFilename))):  # Check if it's a rotated file
                    filepath = os.path.join(self.log_dir, f)
                    # Set read-only permissions (440) for rotated log files
                    os.chmod(filepath, stat.S_IRUSR | stat.S_IRGRP)  # 0440
        except OSError as e:
            raise OSError(f"Error setting permissions for rotated log files: {e}") from e

    def _set_file_permissions(self, filepath: str, is_archive: bool = False) -> None:
        """Set file permissions based on whether it's a current log or archived log.
        Args:
            filepath (str): Path to the file
            is_archive (bool): Whether the file is an archived log
        """
        try:
            if is_archive:
                # Archived logs: read-only permissions (440)
                os.chmod(filepath, stat.S_IRUSR | stat.S_IRGRP)  # 0440
            else:
                # Current logs: read-write permissions (640)
                os.chmod(filepath, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)  # 0640

            # Try to set file owner to current user or uid 1000
            self._set_file_owner(filepath)
        except PermissionError as e:
            raise PermissionError(f"Error setting permissions for log file: {e}") from e

    def _cleanup_old_log_files(self):
        """Clean up old log files when count exceeds max_archive_count.
        Only delete files with the same owner as the current process.
        """
        try:
            current_uid = self._get_current_uid()
            log_files = self._collect_log_files(self.log_dir, current_uid)
            log_files.sort(key=lambda x: x[1])  # Sort by modification time (oldest first)
            self._remove_excess_files(log_files, MIS_MAX_LOG_STORED)
        except OSError as e:
            logger = logging.getLogger("mis")
            logger.error(f"Error occurred while cleaning up old log files: {e}")


class CallStackFilter(logging.Filter):
    """Custom filter to add call stack information to log records."""
    def filter(self, record: logging.LogRecord) -> bool:
        """ Filter method to add call stack information to log records.
        Args:
            record (logging.LogRecord): Log record
        """
        # Get real caller info
        filename, lineno, function_name = _find_caller_info()
        record.filename = filename
        record.lineno = lineno
        record.funcName = function_name
        return True


class LogManager:
    def __init__(self, log_dir: str = MIS_LOG_PATH, max_archive_count: int = MIS_MAX_ARCHIVE_COUNT,
                 archive_size: int = MIS_ARCHIVE_SIZE, log_type: LogType = LogType.DEFAULT) -> None:
        """ Initialize the LogManager.
        Args:
            log_dir: Directory to store log files
            max_archive_count: Maximum number of log files to keep
            archive_size: Maximum size of a log file before archiving
            log_type (LogType): Used to log type, where DEFAULT, OPERATION, and SERVICE.
        """
        self.log_dir: str = log_dir
        self.max_archive_count: int = max_archive_count
        self.archive_size: int = archive_size
        self.logger: Optional[Logger] = None
        self.log_type = log_type

        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def setup_logger(self, name: str) -> Logger:
        """Set up the logger

        Args:
            name (str): Name of the logger

        Returns:
            Logger: Configured logger instance
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if self.log_type == LogType.OPERATION else MIS_LOG_LEVEL)

        # Clear existing handlers
        self.logger.handlers.clear()

        # Create console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(_FORMAT, _DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.DEBUG if self.log_type == LogType.OPERATION else MIS_LOG_LEVEL)
        self.logger.addHandler(console_handler)

        # Create file handler
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        if self.log_type == LogType.DEFAULT:
            log_filename = os.path.join(self.log_dir, f"{MIS_LOG_PREFIX}{timestamp}.log")
        elif self.log_type == LogType.OPERATION:
            log_filename = os.path.join(self.log_dir, f"{MIS_LOG_PREFIX}operation_{timestamp}.log")
        elif self.log_type == LogType.SERVICE:
            log_filename = os.path.join(self.log_dir, f"{MIS_LOG_PREFIX}service_{timestamp}.log")
        else:
            raise ValueError("log_type must be LogType.DEFAULT, LogType.OPERATION, or LogType.SERVICE")

        file_handler = RotatingFileWithArchiveHandler(
            log_filename,
            max_bytes=self.archive_size,
            backup_count=self.max_archive_count,
            log_dir=self.log_dir
        )
        file_formatter = logging.Formatter(_FORMAT, _DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG if self.log_type == LogType.OPERATION else MIS_LOG_LEVEL)
        self.logger.addHandler(file_handler)

        # Add call stack filter
        callstack_filter = CallStackFilter()
        console_handler.addFilter(callstack_filter)
        file_handler.addFilter(callstack_filter)

        # Prevent log propagation to parent loggers
        self.logger.propagate = False

        return self.logger


def _find_caller_info() -> tuple:
    """Find Real caller info"""
    frame = inspect.currentframe()
    result = ("unknown", 0, "unknown")
    # Find first non-logging module caller
    depth = 1
    try:
        while frame and depth < MIS_CALLER_INSPECT_DEPTH:  # Avoid infinite loop
            filename = frame.f_code.co_filename
            function_name = frame.f_code.co_name
            # Ignore logging system internal files
            ignore_files = ["logger", "logging", "logging/__init__", __file__]
            if not any(ignore_name in filename for ignore_name in ignore_files):
                result = (os.path.basename(filename), frame.f_lineno, function_name)
                break
            frame = frame.f_back
            depth += 1
    finally:
        del frame  # Avoid circular reference
    return result


class EnhancedLogger:
    def __init__(self, logger: Logger) -> None:
        """ Initialize enhanced logger
        Args:
            logger (Logger): Logger instance
        """
        self.logger: Logger = logger
        self._caller_filename = None
        self._caller_lineno = None
        self._caller_func_name = None

    def debug(self, message: str) -> None:
        """Log debug message to both console and disk
        Args:
            message (str): Message to log
        """
        original_find_caller = self._find_caller_backup(message)
        self.logger.debug(_filter_invalid_chars(message))
        self.logger.findCaller = original_find_caller

    def info(self, message: str) -> None:
        """Log info message to both console and disk
        Args:
            message (str): Message to log
        """
        original_find_caller = self._find_caller_backup(message)
        self.logger.info(_filter_invalid_chars(message))
        self.logger.findCaller = original_find_caller

    def warning(self, message: str) -> None:
        """Log warning message to both console and disk
        Args:
            message (str): Message to log
        """
        original_find_caller = self._find_caller_backup(message)
        self.logger.warning(_filter_invalid_chars(message))
        self.logger.findCaller = original_find_caller

    def error(self, message: str) -> None:
        """Log error message to both console and disk
        Args:
            message (str): Message to log
        """
        original_find_caller = self._find_caller_backup(message)
        self.logger.error(_filter_invalid_chars(message))
        self.logger.findCaller = original_find_caller

    def critical(self, message: str) -> None:
        """Log Critical message to both console and disk
        Args:
            message (str): Message to log
        """
        original_find_caller = self._find_caller_backup(message)
        self.logger.critical(_filter_invalid_chars(message))
        self.logger.findCaller = original_find_caller

    def _custom_find_caller(self, stack_info: bool, stack_level: int) -> tuple:
        """Custom findCaller implementation that returns predetermined caller info.
        Args:
            stack_info (bool): Whether to include stack information.
            stack_level (int): The stack level to determine the caller's depth.

        Returns:
            tuple: Caller's file name, line number, function name, and additional information (None).
        """
        return (self._caller_filename, self._caller_lineno, self._caller_func_name, None)

    def _find_caller_backup(self, message: str) -> Callable:
        """Log a message at the specified level
        Args:
            level (str): The log level ("debug", "info", "warning", or "error").
            message (str): The message to log.
        """
        if not isinstance(message, str):
            raise TypeError("Log message must be a string")
        self._caller_filename, self._caller_lineno, self._caller_func_name = _find_caller_info()
        original_find_caller = self.logger.findCaller
        self.logger.findCaller = self._custom_find_caller
        return original_find_caller


def _filter_invalid_chars(s: str) -> str:
    """Filter invalid chars in original str
    Args:
        s (str): original log message
    Returns:
        str: filtered log message
    """
    invalid_chars = [
        '\n', '\f', '\r', '\b', '\t', '\v',
        '\u000D', '\u000A', '\u000C', '\u000B',
        '\u0009', '\u0008', '\u0007'
    ]
    pattern = '[' + re.escape(''.join(invalid_chars)) + ']+'
    return re.sub(pattern, ' ', s)


def _configure_mis_root_logger() -> None:
    dictConfig(DEFAULT_LOGGING_CONFIG)


_configure_mis_root_logger()


def init_logger(name: str, log_dir: Optional[str] = None,
                log_type: LogType = LogType.DEFAULT) -> EnhancedLogger:
    """Initialize an enhanced logger that logs to both console and disk
    Args:
        name (str): Name of the logger
        log_dir (str): Directory to store log files
        log_type (LogType): Used to log type, where DEFAULT, OPERATION, and SERVICE.
    """
    if log_dir is None:
        log_dir = os.path.join(os.path.expanduser('~'), "tmp", "log")
    if not isinstance(name, str) or not isinstance(log_dir, str):
        raise ValueError("Invalid logger name or log directory")
    if log_dir is not None and not isinstance(log_dir, str):
        raise ValueError("Log directory must be a string or None")
    if os.path.islink(log_dir):
        raise OSError("Log directory cannot be a symbolic link")
    if not isinstance(log_type, LogType):
        raise ValueError("log_type must be a LogType enum")
    log_manager = LogManager(log_dir=log_dir, log_type=log_type)
    logger = log_manager.setup_logger(name)
    return EnhancedLogger(logger)
