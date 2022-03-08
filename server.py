import socket
import sys
import json
import logging
import os
import select
import threading
import time
import configparser
import argparse

from decripters import Port
from metaclasses import ServerVerifier
from server_database import ServerDB
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from GUI import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from variables import MAX_CONNECTIONS, DEFAULT_PORT, DEFAULT_IP_ADDRESS
from base_commands import get_message, send_message
from log_deco import Log

# sys.path.append(os.path.join(os.getcwd(), '..'))
from log import server_log_config

app_log = logging.getLogger('server_app')

new_connection = False
conflag_lock = threading.Lock()


@Log()
def arg_parser(default_port, default_address):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


@Log()
class Server(threading.Thread, metaclass=ServerVerifier):
    port = Port()

    def __init__(self, listen_address, listen_port, database):

        self.addr = listen_address
        self.port = listen_port
        self.db = database
        self.clients = []
        self.messages = []
        self.names = dict()
        super().__init__()

    def init_socket(self):
        app_log.info(
            f'Запущен сервер, порт для подключений: {self.port} , адрес с которого принимаются подключения: {self.addr}. Если адрес не указан, принимаются соединения с любых адресов.')
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)

        self.sock = transport
        self.sock.listen()

    def run(self):
        self.init_socket()

        while True:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                app_log.info(f'Установлено соедение с ПК {client_address}')
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(
                        self.clients, self.clients, [], 0)
            except OSError as err:
                app_log.error(f'Ошибка работы с сокетами: {err}')

            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.check_data_client(
                            get_message(client_with_message), client_with_message)
                    except (OSError):
                        app_log.info(
                            f'Клиент {client_with_message.getpeername()} отключился от сервера.')
                        for name in self.names:
                            if self.names[name] == client_with_message:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(client_with_message)

            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except (ConnectionAbortedError, ConnectionError, ConnectionResetError, ConnectionRefusedError):
                    app_log.info(
                        f'Связь с клиентом с именем {message["to"]} была потеряна')
                    self.clients.remove(self.names[message['to']])
                    self.database.user_logout(message['to'])
                    del self.names[message['to']]
            self.messages.clear()

    def process_message(self, message, listen_socks):

        if message['to'] in self.names and self.names[message['to']] in listen_socks:
            send_message(self.names[message['to']], message)
            app_log.info(f'Отправлено сообщение пользователю {message["to"]} '
                         f'от пользователя {message["from"]}.')
        elif message["to"] in self.names and self.names[message["to"]] not in listen_socks:
            raise ConnectionError
        else:
            app_log.error(
                f'Пользователь {message["to"]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')

    def check_data_client(self, msg, client):
        global new_connection
        app_log.debug(f'проверка сообщения от клиента: {msg} с {self.names}')

        if 'action' in msg and msg['action'] == 'presence' and 'time' in msg and \
                'user' in msg:
            if msg['user']['account_name'] not in self.names.keys():
                # app_log.debug(f'Доходит или нет: {msg}')
                self.names[msg['user']['account_name']] = client
                client_ip, client_port = client.getpeername()
                self.db.log_in(msg['user']['account_name'], client_ip, client_port)
                send_message(client, {'response': 200})
                with conflag_lock:
                    new_connection = True
            else:
                send_message(client, {
                    'response': 400,
                    'error': 'Имя занято'})
                self.clients.remove(client)
                client.close()
            return
        elif 'action' in msg and msg['action'] == 'message' and 'to' in msg \
                and 'time' in msg and 'from' in msg and 'mess_text' in msg:
            self.messages.append(msg)
            self.db.send_to_user(msg['from'], msg['to'], msg['mess_text'])
            self.db.process_message(msg['from'], msg['to'])
            return
        elif 'action' in msg and msg['action'] == 'exit' and 'account_name' in msg:
            self.db.log_out(msg['account_name'])
            app_log.info(f'Клиент {msg["account_name"]} корректно отключился от сервера.')
            self.clients.remove(self.names[msg['account_name']])
            self.names[msg['account_name']].close()
            del self.names[msg['account_name']]
            with conflag_lock:
                new_connection = True
            return
        elif 'action' in msg and msg['action'] == 'get_contacts' and 'user' in msg and \
                self.names[msg['user']] == client:
            response = {"response": 202, "data_list": self.db.get_contacts(msg['user'])}
            send_message(client, response)
        elif 'action' in msg and msg['action'] == 'add' and 'account_name' in msg and 'user' in msg \
                and self.names[msg['user']] == client:
            self.db.add_contact(msg['user'], msg['account_name'])
            send_message(client, {'response': 200})
        elif 'action' in msg and msg['action'] == 'remove' and 'account_name' in msg and 'user' in msg \
                and self.names[msg['user']] == client:
            self.db.remove_contact(msg['user'], msg['account_name'])
            send_message(client, {'response': 200})
        elif 'action' in msg and msg['action'] == 'get_users' and 'account_name' in msg \
                and self.names[msg['account_name']] == client:
            app_log.info(f'Вход в ГЕТ ЮЗ')
            response = {"response": 202, "data_list": [user[0] for user in self.db.list_clients()]}
            send_message(client, response)
        # 'action' in msg and msg['action'] == 'presence' and 'time' in msg and \
        # 'user' in msg:

        else:
            send_message(client, {
                'response': 400,
                'error': 'Запрос не корректен'
            })
            return



    # # @classmethod
    # def run(self):
    #     # server.py -p 8079 -a 192.168.1.2
    #     if '-a' in sys.argv:
    #         listen_server = sys.argv[sys.argv.index('-a') + 1]
    #     else:
    #         listen_server = DEFAULT_IP_ADDRESS
    #     if '-p' in sys.argv:
    #         input_port = int(sys.argv[sys.argv.index('-p') + 1])
    #     else:
    #         input_port = DEFAULT_PORT
    #     if input_port < 1024 or input_port > 65535:
    #         app_log.critical(f'Невозможно войти с'
    #                          f' номером порта: {input_port}. '
    #                          f'Допустимы порты с 1024 до 65535. Прервано.')
    #         sys.exit(1)
    #     app_log.info(f'Запущен сервер с порта: {input_port}, сообщения принимаются с адреса: {listen_server}')
    #
    #     try:
    #         if '-a' in sys.argv:
    #             address_ip = listen_server
    #         else:
    #             address_ip = ''
    #     except IndexError:
    #         app_log.critical(
    #             'После параметра \'a\'- необходимо указать адрес, который будет слушать сервер.')
    #         sys.exit(1)
    #
    #     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     s.bind((address_ip, input_port))
    #     s.settimeout(0.5)
    #     s.listen()
    #
    #     clients = []
    #     messages = []
    #
    #     name_soc = dict()
    #     # while True:
    #     #     client, client_address = s.accept()
    #     #     app_log.info(f'Установлено соедение с адресом: {client_address}')
    #     #     try:
    #     #         message_from_client = get_message(client)
    #     #         app_log.debug(f'Получено сообщение {message_from_client}')
    #     #         # print(message_from_client)
    #     #         response = cls.check_data_client(message_from_client)
    #     #         app_log.info(f'создан ответ {response}')
    #     #         send_message(client, response)
    #     #         client.close()
    #     #         app_log.debug(f'Соединение с {client_address} закрыто.')
    #     #     except (ValueError, json.JSONDecodeError):
    #     #         app_log.error(f'Принято некорретное сообщение от клиента:{client_address}')
    #     #         client.close()
    #
    #     while True:
    #         try:
    #             client, client_address = s.accept()
    #         except OSError:
    #             pass
    #         else:
    #             app_log.info(f'Установлено соедение с ПК {client_address}')
    #             clients.append(client)
    #
    #         recv_data_lst = []
    #         send_data_lst = []
    #         err_lst = []
    #         try:
    #             if clients:
    #                 recv_data_lst, send_data_lst, err_lst = select.select(clients, clients, [], 0)
    #         except OSError:
    #             pass
    #         if recv_data_lst:
    #             for client_with_message in recv_data_lst:
    #                 try:
    #                     self.check_data_client(get_message(client_with_message),
    #                                            messages, client_with_message, clients, name_soc)
    #                     app_log.info(f'Клиент {client_with_message.getpeername()} отправляет сообщение.')
    #                 except:
    #                     app_log.info(f'Клиент {client_with_message.getpeername()} '
    #                                  f'отключился от сервера.')
    #                     for name in name_soc:
    #                         if name_soc[name] == client_with_message:
    #                             self.db.log_out(name)
    #                             del name_soc[name]
    #                             break
    #                     clients.remove(client_with_message)
    #         for i in messages:
    #             try:
    #                 self.process_message(i, name_soc, send_data_lst)
    #             except Exception:
    #                 app_log.info(f"Связь с клиентом с именем {i['to']} была потеряна")
    #                 clients.remove(name_soc[i['to']])
    #                 self.db.log_out(i['to'])
    #                 del name_soc[i['to']]
    #         messages.clear()

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
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    listen_address, listen_port = arg_parser(
        config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])

    database = ServerDB(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))

    # db = ServerDB(database)
    srv = Server(listen_address, listen_port, database)
    srv.daemon = True
    srv.start()

    # Создаём графическое окуружение для сервера:
    server_app = QApplication(sys.argv)  # создаем приложение
    main_window = MainWindow()
    # ЗАПУСК РАБОТАЕТ ПАРАЛЕЛЬНО СЕРВЕРА(К ОКНУ)
    # ГЛАВНОМ ПОТОКЕ ЗАПУСКАЕМ НАШ GUI - ГРАФИЧЕСКИЙ ИНТЕРФЕС ПОЛЬЗОВАТЕЛЯ

    # Инициализируем параметры в окна Главное окно
    main_window.statusBar().showMessage('Server Working')  # подвал
    main_window.active_clients_table.setModel(
        gui_create_model(database))  # заполняем таблицу основного окна делаем разметку и заполянем ее
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    # Функция обновляющяя список подключённых, проверяет флаг подключения, и
    # если надо обновляет список
    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(
                gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    # Функция создающяя окно со статистикой клиентов
    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        # stat_window.show()

    # Функция создающяя окно с настройками сервера.
    def server_config():
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    # Функция сохранения настроек
    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    # Таймер, обновляющий список клиентов 1 раз в секунду
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    # Связываем кнопки с процедурами
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    # Запускаем GUI
    server_app.exec_()

    # print('Поддерживаемые комманды:')
    # print('users - список известных пользователей')
    # print('connected - список подключенных пользователей')
    # print('loghist - история входов пользователя')
    # print('messages - история сообщений')
    # print('exit - завершение работы сервера.')
    # print('help - вывод справки по поддерживаемым командам')
    #
    # while True:
    #     command = input('Введите комманду: ')
    #     if command == 'help':
    #         print('Поддерживаемые комманды:')
    #         print('users - список известных пользователей')
    #         print('connected - список подключенных пользователей')
    #         print('loghist - история входов пользователя')
    #         print('messages - история сообщений')
    #         print('exit - завершение работы сервера.')
    #         print('help - вывод справки по поддерживаемым командам')
    #     elif command == 'exit':
    #         break
    #     elif command == 'users':
    #         for user in sorted(srv.db.list_clients()):
    #             print(f'Пользователь {user[0]}, последний вход: {user[1]}')
    #     elif command == 'connected':
    #         for user in sorted(srv.db.list_clients_on_server()):
    #             print(
    #                 f'Пользователь {user[0]}, подключен: {user[1]}:{user[2]}, время установки соединения: {user[3]}')
    #     elif command == 'loghist':
    #         name = input(
    #             'Введите имя пользователя для просмотра истории. Для вывода всей истории, просто нажмите Enter: ')
    #         for user in sorted(srv.db.history_log_in(name)):
    #             print(f'Пользователь: {user[0]} время входа: {user[1]}. Вход с: {user[2]}:{user[3]}')
    #     elif command == 'messages':
    #         name = input(
    #             'Введите имя пользователя от которого отправлены сообщения для просмотра истории. Для вывода всей истории, просто нажмите Enter: ')
    #         for user in sorted(srv.db.history_messages(name)):
    #             print(f'Пользователь: {user[0]} отправил: {user[1]}  сообщение содержанием: {user[3]} в {user[2]}')
    #     else:
    #         print('Команда не распознана.')


if __name__ == '__main__':
    main()
