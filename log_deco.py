import inspect
import logging
import sys
import traceback

if sys.argv[0].find('client.py') == -1:
    log = logging.getLogger('server_app')
else:
    log = logging.getLogger('client_app')

class Log:

    def __call__(self, func):
        def to_log(*args, **kwargs):
            result = func(*args, **kwargs)
            log.debug(f'Вызвана функция {func.__name__} c параметрами {args}, {kwargs}. '
                     f'Вызван модуль: {func.__module__}.  из'
                     f' функции {traceback.format_stack()[0].strip().split()[-1]}.'
                     f'Вызов из функции {inspect.stack()[1][3]}', stacklevel=2)
            return result
        return to_log

if sys.argv[0].find('client') == -1:
    # если не клиент то сервер!
    LOGGER = logging.getLogger('server')
else:
    # ну, раз не сервер, то клиент
    LOGGER = logging.getLogger('client')

