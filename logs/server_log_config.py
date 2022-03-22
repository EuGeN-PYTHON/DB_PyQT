import logging
import sys
import os
import logging.handlers

sys.path.append(os.path.join(os.getcwd(), '..'))

path_abs = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(path_abs, 'server_app.log')

app_log = logging.getLogger('server_app')
app_log.setLevel(logging.DEBUG)

formatter_str = logging.Formatter('%(asctime)-25s %(levelname)-7s %(module)-20s %(message)s')

file_handler = logging.handlers.TimedRotatingFileHandler(path, encoding='utf8', when='D', interval=1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter_str)

stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(formatter_str)
stream_handler.setLevel(logging.DEBUG)

app_log.addHandler(file_handler)

app_log.debug("Параметры подключения:")
