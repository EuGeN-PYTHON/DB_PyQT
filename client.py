import logging
import sys
import json
import socket
import threading
import time
import os
from metaclasses import ClientVerifier

from variables import DEFAULT_IP_ADDRESS, DEFAULT_PORT
from log_deco import Log
from base_commands import get_message, send_message

# sys.path.append(os.path.join(os.getcwd(), '..'))
from log import client_log_config

client_log = logging.getLogger('client_app')


@Log()
class Client(metaclass=ClientVerifier):
    # host = DEFAULT_IP_ADDRESS
    port = DEFAULT_PORT

    def __init__(self, port=port):
        # self.host = host
        self.port = port

    @staticmethod
    def leave_message(account_name):
        return {
            'action': 'exit',
            'time': time.time(),
            'account_name': account_name
        }

    @staticmethod
    def message_from_server(s, username):
        while True:
            try:
                message = get_message(s)
                if 'action' in message and message['action'] == 'message' and \
                        'from' in message and 'to' in message and 'mess_text' in message \
                        and message['to'] == username:
                    print(f"Получено сообщение от пользователя {message['from']}:\n{message['mess_text']}")
                    client_log.info(f"Получено сообщение от пользователя {message['from']}:\n{message['mess_text']}")
                else:
                    client_log.error(f'Получено некорректное сообщение с сервера: {message}')
            except (OSError, ConnectionError, ConnectionAbortedError,
                    ConnectionResetError, json.JSONDecodeError):
                client_log.critical(f'Потеряно соединение с сервером.')
                break

    @staticmethod
    def create_message(sock, account_name='Guest'):
        to_user = input('Введите адресата: ')
        message = input('Введите сообщение для отправки: ')
        message_dict = {
            'action': 'message',
            'from': account_name,
            'to': to_user,
            'time': time.time(),
            'mess_text': message
        }
        client_log.debug(f'Сформирован словарь сообщения: {message_dict}')
        try:
            send_message(sock, message_dict)
            client_log.info(f'Отправлено сообщение для пользователя {to_user}')
        except:
            client_log.critical('Потеряно соединение с сервером.')
            sys.exit(1)

    @classmethod
    def send_proc(cls, sock, username):
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                cls.create_message(sock, username)
            elif command == 'help':
                print('Поддерживаемые команды:')
                print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
                print('help - вывести подсказки по командам')
                print('exit - выход из программы')
            elif command == 'exit':
                send_message(sock, cls.leave_message(username))
                print('Завершение соединения.')
                client_log.info('Завершение работы по команде пользователя.')
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')

    @staticmethod
    def get_presence(account_name='Guest'):
        data = {
            'action': 'presence',
            'time': time.time(),
            'user': {
                'account_name': account_name
            }
        }
        client_log.debug(f'Создано сообщение presence для пользователя: {account_name}')
        return data

    @staticmethod
    def response_analyze(msg):
        client_log.debug(f'Соответствие сообщения от сервера: {msg}')
        if 'response' in msg:
            if msg['response'] == 200:
                return '200 : OK'
            return f'400 : {msg["error"]}'
        raise ValueError

    @classmethod
    def base(cls):
        # client.py -a 192.168.1.2 -p 8079 -n username

        if '-a' in sys.argv:
            server_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            server_address = DEFAULT_IP_ADDRESS
        if '-p' in sys.argv:
            server_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            server_port = DEFAULT_PORT
        if '-n' in sys.argv:
            client_name = sys.argv[sys.argv.index('-n') + 1]
        else:
            client_name = input('Введите имя пользователя: ')

        if server_port < 1024 or server_port > 65535:
            client_log.critical(f'Невозможно войти с'
                                f' номером порта: {server_port}. '
                                f'Допустимы порты с 1024 до 65535. Прервано.')
            sys.exit(1)

        client_log.info(f'Запущен клиент с парам.: {server_address}, порт: {server_port}')

        try:

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((server_address, server_port))
            message_to_server = cls.get_presence(client_name)
            send_message(s, message_to_server)
            answer = cls.response_analyze(get_message(s))
            client_log.info(f'Принят ответ от сервера {answer}')
            # print(answer)
        except json.JSONDecodeError:
            client_log.error('Не удалось декодировать полученную Json строку.')
            sys.exit(1)
        except ConnectionRefusedError:
            client_log.critical(
                f'Не удалось подключиться к серверу {server_address}:{server_port}, '
                f'конечный компьютер отверг запрос на подключение.')
            sys.exit(1)
        else:
            listen_proc = threading.Thread(target=cls.message_from_server, args=(s, client_name))
            listen_proc.daemon = True
            listen_proc.start()

            send_proc = threading.Thread(target=cls.send_proc, args=(s, client_name))
            send_proc.daemon = True
            send_proc.start()
            client_log.debug('Процессы запущены')

            while True:
                time.sleep(1)
                if listen_proc.is_alive() and send_proc.is_alive():
                    continue
                break

            # if client_mode == 'send':
            #     print('Режим работы - отправка сообщений.')
            # else:
            #     print('Режим работы - приём сообщений.')
            # while True:
            #     if client_mode == 'send':
            #         try:
            #             send_message(s, cls.create_message(s))
            #         except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
            #             client_log.error(f'Соединение с сервером {server_address} было потеряно.')
            #             sys.exit(1)
            #
            #     if client_mode == 'listen':
            #         try:
            #             cls.message_from_server(get_message(s))
            #         except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
            #             client_log.error(f'Соединение с сервером {server_address} было потеряно.')
            #             sys.exit(1)


if __name__ == '__main__':
    clnt = Client()
    clnt.base()
