"""
Foundry Hosted Agent — Grant Compliance

Exposes the ComplianceAgent via the Foundry Responses protocol so it appears
in the Foundry portal and can be invoked through the standard Foundry endpoint.

This is an ALTERNATIVE hosting option to the Azure Functions host in
src/functions/grant_compliance_host/.  Both share the same agent logic.
"""

import json
import logging
import os
from typing import Annotated, Any

from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ───────────────────────────────────────────────────────────────────────────
# Configuration  (injected by the Foundry platform at runtime)
# ───────────────────────────────────────────────────────────────────────────

PROJECT_ENDPOINT = os.environ.get(
    "FOUNDRY_PROJECT_ENDPOINT",
    os.environ.get("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT", ""),
)
MODEL = os.environ.get(
    "AZURE_AI_MODEL_DEPLOYMENT_NAME",
    os.environ.get("FOUNDRY_MODEL", os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")),
)
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
AZURE_SEARCH_ENDPOINT = os.environ.get("AZURE_SEARCH_ENDPOINT", "")
AZURE_SEARCH_INDEX = os.environ.get(
    "AZURE_SEARCH_INDEX_NAME",
    os.environ.get("AZURE_SEARCH_INDEX", "grant-compliance-index"),
)
AZURE_SEARCH_API_KEY = os.environ.get("AZURE_SEARCH_API_KEY")
AI_SEARCH_QUERY_TYPE = os.environ.get("AI_SEARCH_QUERY_TYPE", "semantic")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.environ.get(
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"
)

# ───────────────────────────────────────────────────────────────────────────
# Tools  (identical to function_app.py — shared compliance search logic)
# ───────────────────────────────────────────────────────────────────────────


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
    """Search the executive orders knowledge base using Azure AI Search (hybrid: text + vector)."""
    from azure.core.credentials import AzureKeyCredential
    from azure.identity import DefaultAzureCredential as SyncCredential
    from azure.identity import get_bearer_token_provider
    from azure.search.documents import SearchClient
    from azure.search.documents.models import VectorizedQuery

    if not AZURE_SEARCH_ENDPOINT:
        return "Error: Azure AI Search endpoint not configured. Set AZURE_SEARCH_ENDPOINT."

    credential: Any = (
        AzureKeyCredential(AZURE_SEARCH_API_KEY)
        if AZURE_SEARCH_API_KEY
        else SyncCredential()
    )
    client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=AZURE_SEARCH_INDEX,
        credential=credential,
    )

    # Generate query embedding for hybrid search
    vector_queries: list[Any] | None = None
    try:
        from openai import AzureOpenAI

        if AZURE_SEARCH_API_KEY:
            openai_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
            if openai_key:
                embedding_client = AzureOpenAI(
                    azure_endpoint=AZURE_OPENAI_ENDPOINT,
                    api_key=openai_key,
                    api_version="2024-06-01",
                )
            else:
                embedding_client = None
        else:
            token_provider = get_bearer_token_provider(
                SyncCredential(),
                "https://cognitiveservices.azure.com/.default",
            )
            embedding_client = AzureOpenAI(
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
                azure_ad_token_provider=token_provider,
                api_version="2024-06-01",
            )

        if embedding_client:
            embed_resp = embedding_client.embeddings.create(
                input=query, model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
            )
            vector_queries = [
                VectorizedQuery(
                    vector=embed_resp.data[0].embedding,
                    k_nearest_neighbors=5,
                    fields="content_vector",
                )
            ]
    except Exception as exc:
        logger.warning("Embedding generation failed, falling back to text-only: %s", exc)

    results = client.search(
        search_text=query,
        query_type=AI_SEARCH_QUERY_TYPE,
        semantic_configuration_name=(
            "default-semantic-config" if AI_SEARCH_QUERY_TYPE == "semantic" else None
        ),
        top=5,
        vector_queries=vector_queries,
    )

    parts: list[str] = []
    for i, result in enumerate(results, 1):
        title = result.get("title", result.get("metadata_storage_name", "Unknown"))
        content = result.get("content", result.get("chunk", ""))
        score = result.get("@search.score", 0)
        parts.append(f"[Result {i}] (score: {score:.2f})\nSource: {title}\n{content}\n")
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

    if summary.get("executive_summary"):
        fmt.append(f"\nExecutive Summary: {summary['executive_summary']}")
    if summary.get("key_topics"):
        topics = summary["key_topics"]
        if isinstance(topics, list):
            fmt.append(f"\nKey Topics: {', '.join(topics)}")
    return "\n".join(fmt)


# ───────────────────────────────────────────────────────────────────────────
# Agent Instructions
# ───────────────────────────────────────────────────────────────────────────

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
# Create Agent + Server
# ───────────────────────────────────────────────────────────────────────────

credential = DefaultAzureCredential()

agent = Agent(
    client=FoundryChatClient(
        project_endpoint=PROJECT_ENDPOINT,
        model=MODEL,
        credential=credential,
    ),
    name="GrantComplianceAgent",
    instructions=COMPLIANCE_INSTRUCTIONS,
    tools=[search_executive_orders, format_grant_context],
    default_options={"store": False},
)

server = ResponsesHostServer(agent)

if __name__ == "__main__":
    server.run()
