import os
import unittest
from unittest.mock import patch

import json

from mis.utils.utils import (
    ConfigChecker,
    read_json,
    write_json,
    check_dependencies
)


class TestConfigChecker(unittest.TestCase):
    def test_is_value_in_range(self):
        # Test if value is within the valid range
        self.assertTrue(ConfigChecker.is_value_in_range("test", 5, 1, 10))
        # Test boundary condition: minimum value
        self.assertTrue(ConfigChecker.is_value_in_range("test", 1, 1, 10))
        # Test boundary condition: maximum value
        self.assertTrue(ConfigChecker.is_value_in_range("test", 10, 1, 10))
        # Test value below the minimum
        self.assertFalse(ConfigChecker.is_value_in_range("test", 0, 1, 10))
        # Test value above the maximum
        self.assertFalse(ConfigChecker.is_value_in_range("test", 11, 1, 10))

    def test_is_value_in_enum(self):
        valid_values = [1, 2, 3]
        # Test valid value
        self.assertTrue(ConfigChecker.is_value_in_enum("test", 2, valid_values))
        # Test invalid value
        self.assertFalse(ConfigChecker.is_value_in_enum("test", 4, valid_values))

    def test_check_string_input(self):
        # Test valid string
        ConfigChecker.check_string_input("test", "valid_string")
        # Test empty string
        with self.assertRaises(ValueError):
            ConfigChecker.check_string_input("test", "")
        # Test string with special characters
        with self.assertRaises(ValueError):
            ConfigChecker.check_string_input("test", "invalid!string")


class TestFileOperations(unittest.TestCase):
    def setUp(self):
        self.test_json_path = "test.json"
        self.test_data = {"key": "value"}

    def tearDown(self):
        if os.path.exists(self.test_json_path):
            os.remove(self.test_json_path)

    def test_read_json(self):
        # Create a test JSON file
        with open(self.test_json_path, 'w') as f:
            json.dump(self.test_data, f)
        # Test reading JSON file
        result = read_json(self.test_json_path)
        self.assertEqual(result, self.test_data)

    def test_write_json(self):
        # Test writing JSON file
        write_json(self.test_json_path, self.test_data)
        # Verify file content
        with open(self.test_json_path, 'r') as f:
            result = json.load(f)
        self.assertEqual(result, self.test_data)


class TestSystemFunctions(unittest.TestCase):
    @patch("mis.utils.utils.logger.warning")
    @patch("mis.utils.utils.importlib")
    def test_check_dependencies(self, mock_importlib, mock_logger):
        # Test all dependencies are installed
        mock_importlib.util.find_spec.return_value = True
        with self.assertNoLogs(level="WARN"):
            check_dependencies(["package1", "package2"])

        # Test missing dependencies
        mock_importlib.util.find_spec.return_value = None
        check_dependencies(["package1", "package2"])
        mock_logger.assert_called_once_with("The following required packages are missing: package1, package2")


if __name__ == "__main__":
    unittest.main()
