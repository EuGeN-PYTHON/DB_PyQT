import sys
import os
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))

from client_server.client import Client


class TestClass(unittest.TestCase):

    def test_def_presence(self):
        test = Client.get_presence()
        test['time'] = 1.1
        self.assertEqual(test, {'action': 'presence', 'time': 1.1, 'user': {'account_name': 'Guest'}})

    def test_200_ans(self):
        self.assertEqual(Client.response_analyze({'response': 200}), '200 : OK')

    def test_400_ans(self):
        self.assertEqual(Client.response_analyze({'response': 400, 'error': 'Bad Request'}), '400 : Bad Request')

    def test_no_response(self):
        self.assertRaises(ValueError, Client.response_analyze, {'error': 'Bad Request'})


if __name__ == '__main__':
    unittest.main()


