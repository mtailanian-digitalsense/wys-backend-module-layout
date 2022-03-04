import logging
# import coloredlogs
from typing import Union


def get_logger(filename: Union[str, None] = None, log_to_console: bool = True, log_level: Union[str, None] = None):
	"""
	@param filename: path to save the log
	@param log_to_console: Whether to also log to console or not
	@param log_level: logging level. Must be one of ["debug", "info", "warning", "error", "critical"]
	@return: logger object. May be used as:
		logger.debug('This is a debug message')
		logger.info('This is an info message')
		logger.warning('This is a warning message')
		logger.error('This is an error message')
		logger.critical('This is a critical message')
	"""

	if log_level is None:
		log_level = "debug"
	else:
		assert log_level in ["debug", "info", "warning", "error", "critical"], \
			"`log_level` must be one of ['debug', 'info', 'warning', 'error', 'critical']"

	logging_level = {
		"debug": logging.DEBUG,
		"info": logging.INFO,
		"warning": logging.WARNING,
		"error": logging.ERROR,
		"critical": logging.CRITICAL
	}[log_level]

	if filename is None:
		filename = "log.log"

	logging_format = '%(levelname)8s  %(asctime)s [%(filename)s:%(funcName)s] >> %(message)s'
	logging_date_format = '%d-%b-%y %H:%M:%S'

	logging.basicConfig(
		filemode="w",
		filename=filename,
		level=logging_level,
		format=logging_format,
		datefmt=logging_date_format
	)

	logger = logging.getLogger(__name__)

	# Also log to std out with colors
	if log_to_console:
		level_styles = {'critical': {'bold': True, 'color': 'red'},
		                'error': {'color': 'red'},
		                'warning': {'color': 'yellow'},
		                'info': {'color': 'green'},
		                'debug': {'color': 'black'}
		                }
		field_style = {
			'asctime': {'color': 'magenta'},
			'levelname': {'bold': True, 'color': 'black'},
			'filename': {'color': 'cyan'},
			'funcName': {'color': 'blue'}
		}
		# coloredlogs.install(
		# 	logger=logger,
		# 	level=logging_level,
		# 	fmt=logging_format,
		# 	datefmt=logging_date_format,
		# 	field_styles=field_style,
		# 	level_styles=level_styles
		# )

	return logger
