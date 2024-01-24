import logging
import colorlog

job_name = 'auto-edge'
LOG_LEVEL = 'DEBUG'


class Logger:
    def __init__(self, name: str = job_name):
        self.logger = logging.getLogger(name)

        self.format = colorlog.ColoredFormatter(
            '%(log_color)s[%(asctime)-15s] %(filename)s(%(lineno)d)'
            ' [%(levelname)s]%(reset)s - %(message)s', )

        self.handler = logging.StreamHandler()
        self.handler.setFormatter(self.format)

        self.logger.addHandler(self.handler)
        self.logLevel = 'INFO'
        self.logger.setLevel(level=LOG_LEVEL)
        self.logger.propagate = False


LOGGER = Logger().logger
