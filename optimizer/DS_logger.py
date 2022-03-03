import logging
import coloredlogs


logging_format = '%(levelname)8s | %(asctime)s | %(filename)s:%(funcName)s >> %(message)s'
logging_level = logging.DEBUG
logging_date_format = '%d-%b-%y %H:%M:%S'

logging.basicConfig(
	filemode="w",
    filename='smart_layout.log',
    level=logging_level,
    format=logging_format,
    datefmt=logging_date_format
)

logger = logging.getLogger(__name__)

# Also log to std out with colors
field_style = {
	'asctime': {'color': 'magenta'},
	'levelname': {'bold': True, 'color': 'black'},
	'filename': {'color': 'cyan'},
	'funcName': {'color': 'blue'}
}
coloredlogs.install(
	logger=logger,
	level=logging_level,
	fmt=logging_format,
	datefmt=logging_date_format,
	field_styles=field_style,
)
