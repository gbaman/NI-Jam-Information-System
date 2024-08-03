import logging
from logging.handlers import RotatingFileHandler
import pathlib

log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

log_folder = pathlib.Path('logs')
log_folder.mkdir(exist_ok=True)

# Configure the access logger
access_handler = RotatingFileHandler('logs/access.log', maxBytes=10000, backupCount=1)
access_handler.setLevel(logging.INFO)
access_handler.setFormatter(logging.Formatter(log_format))
access_logger = logging.getLogger('access')
access_logger.setLevel(logging.INFO)
access_logger.addHandler(access_handler)

# Configure the info handler (for everything else, including accesses)
info_handler = RotatingFileHandler('logs/info.log', maxBytes=10000, backupCount=1)
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(logging.Formatter(log_format))
info_logger = logging.getLogger('info')
info_logger.setLevel(logging.INFO)
info_logger.addHandler(info_handler)
