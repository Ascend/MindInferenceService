# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import logging
import os
import unittest
from unittest.mock import patch
from mis.logger import init_logger, _filter_invalid_chars

MIS_LOG_PATH = "/log/mis"


class TestLogger(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for log files
        self.temp_log_dir = os.path.join(MIS_LOG_PATH, 'tmp2test')
        os.makedirs(self.temp_log_dir, exist_ok=True)

    def tearDown(self):
        # Clean up the temporary directory
        for root, dirs, files in os.walk(self.temp_log_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.temp_log_dir)

    def test_init_logger(self):
        from mis.logger import EnhancedLogger
        logger = init_logger('test_logger', log_dir=self.temp_log_dir)
        self.assertIsInstance(logger, EnhancedLogger)
        self.assertIsInstance(logger.logger, logging.Logger)

    def test_invalid_name_or_log_dir(self):
        with self.assertRaises(ValueError):
            init_logger(123, log_dir=self.temp_log_dir)
        with self.assertRaises(ValueError):
            init_logger('test_logger', log_dir=123)

    def test_invalid_log_type(self):
        with self.assertRaises(ValueError):
            init_logger('test_logger', log_dir=self.temp_log_dir, log_type='invalid')

    def test_log_dir_default_value(self):
        logger = init_logger('test_logger')
        user_home = os.path.expanduser('~')
        found_file_handler = False
        for handler in logger.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                self.assertTrue(handler.baseFilename.startswith(user_home))
                found_file_handler = True
                break
        self.assertTrue(found_file_handler, "No FileHandler found in logger")

    def test_return_type(self):
        from mis.logger import EnhancedLogger
        logger = init_logger('test_logger', log_dir=self.temp_log_dir)
        self.assertIsInstance(logger, EnhancedLogger)
        self.assertIsInstance(logger.logger, logging.Logger)

    def test_log_file_creation(self):
        logger = init_logger('test_log', log_dir=self.temp_log_dir)
        logger.info('This is a test message')
        log_files = [f for f in os.listdir(self.temp_log_dir) if f.startswith('log_mis_')]
        self.assertGreater(len(log_files), 0)

    def test_log_messages(self):
        from mis.logger import MIS_LOG_PREFIX
        logger = init_logger('test_logger', log_dir=self.temp_log_dir)
        logger.debug('This is a debug message')
        logger.info('This is an info message')
        logger.warning('This is a warning message')
        logger.error('This is an error message')

        # Check if log files are created
        log_files = [f for f in os.listdir(self.temp_log_dir) if f.startswith(MIS_LOG_PREFIX)]
        self.assertGreater(len(log_files), 0)

    def test_log_file_cleanup(self):
        from mis.logger import MIS_LOG_PREFIX, MIS_MAX_ARCHIVE_COUNT
        logger = init_logger('test_logger', log_dir=self.temp_log_dir)
        for root, dirs, files in os.walk(self.temp_log_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        # Create more log files than the maximum allowed
        for i in range(MIS_MAX_ARCHIVE_COUNT + 1):
            with open(os.path.join(self.temp_log_dir, f"{MIS_LOG_PREFIX}20231001_120000.log.{i}"), 'w') as f:
                f.write('Test log content')
        # Trigger a log message to force cleanup
        logger.info('This is a debug message to trigger cleanup')

        # Check if the oldest log files are removed
        log_files = [f for f in os.listdir(self.temp_log_dir) if f.startswith(MIS_LOG_PREFIX)]
        self.assertEqual(len(log_files), MIS_MAX_ARCHIVE_COUNT + 1)

    def test_log_file_permissions(self):
        from mis.logger import init_logger
        with patch('os.chmod') as mock_chmod:
            logger = init_logger('test_logger', log_dir=self.temp_log_dir)
            rotated_log_files = [os.path.join(self.temp_log_dir, f) for f in os.listdir(self.temp_log_dir)]
            logger.info('This is a info message to check permissions')
            mock_chmod.assert_called_with(rotated_log_files[0], 0o640)

    def test_log_file_owner(self):
        from mis.logger import init_logger
        with patch('os.chown') as mock_chown:
            logger = init_logger('test_logger', log_dir=self.temp_log_dir)
            rotated_log_files = [os.path.join(self.temp_log_dir, f) for f in os.listdir(self.temp_log_dir)]
            logger.info('This is a info message to check owner')
            mock_chown.assert_called_with(rotated_log_files[0], os.getuid(), -1)

    def test_call_stack_filter(self):
        from mis.logger import init_logger
        logger = init_logger('test_call_stack', log_dir=self.temp_log_dir)
        logger.info('This is a info message to check call stack filter')
        # Check if the log message contains the correct file and line number
        with open(os.path.join(self.temp_log_dir, os.listdir(self.temp_log_dir)[-1])) as f:
            log_content = f.read()
            # The logger will filter the logger field when nested file names are obtained,
            # or test file names that only contain "log".
            self.assertIn('test_log.py', log_content)
            self.assertIn('This is a info message to check call stack filter', log_content)

    def test_filter_invalid_chars_no_invalid_chars(self):
        # Test case for no invalid characters
        message = "This is a test message."
        self.assertEqual(_filter_invalid_chars(message), message)

    def test_filter_invalid_chars_single_invalid_char(self):
        # Test case for a single invalid character
        message = "This is a test message.\n"
        self.assertEqual(_filter_invalid_chars(message), "This is a test message. ")

    def test_filter_invalid_chars_multiple_invalid_chars(self):
        # Test case for multiple invalid characters
        message = "This is a test message.\n\r\t"
        self.assertEqual(_filter_invalid_chars(message), "This is a test message. ")

    def test_filter_invalid_chars_all_invalid_chars(self):
        # Test case for all invalid characters
        message = "\n\r\t\b\f\v\u000D\u000A\u000C\u000B\u0009\u0008\u0007"
        self.assertEqual(_filter_invalid_chars(message), " ")

    def test_filter_invalid_chars_mixed_valid_and_invalid_chars(self):
        # Test case for mixed valid and invalid characters
        message = "This\nis\ra\ntest\tmessage."
        self.assertEqual(_filter_invalid_chars(message), "This is a test message.")

    def test_filter_invalid_chars_empty_string(self):
        # Test case for an empty string
        message = ""
        self.assertEqual(_filter_invalid_chars(message), "")

    def test_filter_invalid_chars_only_spaces(self):
        # Test case for only spaces
        message = "   "
        self.assertEqual(_filter_invalid_chars(message), "   ")

    def test_filter_invalid_chars_unicode_invalid_chars(self):
        # Test case for Unicode invalid characters
        message = "This is a test message.\u000D\u000A"
        self.assertEqual(_filter_invalid_chars(message), "This is a test message. ")


if __name__ == '__main__':
    unittest.main()