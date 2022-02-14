"""
2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
Меняться должен только последний октет каждого адреса.
По результатам проверки должно выводиться соответствующее сообщение.
"""

from ipaddress import ip_address
from task1 import host_ping

def host_range_ping():
    ip_lst = []
    while True:
        start_ip_add = input('Введите начальный ip: ')
        try:
            last_num_from_start = int(start_ip_add.split('.')[3])
            print(last_num_from_start)
            if last_num_from_start <= 255:
                break
            else:
                print('Начальный IP больше *.*.*.255')
        except Exception as e:
            print(e)
    while True:
        final_ip_add = input('Введите конечный ip: ')
        try:
            last_num_from_final = int(final_ip_add.split('.')[3])
            print(last_num_from_final)
            if last_num_from_final >= last_num_from_start and last_num_from_final <= 255:
                count_ip = last_num_from_final - last_num_from_start + 1
                break
            else:
                print('Конечный IP меньше начального или больше *.*.*.255')
        except Exception as e:
            print(e)
    start_ip_add = ip_address(start_ip_add)
    for i in range(count_ip):
        ip_addr = ip_address(start_ip_add + i)
        ip_lst.append((ip_addr))
    # print(host_ping(ip_lst))
    return host_ping(ip_lst)
    # print(ip_lst)



if __name__ == '__main__':
    host_range_ping()
