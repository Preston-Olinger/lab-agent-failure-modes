import functools
import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

provider = TracerProvider(resource=Resource.create({"service.name": "lab-agent"}))
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint=os.environ.get("OTLP_TRACES_ENDPOINT", "http://localhost:4318/v1/traces")))
)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("labagent")

KEYS = ("strategy", "i", "retries", "last_error", "next_action", "status", "actions")


def _val(v):
    return v if isinstance(v, (str, bool, int, float)) else str(v)


def traced(name):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(state):
            with tracer.start_as_current_span(name) as span:
                for k in KEYS:
                    if state.get(k) not in (None, ""):
                        span.set_attribute("in." + k, _val(state[k]))
                out = fn(state)
                for k in KEYS:
                    if out.get(k) not in (None, ""):
                        span.set_attribute("out." + k, _val(out[k]))
                if out.get("reasons"):
                    span.set_attribute("out.reason", str(out["reasons"][-1]))
                return out
        return wrapper
    return deco


def flush():
    provider.force_flush()