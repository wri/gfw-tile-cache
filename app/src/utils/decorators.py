import functools

from app.src import get_module_logger


class LogDecorator(object):
    def __init__(self):
        self.logger = get_module_logger("decorator-log")

    def __call__(self, fn):
        @functools.wraps(fn)
        def decorated(*args, **kwargs):
            try:
                self.logger.debug("{0} - {1} - {2}".format(fn.__name__, args, kwargs))
                result = fn(*args, **kwargs)
                self.logger.debug(result)
            except Exception as ex:
                self.logger.debug("Exception {0}".format(ex))
                raise ex
            return result

        return decorated
