# Restructuring as a Single Prompt Agent

This document describes how to consolidate the multiple `_foundry.py` agents (`ComplianceAgentFoundry`, `SummarizationAgentFoundry`, and the `SequentialWorkflowOrchestratorFoundry`) into a **single Prompt agent** using the Microsoft Foundry Agent Service.

## Background

### Current Architecture (Multi-Agent)

The current implementation creates **three separate Prompt agents** in Python code, coordinated by the `SequentialWorkflowOrchestratorFoundry`:

1. **SummarizationAgentFoundry** — Summarizes grant proposals and extracts key clauses
2. **ComplianceAgentFoundry** — Analyzes compliance against executive orders using Azure AI Search
3. **SequentialWorkflowOrchestratorFoundry** — Creates both agents above, manages conversations, passes data between them

Each agent is created via `PromptAgentDefinition`, invoked through separate conversations, and cleaned up after use. The Python orchestrator handles data flow between agents.

### Proposed Architecture (Single Prompt Agent)

A **single Prompt agent** that handles the complete grant compliance workflow — summarization, compliance analysis, risk flagging, and structured output — in one agent definition with one conversation.

This aligns with the [Prompt agent](https://learn.microsoft.com/en-us/azure/foundry/agents/overview#prompt-agents) pattern from Microsoft documentation:

> Prompt agents are defined entirely through configuration — instructions, model selection, and tools. Create them in the Foundry portal or through the API or SDKs, and Agent Service handles the orchestration and hosting automatically.

## Foundry Agent Types Reference

Per [Microsoft Foundry Agent Service documentation](https://learn.microsoft.com/en-us/azure/foundry/agents/overview):

| Type | Kind | Code Required | Best For |
|------|------|---------------|----------|
| **Prompt agents** | `PromptAgentDefinition` | No | Prototyping, simple tasks, single-agent workflows |
| **Workflow agents** (preview) | Declarative YAML / Visual Builder | No (YAML optional) | Multi-step automation, agent-to-agent coordination |
| **Hosted agents** (preview) | Container-based | Yes | Full control, custom frameworks |

This restructuring uses **Prompt agents** — the simplest and most maintainable approach for this use case.

## Single Agent Design

### Agent Instructions

The single agent combines summarization, compliance analysis, and risk flagging into one set of instructions:

```python
GRANT_COMPLIANCE_AGENT_INSTRUCTIONS = """You are an expert grant proposal compliance analyst.

You have access to an Azure AI Search tool that searches a knowledge base of executive orders.
You MUST always provide citations for answers using the tool and render them as: `[message_idx:search_idx†source]`.

When given a grant proposal, perform a COMPLETE analysis in a single response:

## STEP 1: EXECUTIVE SUMMARY
- Generate a 3-4 sentence executive summary of the proposal
- Identify key objectives and deliverables
- Extract budget highlights and timeline information

## STEP 2: KEY CLAUSE EXTRACTION
- Identify specific clauses or phrases that may pose compliance risks
- Focus on: DEI initiatives, climate/environmental mandates, gender ideology, immigration-related content
- Extract verbatim text when relevant

## STEP 3: COMPLIANCE ANALYSIS
- Use the azure_ai_search tool to find relevant executive orders
- Analyze the proposal against each relevant executive order
- Quote specific sections that apply with proper citations
- Explain how the proposal aligns or conflicts with requirements

## STEP 4: RISK ASSESSMENT
- Flag any compliance risks or concerns
- Identify ambiguous areas requiring human review

## OUTPUT FORMAT (use this exact structure):

### Executive Summary
[3-4 sentence overview]

### Key Objectives
[Bullet points of main goals]

### Key Clauses
[Specific phrases/requirements that may pose compliance risks - extract verbatim]

### Key Topics
[Main themes: compliance, sustainability, equity, cybersecurity, climate, DEI, immigration, etc.]

### Overall Compliance Status
[Compliant / Non-Compliant / Requires Review]

### Confidence Score
[0-100] - how certain you are about your analysis

### Key Findings
[Bullet points with citations to specific executive orders]

### Relevant Executive Orders
[List all applicable EOs with their numbers and brief descriptions]

### Concerns
[Any compliance issues or risks identified]

### Recommendations
[Actions needed to address any issues]
"""
```

### Python Implementation

Following the [Microsoft Foundry quickstart](https://learn.microsoft.com/en-us/azure/foundry/quickstarts/get-started-code) pattern:

```python
"""
Grant Compliance Prompt Agent — Single Agent Implementation
Uses Azure AI Foundry Agent Service with PromptAgentDefinition.

Reference:
  https://learn.microsoft.com/en-us/azure/foundry/agents/overview#prompt-agents
  https://learn.microsoft.com/en-us/azure/foundry/quickstarts/get-started-code
"""

import os
import json
import logging
from typing import Dict, Any, Optional

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import (
    AzureAISearchTool,
    PromptAgentDefinition,
    AzureAISearchToolResource,
    AISearchIndexResource,
    AzureAISearchQueryType,
)
from azure.identity.aio import DefaultAzureCredential

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT", "")
MODEL_DEPLOYMENT = (
    os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME")
    or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
)
SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX_NAME", "grant-compliance-index")
SEARCH_CONNECTION_ID = os.getenv("AI_SEARCH_PROJECT_CONNECTION_ID", "")
AGENT_NAME = "GrantComplianceAgent"

# ---------------------------------------------------------------------------
# Agent Instructions (single comprehensive prompt)
# ---------------------------------------------------------------------------

AGENT_INSTRUCTIONS = """You are an expert grant proposal compliance analyst.

You have access to an Azure AI Search tool that searches a knowledge base of executive orders.
You MUST always provide citations for answers using the tool and render them as: `[message_idx:search_idx†source]`.

When given a grant proposal, perform a COMPLETE analysis in a single response:

## STEP 1: EXECUTIVE SUMMARY
- Generate a 3-4 sentence executive summary of the proposal
- Identify key objectives and deliverables
- Extract budget highlights and timeline information

## STEP 2: KEY CLAUSE EXTRACTION
- Identify specific clauses or phrases that may pose compliance risks
- Focus on: DEI initiatives, climate/environmental mandates, gender ideology, immigration-related content
- Extract verbatim text when relevant

## STEP 3: COMPLIANCE ANALYSIS
- Use the azure_ai_search tool to find relevant executive orders
- Analyze the proposal against each relevant executive order
- Quote specific sections that apply with proper citations
- Explain how the proposal aligns or conflicts with requirements

## STEP 4: RISK ASSESSMENT
- Flag any compliance risks or concerns
- Identify ambiguous areas requiring human review

## OUTPUT FORMAT (use this exact structure):

### Executive Summary
[3-4 sentence overview]

### Key Objectives
[Bullet points of main goals]

### Key Clauses
[Specific phrases/requirements that may pose compliance risks - extract verbatim]

### Key Topics
[Main themes identified]

### Overall Compliance Status
[Compliant / Non-Compliant / Requires Review]

### Confidence Score
[0-100]

### Key Findings
[Bullet points with citations to specific executive orders]

### Relevant Executive Orders
[List all applicable EOs with numbers and brief descriptions]

### Concerns
[Any compliance issues or risks identified]

### Recommendations
[Actions needed to address any issues]
"""


# ---------------------------------------------------------------------------
# Azure AI Search Tool Setup
# ---------------------------------------------------------------------------

def build_search_tool() -> AzureAISearchTool:
    """Build the Azure AI Search tool for the agent."""
    if not SEARCH_CONNECTION_ID:
        raise ValueError(
            "AI_SEARCH_PROJECT_CONNECTION_ID must be set. "
            "Configure the connection in your Azure AI Foundry project."
        )

    return AzureAISearchTool(
        azure_ai_search=AzureAISearchToolResource(
            indexes=[
                AISearchIndexResource(
                    project_connection_id=SEARCH_CONNECTION_ID,
                    index_name=SEARCH_INDEX,
                    query_type=AzureAISearchQueryType.SIMPLE,
                ),
            ]
        )
    )


# ---------------------------------------------------------------------------
# Single Agent: Create, Invoke, Cleanup
# ---------------------------------------------------------------------------

async def create_agent(project_client: AIProjectClient) -> Any:
    """
    Create the Grant Compliance Prompt agent in Foundry.

    Reference: https://learn.microsoft.com/en-us/azure/foundry/quickstarts/get-started-code#create-an-agent
    """
    search_tool = build_search_tool()

    agent = await project_client.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(
            model=MODEL_DEPLOYMENT,
            instructions=AGENT_INSTRUCTIONS,
            tools=[search_tool],
        ),
        description=(
            "Single Prompt agent for grant compliance analysis — "
            "summarizes proposals, checks executive order compliance, "
            "and flags risks with citations."
        ),
    )
    logger.info(
        f"Agent created (id: {agent.id}, name: {agent.name}, version: {agent.version})"
    )
    return agent


async def analyze_proposal(
    proposal_text: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Analyze a grant proposal using a single Prompt agent.

    Steps:
      1. Create the agent (PromptAgentDefinition)
      2. Open a conversation
      3. Send the proposal as input and stream the response
      4. Clean up conversation and agent

    Reference: https://learn.microsoft.com/en-us/azure/foundry/quickstarts/get-started-code#chat-with-an-agent
    """
    credential = DefaultAzureCredential(exclude_environment_credential=True)

    async with (
        credential,
        AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential) as project_client,
        project_client.get_openai_client() as openai_client,
    ):
        # --- Create agent ---
        agent = await create_agent(project_client)

        try:
            # --- Build prompt ---
            metadata_str = json.dumps(metadata or {}, indent=2, default=str)
            prompt = f"""Analyze the following grant proposal for compliance with relevant executive orders.

GRANT PROPOSAL TEXT:
{proposal_text}

DOCUMENT METADATA:
{metadata_str}

Search the knowledge base for relevant executive orders and provide a complete analysis
following the output format in your instructions.
Use the Azure AI Search tool to find and cite relevant executive orders.
Render citations as: `[message_idx:search_idx†source]`
"""

            # --- Create conversation ---
            conversation = await openai_client.conversations.create()
            logger.info(f"Created conversation (id: {conversation.id})")

            try:
                # --- Stream response ---
                response_text = ""
                stream = await openai_client.responses.create(
                    conversation=conversation.id,
                    extra_body={
                        "agent_reference": {
                            "name": agent.name,
                            "type": "agent_reference",
                        }
                    },
                    input=prompt,
                    stream=True,
                    tool_choice="required",
                )

                async for event in stream:
                    if event.type == "response.output_text.delta":
                        response_text += event.delta

                logger.info("Analysis complete")

            finally:
                await openai_client.conversations.delete(
                    conversation_id=conversation.id
                )
                logger.info("Conversation deleted")

        finally:
            # Clean up agent (unless persistence is enabled)
            persist = os.getenv("PERSIST_FOUNDRY_AGENTS", "false").lower() == "true"
            if not persist:
                await project_client.agents.delete_version(
                    agent_name=agent.name,
                    agent_version=agent.version,
                )
                logger.info("Agent deleted")
            else:
                logger.info(
                    f"Agent persisted: {agent.name} (version: {agent.version})"
                )

    # --- Parse structured output ---
    return parse_response(response_text)


# ---------------------------------------------------------------------------
# Response Parsing
# ---------------------------------------------------------------------------

def parse_response(text: str) -> Dict[str, Any]:
    """Parse the agent's structured response into a dictionary."""
    import re

    def extract_section(header: str) -> str:
        pattern = rf"###?\s*{header}[:\s]*\n(.+?)(?=\n###?\s|\Z)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""

    # Extract confidence score
    conf_match = re.search(r"confidence\s*score[:\s\n\-*]*(\d+)", text, re.IGNORECASE)
    confidence_score = int(conf_match.group(1)) if conf_match else 70

    # Extract status
    text_lower = text.lower()
    if "non-compliant" in text_lower:
        status = "Non-Compliant"
    elif "compliant" in text_lower:
        status = "Compliant"
    else:
        status = "Requires Review"

    # Extract EO references
    eo_matches = re.findall(
        r"(?:Executive Order|EO|E\.O\.)[\s#]*(\d{4,5})", text, re.IGNORECASE
    )
    unique_eos = list(set(eo_matches))

    return {
        "executive_summary": extract_section("Executive Summary"),
        "key_objectives": extract_section("Key Objectives"),
        "key_clauses": extract_section("Key Clauses"),
        "key_topics": extract_section("Key Topics"),
        "compliance_status": status,
        "confidence_score": confidence_score,
        "key_findings": extract_section("Key Findings"),
        "relevant_executive_orders": [
            {"eo_number": eo, "title": f"Executive Order {eo}"} for eo in unique_eos
        ],
        "concerns": extract_section("Concerns"),
        "recommendations": extract_section("Recommendations"),
        "full_analysis": text,
        "service": "foundry_prompt_agent",
    }


# ---------------------------------------------------------------------------
# Full Workflow (with local ingestion and risk scoring)
# ---------------------------------------------------------------------------

async def run_full_workflow(file_path: str, send_email: bool = False) -> Dict[str, Any]:
    """
    Run the complete grant compliance workflow using a single Prompt agent.

    Pipeline:
      1. Document Ingestion (local)
      2. Single Prompt Agent — summarization + compliance + risk flagging
      3. Risk Scoring (local)
      4. Email Notification (if needed)
    """
    from agents.document_ingestion_agent import DocumentIngestionAgent
    from agents.risk_scoring_agent import RiskScoringAgent
    from agents.email_trigger_agent import EmailTriggerAgent

    # Step 1: Document Ingestion (local — no AI needed)
    doc_agent = DocumentIngestionAgent(use_azure=True, use_managed_identity=True)
    document_data = doc_agent.process_document(file_path)
    metadata = doc_agent.extract_metadata(document_data)
    logger.info(f"Document ingested: {metadata.get('word_count', 0)} words")

    # Step 2: Single Prompt Agent — all AI work in one call
    result = await analyze_proposal(document_data["text"], metadata)
    logger.info(
        f"Analysis complete: {result['compliance_status']} "
        f"(confidence: {result['confidence_score']})"
    )

    # Step 3: Risk Scoring (local — no AI needed)
    # Adapt result to match the format expected by RiskScoringAgent
    compliance_report = {
        "compliance_score": _status_to_score(result["compliance_status"]),
        "overall_status": result["compliance_status"].lower().replace(" ", "_").replace("-", "_"),
        "analysis": result["full_analysis"],
        "confidence_score": result["confidence_score"],
        "violations": [],
        "warnings": [],
        "relevant_executive_orders": result["relevant_executive_orders"],
    }
    summary = {
        "executive_summary": result["executive_summary"],
        "key_clauses": result["key_clauses"].split("\n") if result["key_clauses"] else [],
        "key_topics": result["key_topics"].split("\n") if result["key_topics"] else [],
    }

    risk_agent = RiskScoringAgent()
    risk_report = risk_agent.calculate_risk_score(compliance_report, summary, metadata)
    logger.info(f"Risk: {risk_report['overall_score']:.1f}% ({risk_report['risk_level']})")

    # Step 4: Email Notification (if needed)
    email_sent = False
    if send_email and risk_report.get("requires_notification"):
        email_agent = EmailTriggerAgent(use_graph_api=True)
        email_data = email_agent.prepare_email(
            risk_report, compliance_report, summary, metadata
        )
        email_agent.send_email(email_data)
        email_sent = True

    return {
        "status": "completed",
        "file_path": file_path,
        "metadata": metadata,
        "analysis": result,
        "compliance_report": compliance_report,
        "risk_report": risk_report,
        "email_sent": email_sent,
        "service": "foundry_single_prompt_agent",
    }


def _status_to_score(status: str) -> float:
    """Convert compliance status string to a numeric score."""
    s = status.lower().replace("-", "_").replace(" ", "_")
    if s == "compliant":
        return 90.0
    elif s == "non_compliant":
        return 30.0
    return 60.0


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

async def main():
    """Example: analyze a sample proposal."""
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO)

    sample = """
    Grant Proposal: Equitable Affordable Housing Program
    Requesting Department: Housing and Community Development
    Requested Amount: $3,500,000
    Timeline: 24 months

    Purpose: Develop 200 units of affordable housing with focus on advancing
    racial equity and environmental justice. The project will prioritize
    historically underserved communities and include diversity, equity, and
    inclusion training for all contractors and staff.

    Compliance Requirements:
    This project addresses Executive Order 13985 on Advancing Racial Equity
    and EO 14008 on Tackling the Climate Crisis.
    """

    result = await analyze_proposal(
        proposal_text=sample,
        metadata={"word_count": len(sample.split()), "filename": "example.txt"},
    )

    print("=" * 70)
    print("SINGLE PROMPT AGENT — ANALYSIS RESULTS")
    print("=" * 70)
    print(f"\nStatus: {result['compliance_status']}")
    print(f"Confidence: {result['confidence_score']}")
    print(f"\nExecutive Summary:\n{result['executive_summary']}")
    print(f"\nKey Findings:\n{result['key_findings']}")
    print(f"\nConcerns:\n{result['concerns']}")
    print(f"\nRecommendations:\n{result['recommendations']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Comparison: Multi-Agent vs Single Agent

| Aspect | Current (Multi-Agent) | Proposed (Single Agent) |
|--------|-----------------------|-------------------------|
| **Agent Count** | 2-3 Prompt agents per run | 1 Prompt agent per run |
| **Conversations** | 2+ conversations (one per agent) | 1 conversation |
| **API Calls** | `create_version` × 2-3, `conversations.create` × 2-3, `responses.create` × 2-3 | `create_version` × 1, `conversations.create` × 1, `responses.create` × 1 |
| **Agent Type** | Prompt agents (each with `PromptAgentDefinition`) | Single Prompt agent with `PromptAgentDefinition` |
| **Latency** | Higher (sequential agent creation + invocation) | Lower (single round-trip for all AI work) |
| **Cleanup** | Delete 2-3 agents + conversations | Delete 1 agent + conversation |
| **Complexity** | Python orchestrator manages data flow | Single prompt handles all analysis |
| **Debuggability** | Separate conversations per agent | One conversation with full analysis |
| **Foundry Portal** | Multiple agents visible | Single agent visible |

## When to Use Each Approach

### Use the Single Prompt Agent when:
- You want the simplest possible implementation
- The grant compliance analysis is the primary use case
- You want to minimize API calls and latency
- You're prototyping or building an internal tool
- You want to manage the agent in the Foundry portal with no code

### Use the Multi-Agent approach when:
- Individual agent steps need to be reused independently
- You need different models for different steps (e.g., cheaper model for summarization)
- You want to parallelize agent calls in the future
- Each step's output needs separate logging or monitoring
- You plan to migrate to **Workflow agents (preview)** for visual orchestration

### Consider Workflow agents (preview) when:
- You need visual orchestration in the Foundry portal
- You want declarative YAML-based workflow definitions
- You need branching logic (if/else), human-in-the-loop approvals, or group chat patterns
- You want to orchestrate agents without writing Python orchestration code
- See: [Build a workflow in Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/workflow)

## Environment Variables

The single agent uses the same environment variables as the existing Foundry agents:

```bash
# Required
AZURE_AI_PROJECT_ENDPOINT=https://your-resource.ai.azure.com/api/projects/your-project
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4o
AI_SEARCH_PROJECT_CONNECTION_ID=your-search-connection-id

# Optional
AZURE_SEARCH_INDEX_NAME=grant-compliance-index    # default
PERSIST_FOUNDRY_AGENTS=false                       # set to true to keep agent in portal
```

## Foundry Portal Setup (No-Code Alternative)

You can also create this agent directly in the Foundry portal without any code:

1. Go to [Microsoft Foundry](https://ai.azure.com)
2. Navigate to your project → **Agents**
3. Select **Create agent**
4. Configure:
   - **Name**: `GrantComplianceAgent`
   - **Model**: `gpt-4o` (or your deployed model)
   - **Instructions**: Paste the `AGENT_INSTRUCTIONS` text above
   - **Tools**: Add Azure AI Search → select your `grant-compliance-index`
5. **Save** and test in the Agents Playground

This creates the identical Prompt agent without writing any code.

## References

- [What is Microsoft Foundry Agent Service?](https://learn.microsoft.com/en-us/azure/foundry/agents/overview)
- [Agent Types — Prompt, Workflow, Hosted](https://learn.microsoft.com/en-us/azure/foundry/agents/overview#agent-types)
- [Microsoft Foundry Quickstart (Python SDK)](https://learn.microsoft.com/en-us/azure/foundry/quickstarts/get-started-code)
- [Build a Workflow in Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/workflow)
- [azure-ai-projects SDK (PyPI)](https://pypi.org/project/azure-ai-projects/)
- [Tool Catalog](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/tool-catalog)
- [Agent Development Lifecycle](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/development-lifecycle)
