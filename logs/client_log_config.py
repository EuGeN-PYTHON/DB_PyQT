import logging
import sys
import os

from logs.server_log_config import stream_handler

sys.path.append(os.path.join(os.getcwd(), '..'))

app_log = logging.getLogger('client_app')
app_log.setLevel(logging.DEBUG)

path_abs = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(path_abs, 'client_app.log')

formatter_str = logging.Formatter('%(asctime)-25s %(levelname)-7s %(module)-20s %(message)s')

file_handler = logging.FileHandler(path, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter_str)
stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(formatter_str)
stream_handler.setLevel(logging.DEBUG)

app_log.addHandler(file_handler)

app_log.debug("Параметры подключения:")