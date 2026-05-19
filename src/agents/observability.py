"""
Observability utilities for the Grant Compliance pipeline.

Provides OpenTelemetry tracing helpers that instrument agent steps,
risk decisions, and human-deferral events.  When connected to Azure
Application Insights the spans appear in the Foundry observability
dashboard automatically.

Usage:
    from agents.observability import get_tracer, trace_agent_step, record_risk_decision

Production setup (in your app entry-point):
    from agents.observability import configure_azure_monitor
    configure_azure_monitor()          # reads APPLICATIONINSIGHTS_CONNECTION_STRING
"""

import logging
import os
from contextlib import contextmanager
from typing import Any, Dict, Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor

logger = logging.getLogger(__name__)

_TRACER_NAME = "grant-compliance-pipeline"

# ---------------------------------------------------------------------------
# Provider bootstrap (idempotent)
# ---------------------------------------------------------------------------

_provider_configured = False


def _ensure_provider() -> None:
    """Set up a TracerProvider if one hasn't been registered yet."""
    global _provider_configured
    if _provider_configured:
        return

    provider = TracerProvider()

    # If APPLICATIONINSIGHTS_CONNECTION_STRING is set, export to Azure Monitor
    conn_str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if conn_str:
        try:
            from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

            exporter = AzureMonitorTraceExporter(connection_string=conn_str)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("OpenTelemetry: Azure Monitor exporter configured")
        except ImportError:
            logger.warning(
                "azure-monitor-opentelemetry-exporter not installed — "
                "falling back to console exporter. "
                "Run: pip install azure-monitor-opentelemetry-exporter"
            )
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter

            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    else:
        # Dev/demo: export to console
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter

        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        logger.info("OpenTelemetry: Console exporter configured (set APPLICATIONINSIGHTS_CONNECTION_STRING for Azure Monitor)")

    trace.set_tracer_provider(provider)
    _provider_configured = True


def configure_azure_monitor(connection_string: Optional[str] = None) -> None:
    """
    Explicitly configure Azure Monitor export.

    Call this once at application startup to send traces to Application Insights.
    If *connection_string* is ``None`` the value is read from
    ``APPLICATIONINSIGHTS_CONNECTION_STRING``.
    """
    global _provider_configured
    conn = connection_string or os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not conn:
        raise ValueError(
            "No connection string provided. Set APPLICATIONINSIGHTS_CONNECTION_STRING "
            "or pass connection_string= explicitly."
        )

    from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

    provider = TracerProvider()
    exporter = AzureMonitorTraceExporter(connection_string=conn)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    _provider_configured = True
    logger.info("OpenTelemetry: Azure Monitor exporter configured (explicit)")


def get_tracer(name: str = _TRACER_NAME) -> trace.Tracer:
    """Return a tracer, bootstrapping the provider on first call."""
    _ensure_provider()
    return trace.get_tracer(name)


# ---------------------------------------------------------------------------
# Convenience helpers for agent instrumentation
# ---------------------------------------------------------------------------

@contextmanager
def trace_agent_step(step_name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Context manager that wraps an agent pipeline step in a span.

    Example::

        with trace_agent_step("compliance_validation", {"proposal.id": "PROP-003"}):
            result = await compliance_agent.analyze_proposal(text)
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(f"pipeline.{step_name}") as span:
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)
        yield span


def record_risk_decision(
    span: trace.Span,
    risk_report: Dict[str, Any],
    proposal_id: str = "",
) -> None:
    """
    Attach risk-scoring telemetry to the current span and emit events
    for human-review triggers and low-certainty alerts.
    """
    score = risk_report.get("overall_score", 0)
    level = risk_report.get("risk_level", "unknown")
    certainty = risk_report.get("assessment_certainty", 0)
    needs_notification = risk_report.get("requires_notification", False)

    span.set_attribute("risk.score", score)
    span.set_attribute("risk.level", level)
    span.set_attribute("risk.certainty", certainty)
    span.set_attribute("risk.requires_notification", needs_notification)
    if proposal_id:
        span.set_attribute("proposal.id", proposal_id)

    # Event: human review triggered
    if needs_notification:
        span.add_event(
            "human_review_triggered",
            attributes={
                "risk.level": level,
                "risk.score": score,
                "reason": f"Score {score:.1f} below notification threshold",
            },
        )

    # Event: low certainty alert
    if certainty < 60:
        span.add_event(
            "low_certainty_alert",
            attributes={
                "certainty": certainty,
                "reason": "Assessment near ambiguity zone — increased monitoring recommended",
            },
        )


def record_compliance_result(
    span: trace.Span,
    compliance_report: Dict[str, Any],
) -> None:
    """Attach compliance analysis telemetry to the current span."""
    span.set_attribute("compliance.status", compliance_report.get("overall_status", "unknown"))
    span.set_attribute("compliance.score", compliance_report.get("compliance_score", 0))
    span.set_attribute("compliance.confidence", compliance_report.get("confidence_score", 0))
    span.set_attribute("compliance.violation_count", len(compliance_report.get("violations", [])))
    span.set_attribute("compliance.warning_count", len(compliance_report.get("warnings", [])))
    span.set_attribute(
        "compliance.eo_count",
        len(compliance_report.get("relevant_executive_orders", [])),
    )
