"""
1. Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
Аргументом функции является список, в котором каждый сетевой узел должен быть представлен
именем хоста или ip-адресом. В функции необходимо перебирать ip-адреса и проверять их доступность
с выводом соответствующего сообщения («Узел доступен», «Узел недоступен»).
При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().
"""

from ipaddress import ip_address
from subprocess import Popen, PIPE


def host_ping(lst_ip, time_out=500, count=1):
    res = []
    for ip in lst_ip:
        try:
            ip_add = ip_address(ip)
        except ValueError:
            pass
        command = Popen(f"ping {ip_add} -t {time_out} -c {count}", shell=True, stdout=PIPE)
        print(ip_add)
        command.wait()
        if command.returncode == 0:
            res.append({'Reachable': ip_add})
        else:
            res.append({'Unreachable': ip_add})
    return res


if __name__ == '__main__':
    lst_ip = ['127.0.0.1', '10.0.0.1', '192.168.0.100', '192.168.0.101']
    print(host_ping(lst_ip))
