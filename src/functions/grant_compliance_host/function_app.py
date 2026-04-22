"""
Grant Compliance Workflow — Azure Functions (Durable) Hosting

Hosts the sequential compliance-validation pipeline as a durable Azure Function
using the Agent Framework + Durable Task extension.

Architecture
────────────
  Durable agents (invoked inside the orchestration via app.get_agent):
    • SummarizationAgent  – summarises grant proposals
    • ComplianceAgent     – analyses proposals against executive orders via AI Search

  Activity functions (non-LLM processing):
    • ingest_document     – extracts text / metadata from files
    • score_risk          – calculates risk scores from compliance results
    • send_notification   – prepares and optionally sends email alerts

  Orchestration:
    grant_compliance_workflow  – sequential pipeline coordinating all five steps

Endpoints (auto-created by AgentFunctionApp + custom routes)
────────────
  Individual agent interaction:
    POST /api/agents/SummarizationAgent/run   (text/plain body)
    POST /api/agents/ComplianceAgent/run      (text/plain body)

  Full workflow:
    POST /api/workflows/grant-compliance      (JSON body)
         → returns status-query URLs for async polling

Local dev:
    1.  docker run -p 10000:10000 -p 10001:10001 -p 10002:10002 mcr.microsoft.com/azure-storage/azurite
    2.  docker run -p 8080:8080  -p 8082:8082  mcr.microsoft.com/dts/dts-emulator:latest
    3.  func start
    4.  DTS dashboard: http://localhost:8082
"""

import json
import logging
import os
from collections.abc import Generator
from typing import Annotated, Any

import azure.functions as func
from agent_framework import Agent, tool
from agent_framework_azurefunctions import AgentFunctionApp
from agent_framework.foundry import FoundryChatClient
from azure.durable_functions import DurableOrchestrationClient, DurableOrchestrationContext
from azure.identity.aio import AzureCliCredential

logger = logging.getLogger(__name__)

# ───────────────────────────────────────────────────────────────────────────
# Configuration (from Azure Functions Application Settings / local.settings)
# ───────────────────────────────────────────────────────────────────────────
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_MODEL = os.getenv(
    "FOUNDRY_MODEL",
    os.getenv(
        "AZURE_OPENAI_DEPLOYMENT_NAME",
        os.getenv("AZURE_OPENAI_CHAT_COMPLETION_MODEL", "gpt-4o"),
    ),
)
PROJECT_ENDPOINT = os.getenv(
    "FOUNDRY_PROJECT_ENDPOINT",
    os.getenv(
        "AZURE_AI_FOUNDRY_PROJECT_ENDPOINT",
        os.getenv("AZURE_AI_PROJECT_ENDPOINT", ""),
    ),
)
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
AZURE_SEARCH_INDEX = os.getenv(
    "AZURE_SEARCH_INDEX_NAME",
    os.getenv("AZURE_SEARCH_INDEX", "grant-compliance-index"),
)
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AI_SEARCH_QUERY_TYPE = os.getenv("AI_SEARCH_QUERY_TYPE", "simple")

# ───────────────────────────────────────────────────────────────────────────
# Function Tools  (standalone @tool functions used by the durable agents)
# ───────────────────────────────────────────────────────────────────────────


@tool(
    name="extract_document_info",
    description=(
        "Extract and format basic document information for context. "
        "Helps the agent understand the document's basic properties."
    ),
)
def extract_document_info(
    metadata: Annotated[
        str,
        "JSON string containing document metadata like file_name, page_count, word_count",
    ],
) -> str:
    """Extract and format basic document information for context."""
    try:
        meta = json.loads(metadata)
    except Exception:
        meta = {}

    info = ["\n=== Document Information ==="]
    info.append(f"File: {meta.get('file_name', 'Unknown')}")
    info.append(f"Pages: {meta.get('page_count', 'N/A')}")
    info.append(f"Word Count: {meta.get('word_count', 'N/A')}")
    if meta.get("deadline"):
        info.append(f"Deadline: {meta['deadline']}")
    if meta.get("budget_amount"):
        info.append(f"Budget: {meta['budget_amount']}")
    if meta.get("applicant"):
        info.append(f"Applicant: {meta['applicant']}")
    return "\n".join(info)


