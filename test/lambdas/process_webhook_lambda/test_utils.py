import unittest
from lambdas.process_webhook_lambda.utils import *

class TestUtils(unittest.TestCase):
    """
    Class to test all functions in utils.py
    """
    def test_convert_json_to_csv_empty_input(self):
        input_data = []
        expected_result = ''
        csv_string = convert_json_to_csv(input_data)
        self.assertEqual(csv_string, expected_result)

    def test_convert_json_to_csv(self):
        """
        Test convert json to csv from utils
        """
        input_data = [
            {
                'id': 'xyz',
                'name': 'xyz'
            },
            {
                'id': 'abc',
                'name': 'abc'
            }
        ]
        expected_result = 'id,name\r\nxyz,xyz\r\nabc,abc\r\n'
        csv_string = convert_json_to_csv(input_data)
        self.assertEqual(csv_string, expected_result)

    def test_split_list_based_on_key(self):
        """
        Test split list based on key value
        """
        input_data = [
            {
                'id': 'xyz',
                'name': 'xyz'
            },
            {
                'id': 'xyz',
                'name': 'abc'
            },
            {
                'id': 'test',
                "name": "test"
            }
        ]
        expected_result = {
            'xyz': [
                {
                    'id': 'xyz',
                    'name': 'xyz'
                },
                {
                    'id': 'xyz',
                    'name': 'abc'
                }
            ],
            'test': [
                {
                    'id': 'test',
                    "name": "test"
                }
            ]
        }
        result = split_list_based_on_key(data=input_data, key='id')
        self.assertEqual(result, expected_result)
