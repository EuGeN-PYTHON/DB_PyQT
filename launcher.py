#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Модуль автозапуска сервера и нескольких клиентов"""

import time
import os
from subprocess import Popen

CLIENTS = []
SERVER = ''
PATH_TO_FILE = os.path.dirname(__file__)
PATH_TO_SCRIPT_SERVER = os.path.join(PATH_TO_FILE, "server.py")
PATH_TO_SCRIPT_CLIENTS = os.path.join(PATH_TO_FILE, "client.py")
print(PATH_TO_SCRIPT_CLIENTS)


def main():
    process = []
    while True:
        action = input('Выберите действие: q - выход , s - запустить сервер,'
                       ' k - запустить клиентов, x - закрыть все окна:')
        if action == 's':
            # Запускаем сервер!
            process.append(Popen(f'osascript -e \'tell application "Terminal"'
                                 f' to do script "python3.8'
                                 f' {PATH_TO_SCRIPT_SERVER}"\'', shell=True))
        elif action == 'q':
            break
        elif action == 'k':
            clients_count = int(input('Введите количество тестовых клиентов для запуска: '))
            # Запускаем клиентов:
            for i in range(clients_count):
                time.sleep(0.5)
                process.append(Popen(f'osascript -e \''
                                     f'tell application "Terminal"'
                                     f' to do script "python3.8'
                                     f' {PATH_TO_SCRIPT_CLIENTS}'
                                     f' -n test{i + 1} -p 1"\'', shell=True))
        elif action == 'x':
            while process:
                process.pop().kill()


if __name__ == '__main__':
    main()