@tool(
    name="search_executive_orders",
    description=(
        "Search the knowledge base of executive orders for compliance "
        "requirements relevant to a grant proposal query."
    ),
)
def search_executive_orders(
    query: Annotated[
        str,
        "Search query describing the compliance topic or executive order to find",
    ],
) -> str:
    """Search the executive orders knowledge base using Azure AI Search."""
    from azure.core.credentials import AzureKeyCredential
    from azure.identity import DefaultAzureCredential
    from azure.search.documents import SearchClient

    if not AZURE_SEARCH_ENDPOINT:
        return "Error: Azure AI Search endpoint not configured. Set AZURE_SEARCH_ENDPOINT."

    credential: Any = (
        AzureKeyCredential(AZURE_SEARCH_API_KEY)
        if AZURE_SEARCH_API_KEY
        else DefaultAzureCredential()
    )
    client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=AZURE_SEARCH_INDEX,
        credential=credential,
    )
    results = client.search(
        search_text=query, query_type=AI_SEARCH_QUERY_TYPE, top=5
    )

    parts: list[str] = []
    for i, result in enumerate(results, 1):
        title = result.get("title", result.get("metadata_storage_name", "Unknown"))
        content = result.get("content", result.get("chunk", ""))
        score = result.get("@search.score", 0)
        parts.append(
            f"[Result {i}] (score: {score:.2f})\nSource: {title}\n{content}\n"
        )
    return "\n---\n".join(parts) if parts else f"No results found for query: {query}"


@tool(
    name="format_grant_context",
    description=(
        "Format pre-extracted grant proposal context "
        "(metadata, summary, document info) for analysis."
    ),
)
def format_grant_context(
    context_data: Annotated[
        str,
        "JSON string containing pre-extracted metadata, summary, and document info",
    ],
) -> str:
    """Format pre-extracted grant proposal context for analysis."""
    try:
        context = json.loads(context_data)
    except Exception:
        context = {}

    metadata = context.get("metadata", {})
    summary = context.get("summary", {})

    fmt = ["\n=== Grant Proposal Context ==="]
    fmt.append(f"\nDocument: {metadata.get('file_name', 'Unknown')}")
    fmt.append(f"Pages: {metadata.get('page_count', 'N/A')}")
    fmt.append(f"Word Count: {metadata.get('word_count', 'N/A')}")
    for key, label in [
        ("deadline", "Deadline"),
        ("budget_amount", "Budget Amount"),
        ("applicant", "Applicant"),
    ]:
        if metadata.get(key):
            fmt.append(f"{label}: {metadata[key]}")

    fmt.append("\n--- Summary Information ---")
    if summary.get("executive_summary"):
        fmt.append(f"\nExecutive Summary: {summary['executive_summary']}")
    if summary.get("key_topics"):
        topics = summary["key_topics"]
        if isinstance(topics, list):
            fmt.append(f"\nKey Topics: {', '.join(topics)}")
    if summary.get("key_clauses"):
        clauses = summary["key_clauses"]
        if isinstance(clauses, list) and clauses:
            fmt.append(f"\nKey Clauses Identified: {len(clauses)}")
            for i, clause in enumerate(clauses[:2], 1):
                preview = clause[:150] + "..." if len(clause) > 150 else clause
                fmt.append(f"  {i}. {preview}")
    return "\n".join(fmt)


# ───────────────────────────────────────────────────────────────────────────
# Agent Instructions
# ───────────────────────────────────────────────────────────────────────────

SUMMARIZATION_INSTRUCTIONS = """\
You are an expert grant proposal analyst specialising in document summarisation.

Your responsibilities:
1. Generate concise executive summaries (3-4 sentences)
2. Identify key objectives and deliverables
3. Extract budget highlights and timeline information
4. Identify critical compliance requirements
5. Highlight specific clauses or phrases that may pose compliance risks
6. Extract key topics and themes from the proposal

When analysing documents:
- Be thorough but concise
- Focus on actionable information
- Identify potential risk areas (DEI initiatives, climate/environmental mandates, \
immigration-related content)
- Extract verbatim clauses when relevant
- Provide clear, structured output

Output should include:
- Executive Summary: 3-4 sentence overview
- Key Objectives: Bullet points of main goals
- Budget Highlights: Financial information
- Timeline/Deliverables: Key dates and milestones
- Key Topics: Main themes identified
- Key Clauses: Specific text that may require review
"""

