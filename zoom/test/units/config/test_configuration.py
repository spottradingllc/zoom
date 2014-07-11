import unittest


class TestConfiguration(unittest.TestCase):
    def setUp(self):
        self.sample_configuration ="""
        local:
            host: local_config
        test:
            host: test_config"""
        #YamlConfiguration.configurations = {}

    # def test_should_return_environment_specific_configuration(self):
    #     with patch('zoom.configuration.read', mock_open(read_data = self.sample_configuration), create=True):
    #         config = Configuration._load_from_file('sample_yaml_file', 'test')
    #     self.assertEqual('test_config', config.value_for('host'))
    #
    #
    # def test_should_not_load_a_file_if_already_loaded(self):
    #     with patch('ats.config.yaml_configuration.open', mock_open(read_data = self.sample_configuration), create=True) as mock_file_open:
    #         YamlConfiguration._load_from_file('sample_yaml_file', 'local')
    #         YamlConfiguration._load_from_file('sample_yaml_file', 'test')
    #     mock_file_open.assert_called_once_with('sample_yaml_file', 'r')
    #
    #
    # @patch('ats.config.yaml_configuration.os')
    # def test_should_default_to_local_env(self, os):
    #     os.getenv.return_value = 'local'
    #     with patch('ats.config.yaml_configuration.open', mock_open(read_data = self.sample_configuration), create=True):
    #         config = YamlConfiguration._load_from_file('sample_yaml_file')
    #     os.getenv.assert_called_once_with('APP_ENV', 'local')
    #     self.assertEqual('local_config', config.value_for('host'))
