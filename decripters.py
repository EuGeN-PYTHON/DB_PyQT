import logging
app_log = logging.getLogger('server_app')

class Port:
    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            app_log.critical(
                f'Попытка запуска сервера с указанием неподходящего порта {value}. Допустимы адреса с 1024 до 65535.')
            exit(1)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name