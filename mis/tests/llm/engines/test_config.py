import unittest
from unittest.mock import patch, mock_open

from mis.args import GlobalArgs
from mis.llm.engines.config import ConfigParser


class TestConfigParser(unittest.TestCase):

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='engine_type: vllm\nmodel: test_model\n')
    def test_engine_config_loading_valid_config(self, mock_file, mock_exists):
        args = GlobalArgs()
        args.engine_type = 'vllm'
        args.mis_config = 'test_config'
        args.model = 'test_model'

        parser = ConfigParser(args)
        updated_args = parser.engine_config_loading()

        self.assertEqual(updated_args.engine_type, 'vllm')
        self.assertEqual(updated_args.model, 'test_model')
        mock_file.assert_called_once()

    @patch('os.path.exists', return_value=False)
    def test_engine_config_loading_invalid_config_path(self, mock_exists):
        args = GlobalArgs()
        args.engine_type = 'vllm'
        args.mis_config = 'non_existent_config'
        args.model = 'test_model'

        parser = ConfigParser(args)
        updated_args = parser.engine_config_loading()

        self.assertEqual(updated_args.engine_type, 'vllm')
        self.assertEqual(updated_args.model, 'test_model')

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='engine_type: invalid_engine\nmodel: test_model\n')
    def test_engine_config_loading_invalid_engine_type(self, mock_file, mock_exists):
        args = GlobalArgs()
        args.engine_type = 'invalid_engine'
        args.mis_config = 'test_config'
        args.model = 'test_model'

        parser = ConfigParser(args)
        updated_args = parser.engine_config_loading()

        self.assertEqual(updated_args.engine_type, 'invalid_engine')
        self.assertEqual(updated_args.model, 'test_model')

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='model: test_model\n')
    def test_engine_config_loading_missing_engine_type(self, mock_file, mock_exists):
        args = GlobalArgs()
        args.engine_type = None
        args.mis_config = 'test_config'
        args.model = 'test_model'

        parser = ConfigParser(args)
        updated_args = parser.engine_config_loading()

        self.assertIsNone(updated_args.engine_type)
        self.assertEqual(updated_args.model, 'test_model')

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='engine_type: vllm\n')
    def test_engine_config_loading_missing_model(self, mock_file, mock_exists):
        args = GlobalArgs()
        args.engine_type = 'vllm'
        args.mis_config = 'test_config'
        args.model = ''

        parser = ConfigParser(args)
        updated_args = parser.engine_config_loading()

        self.assertEqual(updated_args.engine_type, 'vllm')
        self.assertEqual(updated_args.model, '')

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='engine_type: vllm\nmodel: invalid_model\n')
    def test_engine_config_loading_invalid_model(self, mock_file, mock_exists):
        args = GlobalArgs()
        args.engine_type = 'vllm'
        args.mis_config = 'test_config'
        args.model = 'invalid_model'

        parser = ConfigParser(args)
        updated_args = parser.engine_config_loading()

        self.assertEqual(updated_args.engine_type, 'vllm')
        self.assertEqual(updated_args.model, 'invalid_model')

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='engine_type: vllm\nmodel: test_model\n')
    def test_engine_config_loading_valid_model(self, mock_file, mock_exists):
        args = GlobalArgs()
        args.engine_type = 'vllm'
        args.mis_config = 'test_config'
        args.model = 'test_model'

        parser = ConfigParser(args)
        updated_args = parser.engine_config_loading()

        self.assertEqual(updated_args.engine_type, 'vllm')
        self.assertEqual(updated_args.model, 'test_model')


if __name__ == '__main__':
    unittest.main()