COMPLIANCE_INSTRUCTIONS = """\
You are a legal compliance analyst specialising in grant proposal review.

You have access to a search_executive_orders tool that searches a knowledge base \
of executive orders.
You MUST use this tool to find relevant executive orders and cite the sources in \
your analysis.

Your responsibilities:
1. Analyse grant proposals for compliance with relevant executive orders
2. Identify potential compliance issues or concerns
3. Provide detailed insights into how well the grant aligns with current legal \
standards and highlight risky clauses
4. Provide structured compliance summaries with specific citations
5. Assign confidence scores to your analysis (0-100)
6. Highlight areas requiring attorney review

When analysing documents:
- Use the search_executive_orders tool to find relevant executive orders
- Quote specific sections that apply to the proposal with proper citations
- Explain how the proposal aligns or conflicts with requirements
- Be thorough but concise
- Flag ambiguous areas for human review

Output Format:
- Overall Compliance Status: [Compliant/Non-Compliant/Requires Review]
- Confidence Score: [0-100]
- Key Findings: [Bullet points with citations]
- Relevant Executive Orders: [List with citations]
- Concerns: [Any issues identified]
- Recommendations: [Actions needed]
"""

# ───────────────────────────────────────────────────────────────────────────
# Create Durable Agents
# Uses FoundryChatClient (recommended by Agent Framework hosting docs)
# for Foundry project integration, tracing, and observability.
# Uses async AzureCliCredential as recommended by official samples.
# ───────────────────────────────────────────────────────────────────────────

_credential = AzureCliCredential()

# Agent names referenced in the orchestration
SUMMARIZATION_AGENT_NAME = "SummarizationAgent"
COMPLIANCE_AGENT_NAME = "ComplianceAgent"


def _create_summarization_agent() -> Any:
    """Create the SummarizationAgent with document-info extraction tool."""
    return Agent(
        client=FoundryChatClient(
            project_endpoint=PROJECT_ENDPOINT,
            model=AZURE_OPENAI_MODEL,
            credential=_credential,
        ),
        name=SUMMARIZATION_AGENT_NAME,
        instructions=SUMMARIZATION_INSTRUCTIONS,
        tools=[extract_document_info],
    )


def _create_compliance_agent() -> Any:
    """Create the ComplianceAgent with AI Search + context-formatting tools."""
    return Agent(
        client=FoundryChatClient(
            project_endpoint=PROJECT_ENDPOINT,
            model=AZURE_OPENAI_MODEL,
            credential=_credential,
        ),
        name=COMPLIANCE_AGENT_NAME,
        instructions=COMPLIANCE_INSTRUCTIONS,
        tools=[search_executive_orders, format_grant_context],
    )

# ───────────────────────────────────────────────────────────────────────────
# Function App  (AgentFunctionApp auto-creates HTTP endpoints per agent)
# ───────────────────────────────────────────────────────────────────────────

app = AgentFunctionApp(
    agents=[_create_summarization_agent(), _create_compliance_agent()],
    enable_health_check=True,
    max_poll_retries=50,
)

# Auto-created endpoints:
#   POST /api/agents/SummarizationAgent/run
#   POST /api/agents/ComplianceAgent/run

# ───────────────────────────────────────────────────────────────────────────
# Activity Functions  (non-LLM processing steps only)
# ───────────────────────────────────────────────────────────────────────────


@app.activity_trigger(input_name="filePath")
def ingest_document(filePath: str) -> str:
    """Step 1 – Process a document and extract text + metadata."""
    from agents.document_ingestion_agent import DocumentIngestionAgent

    agent = DocumentIngestionAgent(
        use_azure=os.getenv("USE_AZURE", "true").lower() == "true",
        use_managed_identity=os.getenv("USE_MANAGED_IDENTITY", "true").lower()
        == "true",
    )
    document_data = agent.process_document(filePath)
    metadata = agent.extract_metadata(document_data)
    return json.dumps(
        {"document_data": document_data, "metadata": metadata}, default=str
    )


