import sys
import os
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))

from client_server.server import Server


class TestForServer(unittest.TestCase):
    incorrect_dict = {
        'response': 400,
        'error': 'Bad Request'
    }
    correct_dict = {'response': 200}

    def test_no_action(self):
        self.assertEqual(Server.check_data_client(
            {'time': '1.1', 'user': {'account_name': 'Guest'}}), self.incorrect_dict)

    def test_wrong_action(self):
        self.assertEqual(Server.check_data_client(
            {'action': 'Wrong', 'time': '1.1', 'user': {'account_name': 'Guest'}}), self.incorrect_dict)

    def test_no_time(self):
        self.assertEqual(Server.check_data_client(
            {'action': 'presence', 'user': {'account_name': 'Guest'}}), self.incorrect_dict)

    def test_no_user(self):
        self.assertEqual(Server.check_data_client(
            {'action': 'presence', 'time': '1.1'}), self.incorrect_dict)

    def test_unknown_user(self):
        self.assertEqual(Server.check_data_client(
            {'action': 'presence', 'time': '1.1', 'user': {'account_name': 'Pavel'}}), self.incorrect_dict)

    def test_ok_check(self):
        self.assertEqual(Server.check_data_client(
            {'action': 'presence', 'time': '1.1', 'user': {'account_name': 'Guest'}}), self.correct_dict)


if __name__ == '__main__':
    unittest.main()
