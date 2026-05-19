# Observability Guide

This document describes how to enable **distributed tracing** and **production monitoring** for the Grant Compliance pipeline using [OpenTelemetry](https://opentelemetry.io/) and [Azure Application Insights](https://learn.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview).

## Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│  Grant Compliance Pipeline                                  │
│                                                             │
│  DocumentIngestion → Summarization → Compliance → Risk → Email │
│        │                  │               │          │      │
│        └──────────────────┴───────────────┴──────────┘      │
│                           │                                  │
│                   OpenTelemetry Spans                        │
└───────────────────────────┬──────────────────────────────────┘
                            │
                ┌───────────▼───────────┐
                │  Azure Application    │
                │  Insights             │
                │  ─────────────────    │
                │  • Transaction search │
                │  • Dependency map     │
                │  • Custom metrics     │
                │  • Alert rules        │
                └───────────┬───────────┘
                            │
                ┌───────────▼───────────┐
                │  Foundry Observability│
                │  Dashboard            │
                │  ─────────────────    │
                │  • Agent traces       │
                │  • Evaluation metrics │
                │  • Quality scores     │
                └───────────────────────┘
```

## What Is Traced

The pipeline emits OpenTelemetry spans for key events:

| Span / Event | Description |
|---|---|
| `pipeline.process_grant_proposal` | Root span for the full workflow |
| `pipeline.document_ingestion` | Document extraction step |
| `pipeline.summarization` | Summary generation step |
| `pipeline.compliance_validation` | Compliance analysis step |
| `pipeline.risk_scoring` | Risk calculation step |
| `pipeline.email_notification` | Notification decision step |
| **Event:** `human_review_triggered` | Emitted when risk score falls below the notification threshold |
| **Event:** `low_certainty_alert` | Emitted when assessment certainty is < 60% (ambiguity zone) |
| **Event:** `executor_failed` | Emitted when a pipeline step fails |

### Span Attributes

Each span carries structured attributes:

```
risk.score           = 42.5
risk.level           = "high"
risk.certainty       = 57.5
risk.requires_notification = true
compliance.status    = "non_compliant"
compliance.score     = 30.0
compliance.confidence = 72
compliance.violation_count = 3
compliance.warning_count  = 1
compliance.eo_count  = 2
proposal.file_path   = "proposals/PROP-003.txt"
workflow.status       = "requires_legal_review"
```

## Quick Start — Local Development

Traces are printed to the console by default (no Azure credentials required):

```bash
# Run the evaluation demo — traces appear in stdout
python scripts/demo_evaluation.py --risk-only
```

Or use the observability module directly:

```python
from agents.observability import get_tracer, trace_agent_step, record_risk_decision

tracer = get_tracer()

with trace_agent_step("my_custom_step", {"proposal.id": "PROP-001"}) as span:
    # ... do work ...
    record_risk_decision(span, risk_report)
```

## Production Setup — Azure Application Insights

### 1. Install the exporter

```bash
pip install azure-monitor-opentelemetry-exporter
```

### 2. Set the connection string

Add to your `.env` file:

```
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=xxx;IngestionEndpoint=https://...
```

You can find this in the Azure portal under your Application Insights resource → **Overview** → **Connection String**.

### 3. Configure at application startup

The pipeline auto-detects `APPLICATIONINSIGHTS_CONNECTION_STRING` and routes traces to Azure Monitor. No code changes required.

To configure explicitly:

```python
from agents.observability import configure_azure_monitor

configure_azure_monitor()  # reads from environment
# or
configure_azure_monitor(connection_string="InstrumentationKey=...")
```

### 4. Verify in the portal

1. Open your **Application Insights** resource in the Azure portal
2. Go to **Transaction search** → filter by Operation Name = `pipeline.process_grant_proposal`
3. Click a trace to see the full span waterfall (each agent step as a child span)
4. Check **Custom Events** for `human_review_triggered` and `low_certainty_alert`

## Setting Up Alerts

Create Azure Monitor alerts for critical compliance events:

### Alert: High-Risk Proposals

```kusto
// KQL query for Azure Monitor alert rule
customEvents
| where name == "human_review_triggered"
| extend risk_score = toreal(customDimensions["risk.score"])
| where risk_score < 60
| project timestamp, risk_score, risk_level = tostring(customDimensions["risk.level"])
```

**Recommended alert**: Fire when > 0 high-risk proposals are processed in a 15-minute window.

### Alert: Low Certainty (Ambiguity Zone)

```kusto
customEvents
| where name == "low_certainty_alert"
| extend certainty = toreal(customDimensions["certainty"])
| project timestamp, certainty, reason = tostring(customDimensions["reason"])
```

**Recommended alert**: Fire when certainty < 55% — indicates the model may need prompt tuning or additional training data.

### Alert: Pipeline Failures

```kusto
customEvents
| where name == "executor_failed" or name == "workflow_failed"
| extend error_msg = tostring(customDimensions["error.message"])
| project timestamp, error_msg
```

### Dashboard: Risk Score Drift

```kusto
// Monitor average risk scores over time to detect drift
dependencies
| where name startswith "pipeline."
| extend risk_score = toreal(customDimensions["risk.score"])
| where isnotnull(risk_score)
| summarize avg_risk = avg(risk_score), p50 = percentile(risk_score, 50) by bin(timestamp, 1h)
| render timechart
```

## Foundry Portal Integration

When using the Foundry Agent Service (`sequential_workflow_orchestrator_foundry.py`), traces are automatically visible in the **Foundry Observability Dashboard**:

1. Open [Azure AI Foundry portal](https://ai.azure.com)
2. Navigate to your project → **Observability**
3. View agent traces, evaluation metrics, and quality scores
4. The dashboard shows:
   - Per-agent latency and success rates
   - Token consumption by agent step
   - Evaluation score trends over time
   - Safety and quality metric dashboards

See [Foundry Observability Docs](https://learn.microsoft.com/en-us/azure/foundry/concepts/observability) for details.

## Evaluation + Observability Together

The evaluation framework and observability work together:

```python
from agent_framework import evaluate_agent, LocalEvaluator, evaluator
from agents.observability import get_tracer

tracer = get_tracer()

# Traces from evaluate_agent calls are automatically captured
with tracer.start_as_current_span("evaluation.compliance_batch"):
    results = await evaluate_agent(
        agent=compliance_agent,
        queries=queries,
        evaluators=local_evaluator,
    )
    # results.assert_passed()  # Use in CI/CD to gate deployments
```

In the notebook ([notebooks/GrantComplianceEvaluator.ipynb](../notebooks/GrantComplianceEvaluator.ipynb)), Section 7 demonstrates traced risk scoring with custom events.

## Custom Instrumentation

To add tracing to your own agent steps:

```python
from agents.observability import trace_agent_step, record_risk_decision

# Wrap any step
with trace_agent_step("custom_analysis", {"doc.type": "grant"}) as span:
    result = my_custom_analysis(document)
    span.set_attribute("analysis.score", result["score"])
    
    if result["score"] < threshold:
        span.add_event("threshold_breach", attributes={
            "score": result["score"],
            "threshold": threshold,
        })
```

## Dependencies

| Package | Purpose |
|---|---|
| `opentelemetry-api` | Core tracing API |
| `opentelemetry-sdk` | Tracer provider and span processors |
| `azure-monitor-opentelemetry-exporter` | Export to Application Insights (production) |

These are included in `requirements.txt`. The Azure Monitor exporter is optional for local development.

## References

- [Azure AI Foundry Observability](https://learn.microsoft.com/en-us/azure/foundry/concepts/observability)
- [Agent Framework Evaluation](https://learn.microsoft.com/en-us/agent-framework/agents/evaluation?pivots=programming-language-python)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [Azure Monitor OpenTelemetry Exporter](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-configuration?tabs=python)
