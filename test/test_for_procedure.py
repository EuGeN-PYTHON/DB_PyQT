import sys
import os
import unittest
import json

sys.path.append(os.path.join(os.getcwd(), '..'))
from client_server.variables import ENCODING
from client_server.base_commands import get_message, send_message


class TestSocket:

    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encoded_message = None
        self.receved_message = None

    def send(self, message_to_send):
        json_test_message = json.dumps(self.test_dict)
        self.encoded_message = json_test_message.encode(ENCODING)
        self.receved_message = message_to_send

    def recv(self):
        json_test_message = json.dumps(self.test_dict)
        return json_test_message.encode(ENCODING)


class Tests(unittest.TestCase):
    test_dict_send = {
        'action': 'presence',
        'time': 111111.111111,
        'user': {
            'account_name': 'test_test'
        }
    }
    test_dict_recv_ok = {'response': 200}
    test_dict_recv_err = {
        'response': 400,
        'error': 'Bad Request'
    }

    def test_send_message(self):
        test_socket = TestSocket(self.test_dict_send)
        send_message(test_socket, self.test_dict_send)
        self.assertEqual(test_socket.encoded_message, test_socket.receved_message)
        with self.assertRaises(Exception):
            send_message(test_socket, test_socket)

    def test_get_message(self):
        test_sock_ok = TestSocket(self.test_dict_recv_ok)
        test_sock_err = TestSocket(self.test_dict_recv_err)
        self.assertEqual(get_message(test_sock_ok), self.test_dict_recv_ok)
        self.assertEqual(get_message(test_sock_err), self.test_dict_recv_err)


if __name__ == '__main__':
    unittest.main()
