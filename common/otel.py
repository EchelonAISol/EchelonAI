import importlib.util
import logging
from typing import Optional, Any

import fastapi
from opentelemetry import baggage
from opentelemetry import trace
from opentelemetry.baggage import get_baggage
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.context import get_current, attach
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import get_current_span
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from echelon.common.config import SETTINGS

logger = logging.getLogger(__name__)


def check_pkg(pkg: str) -> bool:
    """"""
    spec = None
    try:
        spec = importlib.util.find_spec(pkg)
    except (ImportError, AttributeError, TypeError, ValueError) as ex:
        pass
    if spec is None:
        logger.warning(f"please install {pkg}")
    return spec is not None


class Otel(object):
    """"""
    _executed = False
    _trace_provider = None
    _settings = None

    @staticmethod
    def init():
        if Otel._executed:
            return

        Otel._executed = True

        if not SETTINGS.OTEL_ENABLED:
            logger.info("otel disabled")
            return
        logger.info("otel enabled")

        Otel._init_propagator()

        resource = Otel._init_resource()

        Otel._init_trace(resource)

        OtelAioHttpClient.init()
        OtelHttpx.init()
        OtelRequests.init()

    @staticmethod
    def get_trace_provider() -> Optional[Any]:
        """"""
        Otel.init()
        return Otel._trace_provider

    @staticmethod
    def get_cur_tid() -> str:
        ret = ""
        try:
            current_span = get_current_span()
            tid = current_span.get_span_context().trace_id if current_span.get_span_context().is_valid else ''
            if tid:
                ret = format(tid, '032x')
        except Exception:
            pass
        return ret

    @staticmethod
    def get_cur_sid() -> str:
        ret = ""
        try:
            current_span = get_current_span()
            sid = current_span.get_span_context().span_id if current_span.get_span_context().is_valid else ''
            if sid:
                ret = format(sid, '016x')
        except Exception:
            pass
        return ret

    @staticmethod
    def get_baggage(key: str) -> Optional[object]:
        if not key:
            return None
        current_context = get_current()
        return get_baggage(key, context=current_context)

    @staticmethod
    def add_baggage(name: str, value: object):
        current_context = get_current()
        attach(baggage.set_baggage(name, value, current_context))

    @staticmethod
    def _init_trace(resource):
        trace_provider = TracerProvider(resource=resource)
        if SETTINGS.OTEL_TRACE_UPLOAD_ENABLED:
            logger.info("otel trace upload enabled")
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=SETTINGS._OTEL_TRACE_UPLOAD_URL))
            trace_provider.add_span_processor(processor)
        else:
            logger.info("otel trace upload disabled")

        Otel._trace_provider = trace_provider
        trace.set_tracer_provider(trace_provider)

    @staticmethod
    def _init_propagator():
        propagator = CompositePropagator([TraceContextTextMapPropagator(), W3CBaggagePropagator()])
        set_global_textmap(propagator)

    @staticmethod
    def _init_resource():
        resource = Resource(attributes={
            SERVICE_NAME: SETTINGS.APP_NAME,
        })
        return resource

    @staticmethod
    def _init_sub_module(module_name, class_name):
        try:
            package_name = __name__.rpartition('.')[0]
            module = importlib.import_module(f".{module_name}", package=package_name)
            getattr(module, class_name).init()
        except (ImportError, AttributeError):
            logger.warning(f"{module_name}.{class_name} not found")


class OtelFastAPI(object):
    _executed = False

    @staticmethod
    def init(app: fastapi.FastAPI):
        """"""
        if OtelFastAPI._executed:
            return

        if not SETTINGS.OTEL_ENABLED:
            return

        OtelFastAPI._executed = True

        if not check_pkg("opentelemetry.instrumentation.fastapi"):
            return

        if app and Otel.get_trace_provider():
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            FastAPIInstrumentor.instrument_app(app, tracer_provider=Otel.get_trace_provider())


class OtelHttpx(object):
    """"""
    _executed = False

    @staticmethod
    def init():
        if OtelHttpx._executed:
            return

        if not SETTINGS.OTEL_ENABLED:
            return

        OtelHttpx._executed = True

        if not check_pkg("opentelemetry.instrumentation.httpx"):
            return

        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        HTTPXClientInstrumentor().instrument()


class OtelLogging(object):
    """"""
    _executed = False

    @staticmethod
    def init():
        """"""
        if OtelLogging._executed:
            return

        if not SETTINGS.OTEL_ENABLED:
            return

        OtelLogging._executed = True

        if not check_pkg("opentelemetry.instrumentation.logging"):
            return

        from opentelemetry.instrumentation.logging import LoggingInstrumentor
        LoggingInstrumentor().instrument()


class OtelRequests(object):
    """"""
    _executed = False

    @staticmethod
    def init():
        """"""
        if OtelRequests._executed:
            return

        if not SETTINGS.OTEL_ENABLED:
            return

        OtelRequests._executed = True

        if not check_pkg("opentelemetry.instrumentation.requests"):
            return

        import opentelemetry.instrumentation.requests
        opentelemetry.instrumentation.requests.RequestsInstrumentor().instrument()


class OtelAioHttpClient(object):
    """"""
    _executed = False

    @staticmethod
    def init():
        """"""
        if OtelAioHttpClient._executed:
            return

        if not SETTINGS.OTEL_ENABLED:
            return

        OtelAioHttpClient._executed = True

        if not check_pkg("opentelemetry.instrumentation.aiohttp_client"):
            return

        from opentelemetry.instrumentation.aiohttp_client import (
            AioHttpClientInstrumentor
        )
        AioHttpClientInstrumentor().instrument()
