import socket
import sys
import json
import logging
import os
import select
import threading
import time

from decripters import Port
from metaclasses import ServerVerifier
from server_database import ServerDB

from variables import MAX_CONNECTIONS, DEFAULT_PORT, DEFAULT_IP_ADDRESS
from base_commands import get_message, send_message
from log_deco import Log

# sys.path.append(os.path.join(os.getcwd(), '..'))
from log import server_log_config

app_log = logging.getLogger('server_app')

clients = []
messages = []


@Log()
class Server(threading.Thread, metaclass=ServerVerifier):
    conn = MAX_CONNECTIONS
    port = Port()

    def __init__(self, db, conn=MAX_CONNECTIONS, port=DEFAULT_PORT):
        self.conn = conn
        self.port = port
        self.db = db
        super().__init__()

    # @staticmethod
    def check_data_client(self, msg, msg_lst, client, clients, name_soc):
        app_log.debug(f'проверка сообщения от клиента: {msg}')
        if 'action' in msg and msg['action'] == 'presence' and 'time' in msg and \
                'user' in msg:
            if msg['user']['account_name'] not in name_soc.keys():
                app_log.debug(f'Доходит или нет: {msg}')
                name_soc[msg['user']['account_name']] = client
                client_ip, client_port = client.getpeername()
                self.db.log_in(msg['user']['account_name'], client_ip, client_port)
                send_message(client, {'response': 200})
            else:
                send_message(client, {
                    'response': 400,
                    'error': 'Имя занято'})
                clients.remove(client)
                client.close()
            return
        elif 'action' in msg and msg['action'] == 'message' and 'to' in msg \
                and 'time' in msg and 'from' in msg and 'mess_text' in msg:
            msg_lst.append(msg)
            return
        elif 'action' in msg and msg['action'] == 'exit' and 'account_name' in msg:
            self.db.log_out(msg['account_name'])
            clients.remove(name_soc[msg['account_name']])
            name_soc[msg['account_name']].close()
            del name_soc[msg['account_name']]
            return
        else:
            send_message(client, {
                'response': 400,
                'error': 'Запрос не корректен'
            })
            return

    @staticmethod
    def process_message(message, name_soc, listen_socks):

        if message['to'] in name_soc and name_soc[message['to']] in listen_socks:
            send_message(name_soc[message['to']], message)
            app_log.info(f'Отправлено сообщение пользователю {message["to"]} '
                         f'от пользователя {message["from"]}.')
        elif message["to"] in name_soc and name_soc[message["to"]] not in listen_socks:
            raise ConnectionError
        else:
            app_log.error(
                f'Пользователь {message["to"]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')

    # @classmethod
    def run(self):
        # server.py -p 8079 -a 192.168.1.2
        if '-a' in sys.argv:
            listen_server = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_server = DEFAULT_IP_ADDRESS
        if '-p' in sys.argv:
            input_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            input_port = DEFAULT_PORT
        if input_port < 1024 or input_port > 65535:
            app_log.critical(f'Невозможно войти с'
                             f' номером порта: {input_port}. '
                             f'Допустимы порты с 1024 до 65535. Прервано.')
            sys.exit(1)
        app_log.info(f'Запущен сервер с порта: {input_port}, сообщения принимаются с адреса: {listen_server}')

        try:
            if '-a' in sys.argv:
                address_ip = listen_server
            else:
                address_ip = ''
        except IndexError:
            app_log.critical(
                'После параметра \'a\'- необходимо указать адрес, который будет слушать сервер.')
            sys.exit(1)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((address_ip, input_port))
        s.settimeout(0.5)
        s.listen(MAX_CONNECTIONS)

        clients = []
        messages = []

        name_soc = dict()
        # while True:
        #     client, client_address = s.accept()
        #     app_log.info(f'Установлено соедение с адресом: {client_address}')
        #     try:
        #         message_from_client = get_message(client)
        #         app_log.debug(f'Получено сообщение {message_from_client}')
        #         # print(message_from_client)
        #         response = cls.check_data_client(message_from_client)
        #         app_log.info(f'создан ответ {response}')
        #         send_message(client, response)
        #         client.close()
        #         app_log.debug(f'Соединение с {client_address} закрыто.')
        #     except (ValueError, json.JSONDecodeError):
        #         app_log.error(f'Принято некорретное сообщение от клиента:{client_address}')
        #         client.close()

        while True:
            try:
                client, client_address = s.accept()
            except OSError:
                pass
            else:
                app_log.info(f'Установлено соедение с ПК {client_address}')
                clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            try:
                if clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(clients, clients, [], 0)
            except OSError:
                pass
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.check_data_client(get_message(client_with_message),
                                              messages, client_with_message, clients, name_soc)
                        app_log.info(f'Клиент {client_with_message.getpeername()} отправляет сообщение.')
                    except:
                        app_log.info(f'Клиент {client_with_message.getpeername()} '
                                     f'отключился от сервера.')
                        clients.remove(client_with_message)
            for i in messages:
                try:
                    self.process_message(i, name_soc, send_data_lst)
                except Exception:
                    app_log.info(f"Связь с клиентом с именем {i['to']} была потеряна")
                    clients.remove(name_soc[i['to']])
                    del name_soc[i['to']]
            messages.clear()

            # if messages and send_data_lst:
            #     message = {
            #         'action': 'message',
            #         'sender': messages[0][0],
            #         'time': time.time(),
            #         'mess_text': messages[0][1]
            #     }
            #     del messages[0]
            #     for waiting_client in send_data_lst:
            #         try:
            #             send_message(waiting_client, message)
            #         except:
            #             app_log.info(f'Клиент {waiting_client.getpeername()} отключился от сервера.')
            #             clients.remove(waiting_client)


def main():
    db = ServerDB()
    srv = Server(db)
    srv.daemon = True
    srv.start()

    print('Поддерживаемые комманды:')
    print('users - список известных пользователей')
    print('connected - список подключенных пользователей')
    print('loghist - история входов пользователя')
    print('exit - завершение работы сервера.')
    print('help - вывод справки по поддерживаемым командам')

    while True:
        command = input('Введите комманду: ')
        if command == 'help':
            print('Поддерживаемые комманды:')
            print('users - список известных пользователей')
            print('connected - список подключенных пользователей')
            print('loghist - история входов пользователя')
            print('exit - завершение работы сервера.')
            print('help - вывод справки по поддерживаемым командам')
        elif command == 'exit':
            break
        elif command == 'users':
            for user in sorted(srv.db.list_clients()):
                print(f'Пользователь {user[0]}, последний вход: {user[1]}')
        elif command == 'connected':
            for user in sorted(srv.db.list_clients_on_server()):
                print(
                    f'Пользователь {user[0]}, подключен: {user[1]}:{user[2]}, время установки соединения: {user[3]}')
        elif command == 'loghist':
            name = input(
                'Введите имя пользователя для просмотра истории. Для вывода всей истории, просто нажмите Enter: ')
            for user in sorted(srv.db.history_log_in(name)):
                print(f'Пользователь: {user[0]} время входа: {user[1]}. Вход с: {user[2]}:{user[3]}')
        else:
            print('Команда не распознана.')


if __name__ == '__main__':
    main()
