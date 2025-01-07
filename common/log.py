import logging

from echelon.common.config import SETTINGS
from echelon.common.otel import OtelLogging


class Log(object):
    """"""
    _executed = False

    @staticmethod
    def init():
        """"""
        if Log._executed:
            return

        if SETTINGS.OTEL_ENABLED:
            OtelLogging.init()
            fmt = f"%(asctime)s [%(levelname)s] [tid=%(otelTraceID)s sid=%(otelSpanID)s] %(filename)s:%(funcName)s:%(lineno)s - %(message)s"
        else:
            fmt = f"%(asctime)s [%(levelname)s] %(filename)s:%(funcName)s:%(lineno)s - %(message)s"

        formatter = logging.Formatter(
            fmt=fmt,
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        logging.basicConfig(level=logging.INFO)
        logging.getLogger().handlers[0].setFormatter(formatter)