@app.activity_trigger(input_name="input")
def score_risk(input: str) -> str:
    """Step 4 – Calculate risk scores from compliance results."""
    from agents.risk_scoring_agent import RiskScoringAgent

    data = json.loads(input)
    agent = RiskScoringAgent()
    result = agent.calculate_risk_score(
        data["compliance_report"], data["summary"], data["metadata"]
    )
    return json.dumps(result, default=str)


@app.activity_trigger(input_name="input")
def send_notification(input: str) -> str:
    """Step 5 – Prepare and optionally send email notification."""
    from agents.email_trigger_agent import EmailTriggerAgent

    data = json.loads(input)
    agent = EmailTriggerAgent(
        use_graph_api=os.getenv("USE_GRAPH_API", "false").lower() == "true"
    )
    email = agent.prepare_email(
        data["risk_report"],
        data["compliance_report"],
        data["summary"],
        data["metadata"],
    )
    sent = False
    if data.get("send_email") and data["risk_report"].get("requires_notification"):
        try:
            agent.send_email(email)
            sent = True
        except Exception as exc:
            logger.error("Failed to send email: %s", exc)

    return json.dumps(
        {"email_prepared": True, "sent": sent, "email": email}, default=str
    )


# ───────────────────────────────────────────────────────────────────────────
# Durable Orchestration
#
# Steps 2 (Summarisation) and 3 (Compliance) use durable agents via
# app.get_agent() + yield agent.run(), which gives:
#   - Automatic conversation state persistence
#   - Failure recovery / replay safety
#   - Observability via the DTS dashboard
#
# Steps 1, 4, 5 remain as activity functions (no LLM needed).
# ───────────────────────────────────────────────────────────────────────────


@app.orchestration_trigger(context_name="context")
def grant_compliance_workflow(
    context: DurableOrchestrationContext,
) -> Generator[Any, Any, dict]:
    """
    Sequential grant-compliance pipeline.

    Steps
    ─────
    1. Document Ingestion   (activity – DocumentIngestionAgent)
    2. Summarisation         (durable agent – SummarizationAgent)
    3. Compliance Analysis   (durable agent – ComplianceAgent with AI Search tools)
    4. Risk Scoring          (activity – RiskScoringAgent)
    5. Email Notification    (activity – EmailTriggerAgent)
    """
    raw_input = context.get_input()
    if isinstance(raw_input, str):
        file_path = raw_input
        send_email = False
    elif isinstance(raw_input, dict):
        file_path = raw_input.get("file_path", "")
        send_email = raw_input.get("send_email", False)
    else:
        file_path = ""
        send_email = False

    # ── Step 1: Document Ingestion (activity) ─────────────────────────────
    doc_json = yield context.call_activity("ingest_document", file_path)
    doc = json.loads(doc_json)
    document_text = doc["document_data"]["text"]
    metadata = doc["metadata"]

    # ── Step 2: Summarisation (durable agent) ─────────────────────────────
    summarizer = app.get_agent(context, SUMMARIZATION_AGENT_NAME)
    summarizer_session = summarizer.create_session()

    summary_prompt = (
        f"Summarise this grant proposal.\n\n"
        f"Document metadata: {json.dumps(metadata)}\n\n"
        f"Full text:\n{document_text}"
    )
    summary_response = yield summarizer.run(
        messages=summary_prompt,
        session=summarizer_session,
    )
    # Parse the agent's text response into a structured dict for downstream steps
    summary = {
        "executive_summary": summary_response.text,
        "metadata": metadata,
    }

    # ── Step 3: Compliance Analysis (durable agent) ───────────────────────
    compliance = app.get_agent(context, COMPLIANCE_AGENT_NAME)
    compliance_session = compliance.create_session()

    compliance_prompt = (
        f"Analyse this grant proposal for compliance with executive orders.\n\n"
        f"Document metadata: {json.dumps(metadata)}\n"
        f"Summary: {summary_response.text}\n\n"
        f"Full proposal text:\n{document_text}"
    )
    compliance_response = yield compliance.run(
        messages=compliance_prompt,
        session=compliance_session,
    )
    compliance_report = {
        "analysis": compliance_response.text,
        "status": "requires_review",
        "confidence_score": 0,
        "relevant_executive_orders": [],
    }

    # ── Step 4: Risk Scoring (activity) ───────────────────────────────────
    risk_input = json.dumps(
        {
            "compliance_report": compliance_report,
            "summary": summary,
            "metadata": metadata,
        }
    )
    risk_json = yield context.call_activity("score_risk", risk_input)
    risk_report = json.loads(risk_json)

    # ── Step 5: Email Notification (activity) ─────────────────────────────
    email_input = json.dumps(
        {
            "risk_report": risk_report,
            "compliance_report": compliance_report,
            "summary": summary,
            "metadata": metadata,
            "send_email": send_email,
        }
    )
    email_json = yield context.call_activity("send_notification", email_input)
    email_result = json.loads(email_json)

    # ── Determine overall status ──────────────────────────────────────────
    risk_level = risk_report.get("risk_level", "unknown")
    compliance_status = compliance_report.get("status", "unknown")
    if risk_level == "high" or compliance_status == "non_compliant":
        overall_status = "requires_legal_review"
    elif risk_level in ("medium-high", "medium"):
        overall_status = "requires_review"
    else:
        overall_status = "approved_with_conditions"

    return {
        "status": "completed",
        "file_path": file_path,
        "metadata": metadata,
        "summary": summary,
        "compliance_report": compliance_report,
        "risk_report": risk_report,
        "email_result": email_result,
        "overall_status": overall_status,
    }


