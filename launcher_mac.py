#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Модуль автозапуска сервера и нескольких клиентов"""

import time
import os
from subprocess import Popen



CLIENTS = []
SERVER = ''
PATH_TO_FILE = os.path.dirname(__file__)
# TRUE_PATH_TO_FILE = PATH_TO_FILE[PATH_TO_FILE.index('evgeny_varlamov/')+len('evgeny_varlamov/'):]
PATH_TO_SCRIPT_SERVER = os.path.join(PATH_TO_FILE, "pack_server/server/server.py")
PATH_TO_SCRIPT_CLIENTS = os.path.join(PATH_TO_FILE, "pack_client/client/client.py")
print(PATH_TO_SCRIPT_CLIENTS)

process = []


def main():
    '''
    hi
    '''
    process = []

    while True:
        action = input(
            'Выберите действие: q - выход , s - запустить сервер,'
            ' k - запустить клиенты x - закрыть все окна:')
        if action == 's':
            # Запускаем сервер!
            process.append(Popen(f'osascript -e \'tell application '
                                 f'"Terminal" to do script "python3.8'
                                 f' {PATH_TO_SCRIPT_SERVER}"\'', shell=True))
        elif action == 'q':
            break
        elif action == 'k':
            print('Убедитесь, что на сервере зарегистрировано'
                  ' необходимо количество клиентов с паролем 123.')
            print('Первый запуск может быть достаточно'
                  ' долгим из-за генерации ключей!')
            clients_count = int(
                input('Введите количество тестовых клиентов для запуска: '))
            # Запускаем клиентов:
            for i in range(clients_count):
                time.sleep(0.5)
                process.append(Popen(f'osascript -e \'tell application "Terminal" to do script "python3.8'
                                     f' {PATH_TO_SCRIPT_CLIENTS} -n test{i+1} -p 1"\'', shell=True))
        elif action == 'x':
            while process:
                process.pop().kill()


if __name__ == '__main__':
    main()
    # print(PATH_TO_FILE)
# while True:
#     action = input('Выберите действие: q - выход , s - запустить сервер и клиенты, x - закрыть все окна:')
#     if action == 'q':
#         break
#     elif action == 's':
#         clients_count = int(input('Введите количество тестовых клиентов для запуска: '))
#         # Запускаем сервер!
#         process.append(Popen(f'osascript -e \'tell application "Terminal" to do script "python3.8 {PATH_TO_SCRIPT_SERVER}"\'', shell=True))
#         # Запускаем клиентов:
#         for i in range(clients_count):
#             time.sleep(0.5)
#             process.append(Popen(f'osascript -e \'tell application "Terminal" to do script "python3.8 {PATH_TO_SCRIPT_CLIENTS} -n test{i+3} -p 1"\'', shell=True))
#     elif action == 'x':
#         while process:
#             process.pop().kill()