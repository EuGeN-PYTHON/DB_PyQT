import subprocess
import time

PROCESS = []

while True:
    ACTION = input('Выберите действие: q - выход, '
                   's - запустить сервер и клиенты, x - закрыть все окна: ')

    if ACTION == 'q':
        break
    elif ACTION == 's':
        PROCESS.append(subprocess.Popen('gnome-terminal -- python3 server.py', shell=True))
        for i in range(3):
            time.sleep(0.5)
            PROCESS.append(subprocess.Popen(f'gnome-terminal -- python3 client.py -n test{i}', shell=True))
        # for i in range(2):
        #     time.sleep(0.5)
        #     PROCESS.append(subprocess.Popen('gnome-terminal -- python3 client.py -m listen', shell=True))
    elif ACTION == 'x':
        while PROCESS:
            VICTIM = PROCESS.pop()
            VICTIM.kill()