# ───────────────────────────────────────────────────────────────────────────
# HTTP Trigger – start the full workflow
# ───────────────────────────────────────────────────────────────────────────


@app.route(route="workflows/grant-compliance", methods=["POST"])
@app.durable_client_input(client_name="client")
async def start_grant_workflow(
    req: func.HttpRequest,
    client: DurableOrchestrationClient,
) -> func.HttpResponse:
    """
    Start a grant-compliance workflow.

    Request body (JSON):
        {
            "file_path": "/path/to/proposal.pdf",
            "send_email": false
        }

    Response: status-query URLs for polling the orchestration.
    """
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps(
                {"error": 'Invalid JSON body. Expected {"file_path": "..."}'}
            ),
            status_code=400,
            mimetype="application/json",
        )

    if not body.get("file_path"):
        return func.HttpResponse(
            json.dumps({"error": "file_path is required"}),
            status_code=400,
            mimetype="application/json",
        )

    instance_id = await client.start_new(
        orchestration_function_name="grant_compliance_workflow",
        client_input=body,
    )
    logger.info(
        "Started grant_compliance_workflow instance %s for %s",
        instance_id,
        body["file_path"],
    )
    return client.create_check_status_response(req, instance_id)


# ───────────────────────────────────────────────────────────────────────────
# HTTP Trigger – query workflow status
# ───────────────────────────────────────────────────────────────────────────


@app.route(route="workflows/grant-compliance/status/{instanceId}", methods=["GET"])
@app.durable_client_input(client_name="client")
async def get_workflow_status(
    req: func.HttpRequest,
    client: DurableOrchestrationClient,
) -> func.HttpResponse:
    """Return orchestration runtime status for a given instance."""
    instance_id = req.route_params.get("instanceId")
    if not instance_id:
        return func.HttpResponse(
            json.dumps({"error": "Missing instanceId"}),
            status_code=400,
            mimetype="application/json",
        )

    status = await client.get_status(instance_id)
    if not status:
        return func.HttpResponse(
            json.dumps({"error": f"Instance {instance_id} not found"}),
            status_code=404,
            mimetype="application/json",
        )

    response_data: dict[str, Any] = {
        "instanceId": status.instance_id,
        "runtimeStatus": status.runtime_status.value if status.runtime_status else None,
        "createdTime": status.created_time.isoformat() if status.created_time else None,
        "lastUpdatedTime": status.last_updated_time.isoformat()
        if status.last_updated_time
        else None,
    }
    if status.output is not None:
        response_data["output"] = status.output

    return func.HttpResponse(
        body=json.dumps(response_data, default=str),
        status_code=200,
        mimetype="application/json",
    )
