import logging
import logs.config_client_log
import argparse
import sys
import os
from Cryptodome.PublicKey import RSA
from PyQt5.QtWidgets import QApplication, QMessageBox

from common.variables import *
from common.errors import ServerError
from common.decos import log
from client.database import ClientDatabase
from client.transport import ClientTransport
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog

# Инициализация клиентского логера
logger = logging.getLogger('client')


# Парсер аргументов коммандной строки
@log
def arg_parser():
    '''
    Парсер аргументов командной строки, возвращает кортеж из 4 элементов
    адрес сервера, порт, имя пользователя, пароль.
    Выполняет проверку на корректность номера порта.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('-p', '--password', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name
    client_passwd = namespace.password

    # проверим подходящий номер порта
    if not 1023 < server_port < 65536:
        logger.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {server_port}. Допустимы адреса с 1024 до 65535. Клиент завершается.')
        exit(1)

    return server_address, server_port, client_name, client_passwd


# Основная функция клиента
if __name__ == '__main__':
    # Загружаем параметы коммандной строки
    server_address, server_port, client_name, client_passwd = arg_parser()
    logger.debug('Args loaded')

    # Создаём клиентокое приложение
    client_app = QApplication(sys.argv)

    # Если имя пользователя не было указано в командной строке то запросим его
    start_dialog = UserNameDialog()
    if not client_name or not client_passwd:
        client_app.exec_()
        # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и
        # удаляем объект, инааче выходим
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_passwd = start_dialog.client_passwd.text()
            logger.debug(f'Using USERNAME = {client_name}, PASSWD = {client_passwd}.')
        else:
            exit(0)

    # Записываем логи
    logger.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address} , порт: {server_port}, имя пользователя: {client_name}')

    # Загружаем ключи с файла, если же файла нет, то генерируем новую пару.
    dir_path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())

    #!!!keys.publickey().export_key()
    logger.debug("Keys sucsessfully loaded.")
    # Создаём объект базы данных
    database = ClientDatabase(client_name)
    # Создаём объект - транспорт и запускаем транспортный поток
    try:
        transport = ClientTransport(
            server_port,
            server_address,
            database,
            client_name,
            client_passwd,
            keys)
        logger.debug("Transport ready.")
    except ServerError as error:
        message = QMessageBox()
        message.critical(start_dialog, 'Ошибка сервера', error.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    # Удалим объект диалога за ненадобностью
    del start_dialog

    # Создаём GUI
    main_window = ClientMainWindow(database, transport, keys)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат Программа alpha release - {client_name}')
    client_app.exec_()

    # Раз графическая оболочка закрылась, закрываем транспорт
    transport.transport_shutdown()
    transport.join()


#
#
#
# sock_lock = threading.Lock()
# database_lock = threading.Lock()
#
#
# @Log()
# class ClientSender(threading.Thread, metaclass=ClientVerifier):
#     # host = DEFAULT_IP_ADDRESS
#     port = Port()
#
#     def __init__(self, account_name, sock, database, port=DEFAULT_PORT):
#         # self.host = host
#         self.port = port
#         self.account_name = account_name
#         self.sock = sock
#         self.database = database
#         super().__init__()
#
#     # @staticmethod
#     def leave_message(self):
#         return {
#             'action': 'exit',
#             'time': time.time(),
#             'account_name': self.account_name
#         }
#
#     # @staticmethod
#     # def message_from_server(self, username):
#     #     while True:
#     #         try:
#     #             message = get_message(s)
#     #             if 'action' in message and message['action'] == 'message' and \
#     #                     'from' in message and 'to' in message and 'mess_text' in message \
#     #                     and message['to'] == username:
#     #                 print(f"Получено сообщение от пользователя {message['from']}:\n{message['mess_text']}")
#     #                 client_log.info(f"Получено сообщение от пользователя {message['from']}:\n{message['mess_text']}")
#     #             else:
#     #                 client_log.error(f'Получено некорректное сообщение с сервера: {message}')
#     #         except (OSError, ConnectionError, ConnectionAbortedError,
#     #                 ConnectionResetError, json.JSONDecodeError):
#     #             client_log.critical(f'Потеряно соединение с сервером.')
#     #             break
#
#     # @staticmethod
#     def create_message(self):
#         to_user = input('Введите адресата: ')
#         message = input('Введите сообщение для отправки: ')
#         with database_lock:
#             if not self.database.check_user(to_user):
#                 client_log.error(f'Попытка отправить сообщение незарегистрированому получателю: {to_user}')
#                 return
#
#         message_dict = {
#             'action': 'message',
#             'from': self.account_name,
#             'to': to_user,
#             'time': time.time(),
#             'mess_text': message
#         }
#         client_log.debug(f'Сформирован словарь сообщения: {message_dict}')
#         with database_lock:
#             self.database.save_message(self.account_name, to_user, message)
#
#         with sock_lock:
#             try:
#                 send_message(self.sock, message_dict)
#                 client_log.info(f'Отправлено сообщение для пользователя {to_user}')
#             except OSError as err:
#                 if err.errno:
#                     client_log.critical('Потеряно соединение с сервером.')
#                     exit(1)
#                 else:
#                     client_log.error('Не удалось передать сообщение. Таймаут соединения')
#
#         # try:
#         #     send_message(sock, message_dict)
#         #     client_log.info(f'Отправлено сообщение для пользователя {to_user}')
#         # except:
#         #     client_log.critical('Потеряно соединение с сервером.')
#         #     sys.exit(1)
#
#     @staticmethod
#     def print_help():
#         print('Поддерживаемые команды:')
#         print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
#         print('history - история сообщений')
#         print('contacts - список контактов')
#         print('edit - редактирование списка контактов')
#         print('help - вывести подсказки по командам')
#         print('exit - выход из программы')
#
#     def run(self):
#         self.print_help()
#         while True:
#             command = input('Введите команду: ')
#             if command == 'message':
#                 self.create_message()
#             elif command == 'help':
#                 self.print_help()
#             elif command == 'exit':
#                 with sock_lock:
#                     try:
#                         send_message(self.sock, self.create_exit_message())
#                     except:
#                         pass
#                     print('Завершение соединения.')
#                     client_log.info('Завершение работы по команде пользователя.')
#                 time.sleep(0.5)
#                 break
#             elif command == 'contacts':
#                 with database_lock:
#                     contacts_list = self.database.get_contacts()
#                 for contact in contacts_list:
#                     print(contact)
#             elif command == 'edit':
#                 self.edit_contacts()
#             elif command == 'history':
#                 self.print_history()
#             else:
#                 print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')
#
#     # @classmethod
#     # def send_proc(cls, sock, username):
#     #     print('Поддерживаемые команды:')
#     #     print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
#     #     print('help - вывести подсказки по командам')
#     #     print('exit - выход из программы')
#     #     while True:
#     #         command = input('Введите команду: ')
#     #         if command == 'message':
#     #             cls.create_message(sock, username)
#     #         elif command == 'help':
#     #             print('Поддерживаемые команды:')
#     #             print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
#     #             print('help - вывести подсказки по командам')
#     #             print('exit - выход из программы')
#     #         elif command == 'exit':
#     #             send_message(sock, cls.leave_message(username))
#     #             print('Завершение соединения.')
#     #             client_log.info('Завершение работы по команде пользователя.')
#     #             time.sleep(0.5)
#     #             break
#     #         else:
#     #             print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')
#
#     def print_history(self):
#         ask = input('Показать входящие сообщения - in, исходящие - out, все - просто Enter: ')
#         with database_lock:
#             if ask == 'in':
#                 history_list = self.database.get_history(to_who=self.account_name)
#                 for message in history_list:
#                     print(f'\nСообщение от пользователя: {message[0]} от {message[3]}:\n{message[2]}')
#             elif ask == 'out':
#                 history_list = self.database.get_history(from_who=self.account_name)
#                 for message in history_list:
#                     print(f'\nСообщение пользователю: {message[1]} от {message[3]}:\n{message[2]}')
#             else:
#                 history_list = self.database.get_history()
#                 for message in history_list:
#                     print(
#                         f'\nСообщение от пользователя: {message[0]}, пользователю {message[1]} от {message[3]}\n{message[2]}')
#
#     def edit_contacts(self):
#         ans = input('Для удаления введите del, для добавления add: ')
#         if ans == 'del':
#             edit = input('Введите имя удаляемного контакта: ')
#             with database_lock:
#                 if self.database.check_contact(edit):
#                     self.database.del_contact(edit)
#                 else:
#                     client_log.error('Попытка удаления несуществующего контакта.')
#         elif ans == 'add':
#             edit = input('Введите имя создаваемого контакта: ')
#             if self.database.check_user(edit):
#                 with database_lock:
#                     self.database.add_contact(edit)
#                 with sock_lock:
#                     try:
#                         add_contact(self.sock, self.account_name, edit)
#                     except:
#                         client_log.error('Не удалось отправить информацию на сервер.')
#
#
# @Log()
# class ClientReader(threading.Thread, metaclass=ClientVerifier):
#     def __init__(self, account_name, sock, database):
#         self.account_name = account_name
#         self.sock = sock
#         self.database = database
#         super().__init__()
#
#     def run(self):
#         while True:
#             time.sleep(1)
#             with sock_lock:
#                 try:
#                     message = get_message(self.sock)
#                 except IncorrectDataRecivedError:
#                     client_log.error(f'Не удалось декодировать полученное сообщение.')
#                 except OSError as err:
#                     if err.errno:
#                         client_log.critical(f'Потеряно соединение с сервером.')
#                         break
#                 except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
#                     client_log.critical(f'Потеряно соединение с сервером.')
#                     break
#                 else:
#                     if 'action' in message and message[
#                         'action'] == 'message' and 'from' in message and 'to' in message \
#                             and 'mess_text' in message and message['to'] == self.account_name:
#                         print(f'\nПолучено сообщение от пользователя {message["from"]}:\n{message["mess_text"]}')
#                         with database_lock:
#                             try:
#                                 self.database.save_message(message['from'], self.account_name,
#                                                            message['mess_text'])
#                             except:
#                                 client_log.error('Ошибка взаимодействия с базой данных')
#
#                         client_log.info(
#                             f'Получено сообщение от пользователя {message["from"]}:\n{message["mess_text"]}')
#                     else:
#                         client_log.error(f'Получено некорректное сообщение с сервера: {message}')
#
#
# @Log()
# def create_presence(account_name):
#     out = {
#         'action': 'presence',
#         'time': time.time(),
#         'user': {
#             'account_name': account_name
#         }
#     }
#     client_log.debug(f'Сформировано {"presence"} сообщение для пользователя {account_name}')
#     return out
#
#
# @Log()
# def process_response_ans(message):
#     client_log.debug(f'Разбор приветственного сообщения от сервера: {message}')
#     if 'response' in message:
#         if message['response'] == 200:
#             return '200 : OK'
#         elif message['response'] == 400:
#             raise ServerError(f'400 : {message["error"]}')
#     raise ReqFieldMissingError('response')
#
#
#
# def contacts_list_request(sock, name):
#     client_log.debug(f'Запрос контакт листа для пользователся {name}')
#     req = {
#         'action': 'get_contacts',
#         'time': time.time(),
#         'user': name
#     }
#     client_log.debug(f'Сформирован запрос {req}')
#     send_message(sock, req)
#     ans = get_message(sock)
#     client_log.debug(f'Получен ответ {ans}')
#     if 'response' in ans and ans['response'] == 202:
#         return ans['data_list']
#     else:
#         raise ServerError
#
#
# def add_contact(sock, username, contact):
#     client_log.debug(f'Создание контакта {contact}')
#     req = {
#         'action': 'add',
#         'time': time.time(),
#         'user': username,
#         'account_name': contact
#     }
#     send_message(sock, req)
#     ans = get_message(sock)
#     if 'response' in ans and ans['response'] == 200:
#         pass
#     else:
#         raise ServerError('Ошибка создания контакта')
#     print('Удачное создание контакта.')
#
#
# def user_list_request(sock, username):
#     client_log.debug(f'Запрос списка известных пользователей {username}')
#     print(username)
#     req = {
#         'action': 'get_users',
#         'time': time.time(),
#         'account_name': username
#     }
#     print(req)
#     send_message(sock, req)
#     print('send')
#     ans = get_message(sock)
#     print(ans)
#     if 'response' in ans and ans['response'] == 202:
#         return ans['data_list']
#     else:
#         raise ServerError
#
#
# # Функция удаления пользователя из контакт листа
# def remove_contact(sock, username, contact):
#     client_log.debug(f'Создание контакта {contact}')
#     req = {
#         'action': 'remove',
#         'time': time.time(),
#         'user': username,
#         'account_name': contact
#     }
#     send_message(sock, req)
#     ans = get_message(sock)
#     if ['response'] in ans and ans['response'] == 200:
#         pass
#     else:
#         raise ServerError('Ошибка удаления клиента')
#     print('Удачное удаление')
#
#
# def database_load(sock, database, username):
#     try:
#         users_list = user_list_request(sock, username)
#     except ServerError:
#         client_log.error('Ошибка запроса списка известных пользователей.')
#     else:
#         database.add_users(users_list)
#
#     try:
#         contacts_list = contacts_list_request(sock, username)
#     except ServerError:
#         client_log.error('Ошибка запроса списка контактов.')
#     else:
#         for contact in contacts_list:
#             database.add_contact(contact)

#
# def main():
#     print('Консольный месседжер. Клиентский модуль.')
#
#     server_address, server_port, client_name = arg_parser()
#
#     if not client_name:
#         client_name = input('Введите имя пользователя: ')
#     else:
#         print(f'Клиентский модуль запущен с именем: {client_name}')
#
#     client_log.info(
#         f'Запущен клиент с парамертами: адрес сервера: {server_address} , порт: {server_port}, имя пользователя: {client_name}')
#     try:
#         transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#
#         transport.settimeout(1)
#
#         transport.connect((server_address, server_port))
#         send_message(transport, create_presence(client_name))
#         answer = process_response_ans(get_message(transport))
#         client_log.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
#         print(f'Установлено соединение с сервером.')
#     except json.JSONDecodeError:
#         client_log.error('Не удалось декодировать полученную Json строку.')
#         exit(1)
#     except (ConnectionRefusedError, ConnectionError):
#         client_log.critical(
#             f'Не удалось подключиться к серверу {server_address}:{server_port}, конечный компьютер отверг запрос на подключение.')
#         exit(1)
#     else:
#
#         database = ClientDatabase(client_name)
#         database_load(transport, database, client_name)
#
#         module_sender = ClientSender(client_name, transport, database)
#         module_sender.daemon = True
#         module_sender.start()
#         client_log.debug('Запущены процессы')
#
#         module_receiver = ClientReader(client_name, transport, database)
#         module_receiver.daemon = True
#         module_receiver.start()
#
#         while True:
#             time.sleep(1)
#             if module_receiver.is_alive() and module_sender.is_alive():
#                 continue
#             break
#
#
# if __name__ == '__main__':
#     if __name__ == '__main__':
#         # Загружаем параметы коммандной строки
#         server_address, server_port, client_name = arg_parser()
#
#         # Создаём клиентокое приложение
#         client_app = QApplication(sys.argv)
#
#         # Если имя пользователя не было указано в командной строке то запросим его
#         if not client_name:
#             start_dialog = UserNameDialog()
#             client_app.exec_()
#             # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и удаляем объект, инааче выходим
#             if start_dialog.ok_pressed:
#                 client_name = start_dialog.client_name.text()
#                 del start_dialog
#             else:
#                 exit(0)
#
#         # Записываем логи
#         client_log.info(
#             f'Запущен клиент с парамертами: адрес сервера: {server_address} , порт: {server_port}, имя пользователя: {client_name}')
#
#         # Создаём объект базы данных
#         database = ClientDatabase(client_name)
#
#         # Создаём объект - транспорт и запускаем транспортный поток
#         try:
#             transport = ClientTransport(server_port, server_address, database, client_name)
#         except ServerError as error:
#             print(error.text)
#             exit(1)
#         transport.setDaemon(True)
#         transport.start()
#
#         # Создаём GUI
#         main_window = ClientMainWindow(database, transport)
#         main_window.make_connection(transport)
#         main_window.setWindowTitle(f'Чат Программа alpha release - {client_name}')
#         client_app.exec_()
#
#         # Раз графическая оболочка закрылась, закрываем транспорт
#         transport.transport_shutdown()
#         transport.join()

    #
    # @staticmethod
    # def get_presence(account_name='Guest'):
    #     data = {
    #         'action': 'presence',
    #         'time': time.time(),
    #         'user': {
    #             'account_name': account_name
    #         }
    #     }
    #     client_log.debug(f'Создано сообщение presence для пользователя: {account_name}')
    #     return data
    #
    # @staticmethod
    # def response_analyze(msg):
    #     client_log.debug(f'Соответствие сообщения от сервера: {msg}')
    #     if 'response' in msg:
    #         if msg['response'] == 200:
    #             return '200 : OK'
    #         return f'400 : {msg["error"]}'
    #     raise ValueError
    #
    #
    #
    #
    # @classmethod
    # def base(cls):
    #     # client.py -a 192.168.1.2 -p 8079 -n username
    #
    #     if '-a' in sys.argv:
    #         server_address = sys.argv[sys.argv.index('-a') + 1]
    #     else:
    #         server_address = DEFAULT_IP_ADDRESS
    #     if '-p' in sys.argv:
    #         server_port = int(sys.argv[sys.argv.index('-p') + 1])
    #     else:
    #         server_port = DEFAULT_PORT
    #     if '-n' in sys.argv:
    #         client_name = sys.argv[sys.argv.index('-n') + 1]
    #     else:
    #         client_name = input('Введите имя пользователя: ')
    #
    #     if server_port < 1024 or server_port > 65535:
    #         client_log.critical(f'Невозможно войти с'
    #                             f' номером порта: {server_port}. '
    #                             f'Допустимы порты с 1024 до 65535. Прервано.')
    #         sys.exit(1)
    #
    #     client_log.info(f'Запущен клиент с парам.: {server_address}, порт: {server_port}')
    #
    #     try:
    #
    #         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         s.connect((server_address, server_port))
    #         message_to_server = cls.get_presence(client_name)
    #         send_message(s, message_to_server)
    #         answer = cls.response_analyze(get_message(s))
    #         client_log.info(f'Принят ответ от сервера {answer}')
    #         # print(answer)
    #     except json.JSONDecodeError:
    #         client_log.error('Не удалось декодировать полученную Json строку.')
    #         sys.exit(1)
    #     except ConnectionRefusedError:
    #         client_log.critical(
    #             f'Не удалось подключиться к серверу {server_address}:{server_port}, '
    #             f'конечный компьютер отверг запрос на подключение.')
    #         sys.exit(1)
    #     else:
    #         listen_proc = threading.Thread(target=cls.message_from_server, args=(s, client_name))
    #         listen_proc.daemon = True
    #         listen_proc.start()
    #
    #         send_proc = threading.Thread(target=cls.send_proc, args=(s, client_name))
    #         send_proc.daemon = True
    #         send_proc.start()
    #         client_log.debug('Процессы запущены')
    #
    #         while True:
    #             time.sleep(1)
    #             if listen_proc.is_alive() and send_proc.is_alive():
    #                 continue
    #             break

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
