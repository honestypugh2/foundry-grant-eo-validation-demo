# Restructuring as Foundry Workflow Agents (Preview)

This document describes how to restructure the `_foundry.py` agents into a **Foundry Workflow agent** using the Foundry portal visual builder and/or YAML definition. Workflow agents (preview) are a declarative, no-code/low-code approach to multi-agent orchestration that replaces the Python-based orchestration in `SequentialWorkflowOrchestratorFoundry`.

> **Preview Notice**: Workflow agents are currently in **public preview**. Features and YAML schema may change before general availability.

---

## Table of Contents

- [Background](#background)
- [What Are Workflow Agents?](#what-are-workflow-agents)
- [Current vs Proposed Architecture](#current-vs-proposed-architecture)
- [Prerequisites](#prerequisites)
- [Step 1: Create the Prompt Agents in Foundry Portal](#step-1-create-the-prompt-agents-in-foundry-portal)
- [Step 2: Create the Workflow in Foundry Portal](#step-2-create-the-workflow-in-foundry-portal)
- [Step 3: YAML Workflow Definition](#step-3-yaml-workflow-definition)
- [Step 4: Working with YAML in VS Code](#step-4-working-with-yaml-in-vs-code)
- [Step 5: Adding Human-in-the-Loop Approval](#step-5-adding-human-in-the-loop-approval)
- [Step 6: Adding If/Else Risk Branching](#step-6-adding-ifelse-risk-branching)
- [Step 7: Converting YAML to Agent Framework Code](#step-7-converting-yaml-to-agent-framework-code)
- [Agent Definitions Reference](#agent-definitions-reference)
- [JSON Schema Definitions](#json-schema-definitions)
- [Comparison Table](#comparison-table)
- [Limitations and Considerations](#limitations-and-considerations)
- [References](#references)

---

## Background

### Current Architecture (Python-Orchestrated Prompt Agents)

The current `_foundry.py` implementation creates **multiple Prompt agents** via the `azure-ai-projects` SDK, with Python code managing the data flow:

```
Python Orchestrator (sequential_workflow_orchestrator_foundry.py)
  │
  ├── Step 1: DocumentIngestionAgent       ← Local Python (no AI)
  ├── Step 2: SummarizationAgentFoundry    ← Prompt agent (PromptAgentDefinition)
  ├── Step 3: ComplianceAgentFoundry       ← Prompt agent + Azure AI Search tool
  ├── Step 4: RiskScoringAgent             ← Local Python (no AI)
  └── Step 5: EmailTriggerAgent            ← Local Python (no AI)
```

**Problem**: The orchestration logic lives in Python, which means:
- You must write and maintain Python code to coordinate agents
- Adding/reordering steps requires code changes and redeployment
- No visual representation of the workflow
- No portal-native versioning of the orchestration itself

### Proposed Architecture (Foundry Workflow Agent)

Replace the Python orchestrator with a **Foundry Workflow agent** that coordinates the Prompt agents declaratively:

```
Foundry Workflow (Sequential pattern, portal/YAML)
  │
  ├── Node 1: Ask a question         ← "Upload your grant proposal text"
  ├── Node 2: Invoke Summarization Agent  ← Prompt agent
  │            └── Save output as: Local.SummaryResult
  ├── Node 3: Invoke Compliance Agent     ← Prompt agent + AI Search tool
  │            └── Save output as: Local.ComplianceResult
  ├── Node 4: If/Else (risk check)        ← Power Fx condition on ComplianceResult
  │   ├── High Risk → Node 5a: Send message (flag for attorney review)
  │   └── Low Risk  → Node 5b: Send message (approved summary)
  └── Node 6: Send message               ← Final consolidated report
```

---

## What Are Workflow Agents?

Per [Microsoft Foundry documentation](https://learn.microsoft.com/en-us/azure/foundry/agents/overview#workflow-agents-preview):

> **Workflow agents** orchestrate a sequence of actions or coordinate multiple agents using declarative definitions. Build workflows visually in the Foundry portal or define them in YAML through Visual Studio Code. Workflows support branching logic, human-in-the-loop steps, and sequential or group-chat patterns.

### Workflow Patterns

| Pattern | Description | Mapping to This Project |
|---------|-------------|------------------------|
| **Sequential** | Passes results from one agent to the next in order | Summarization → Compliance → Risk Decision |
| **Human in the loop** | Pauses workflow for user input or approval | Attorney review of flagged proposals |
| **Group chat** | Dynamically passes control between agents | Not needed for this use case |

### Why Workflow Agents for This Project?

- The grant compliance pipeline is inherently **sequential** — summarize, then check compliance, then assess risk
- **Human-in-the-loop** is a core requirement (attorney review)
- **Branching logic** is needed (high-risk vs low-risk routing)
- No custom orchestration code to maintain
- Full **version history** in the Foundry portal
- **Visual debugging** — see each node's execution in the portal

---

## Current vs Proposed Architecture

| Aspect | Current (`_foundry.py`) | Proposed (Workflow Agent) |
|--------|-------------------------|--------------------------|
| **Orchestration** | Python code | Declarative YAML / Visual builder |
| **Agent type** | Prompt agents created at runtime | Prompt agents pre-created in portal |
| **Workflow definition** | `sequential_workflow_orchestrator_foundry.py` (~600 lines) | YAML file (~100 lines) or visual builder |
| **Adding a step** | Edit Python, redeploy | Add node in portal, click Save |
| **Branching logic** | Python if/else | Visual if/else nodes with Power Fx |
| **Human-in-the-loop** | Not implemented | Built-in "Ask a question" node |
| **Versioning** | Git only | Portal version history + Git |
| **Debugging** | Logs + conversation inspection | Visual node-by-node execution |
| **Code required** | Yes | No (YAML optional) |
| **Local dev** | Run Python script | VS Code extension playground |
| **Preview status** | GA (`azure-ai-projects` 2.0.1) | **Preview** |

---

## Prerequisites

- An Azure AI Foundry project with a deployed model (e.g., `gpt-4o`)
- Azure AI Search index (`grant-compliance-index`) with executive orders indexed
- AI Search connection configured in the Foundry project (`AI_SEARCH_PROJECT_CONNECTION_ID`)
- **Contributor** role or higher on the Foundry project (required for workflow creation)
- (Optional) [Microsoft Foundry for VS Code extension](https://marketplace.visualstudio.com/items?itemName=TeamsDevApp.vscode-ai-foundry) for YAML editing
- (Optional) [GitHub Copilot](https://github.com/features/copilot) subscription for YAML-to-code conversion

---

## Step 1: Create the Prompt Agents in Foundry Portal

Before building the workflow, create the individual Prompt agents that the workflow will invoke.

### 1a. Create the Summarization Agent

1. Go to [Microsoft Foundry](https://ai.azure.com) → your project → **Agents**
2. Select **Create agent**
3. Configure:
   - **Name**: `SummarizationAgent`
   - **Model**: `gpt-4o` (or your deployed model)
   - **Instructions**:

```text
You are an expert grant proposal analyst specializing in document summarization.

Your responsibilities:
1. Generate concise executive summaries (3-4 sentences)
2. Identify key objectives and deliverables
3. Extract budget highlights and timeline information
4. Identify critical compliance requirements
5. Highlight specific clauses or phrases that may pose compliance risks
6. Extract key topics and themes from the proposal

Output should include:
- Executive Summary: 3-4 sentence overview
- Key Objectives: Bullet points of main goals
- Budget Highlights: Financial information
- Timeline/Deliverables: Key dates and milestones
- Key Topics: Main themes identified
- Key Clauses: Specific text that may require review
```

4. Under **Details** → **Parameters** → **Text format**, select **JSON Schema** and paste the schema from the [JSON Schema Definitions](#summarization-agent-output-schema) section below.
5. Select **Save**

### 1b. Create the Compliance Agent

1. Select **Create agent**
2. Configure:
   - **Name**: `ComplianceAgent`
   - **Model**: `gpt-4o`
   - **Instructions**:

```text
You are a legal compliance analyst specializing in grant proposal review.

You have access to an Azure AI Search tool that searches a knowledge base of executive orders.
You MUST always provide citations for answers using the tool and render them as: [message_idx:search_idx†source].

Your responsibilities:
1. Analyze grant proposals for compliance with relevant executive orders
2. Identify potential compliance issues or concerns
3. Provide detailed insights into how well the grant aligns with current legal standards
4. Highlight specific clauses or phrases that may pose compliance risks
5. Assign confidence scores to your analysis (0-100)

Output Format:
- Overall Compliance Status: [Compliant/Non-Compliant/Requires Review]
- Confidence Score: [0-100]
- Key Findings: [Bullet points with citations]
- Relevant Executive Orders: [List with citations]
- Concerns: [Any issues identified]
- Recommendations: [Actions needed]
```

3. Select **Tools** → **Add tool** → **Azure AI Search**
   - Select your search connection
   - Index: `grant-compliance-index`
   - Query type: `Simple` (or `Semantic` if configured)
4. Under **Details** → **Parameters** → **Text format**, select **JSON Schema** and paste the schema from the [JSON Schema Definitions](#compliance-agent-output-schema) section below.
5. Select **Save**

---

## Step 2: Create the Workflow in Foundry Portal

1. In the Foundry portal, select **Build** (upper-right menu)
2. Select **Create new workflow** → **Sequential**
3. Build the workflow by adding nodes:

### Node Layout

```
[Start]
   │
   ▼
[Ask a question]  ──  "Paste the grant proposal text for compliance review."
   │                   Save response as: Local.ProposalText
   ▼
[Invoke agent: SummarizationAgent]
   │  Input: Local.ProposalText
   │  Save output as: Local.SummaryResult
   ▼
[Invoke agent: ComplianceAgent]
   │  Input: Concat(Local.ProposalText, Char(10), Char(10),
   │         "SUMMARY:", Char(10), Local.SummaryResult)
   │  Save output as: Local.ComplianceResult
   ▼
[If/Else]  ──  Condition: Local.ComplianceResult contains "Non-Compliant"
   │                       OR Local.ComplianceResult contains "Requires Review"
   │
   ├── True (High Risk):
   │   [Send message]  ──  "⚠️ HIGH RISK — Attorney review required."
   │                       + Local.ComplianceResult
   │
   └── False (Compliant):
       [Send message]  ──  "✅ Proposal appears compliant."
                           + Local.SummaryResult
   │
   ▼
[Send message]  ──  Final consolidated report:
                    Concat("## Analysis Complete", Char(10),
                           "### Summary", Char(10), Local.SummaryResult, Char(10),
                           "### Compliance", Char(10), Local.ComplianceResult)
```

4. Select **Save** after every change (Foundry does not auto-save)
5. Select **Run Workflow** to test

### Detailed Node Configuration

#### Node 1: Ask a Question
- **Type**: Ask a question
- **Message**: `Please paste the full grant proposal text for compliance review.`
- **Save user response as**: `ProposalText`

#### Node 2: Invoke Summarization Agent
- **Type**: Invoke agent
- **Agent**: Select `SummarizationAgent`
- **Input message**: `{Local.ProposalText}`
- **Action settings**: Save output as `SummaryResult`

#### Node 3: Invoke Compliance Agent
- **Type**: Invoke agent
- **Agent**: Select `ComplianceAgent`
- **Input message**: Use a Power Fx expression to combine proposal + summary:
  ```
  Concat(Local.ProposalText, Char(10), Char(10), "KEY CLAUSES FROM SUMMARY:", Char(10), Local.SummaryResult)
  ```
- **Action settings**: Save output as `ComplianceResult`

#### Node 4: If/Else Risk Branch
- **Type**: If/Else
- **Condition** (Power Fx):
  ```
  "Non-Compliant" in Local.ComplianceResult || "Requires Review" in Local.ComplianceResult
  ```
- **True branch**: Send message with risk flag
- **False branch**: Send message with approval

#### Node 5: Final Report
- **Type**: Send message
- **Message**:
  ```
  {Concat("## Grant Compliance Analysis Report", Char(10), Char(10), "### Executive Summary", Char(10), Local.SummaryResult, Char(10), Char(10), "### Compliance Analysis", Char(10), Local.ComplianceResult)}
  ```

---

## Step 3: YAML Workflow Definition

Enable the **YAML Visualizer View** toggle in the Foundry portal to see and edit the YAML representation. The following is a reference YAML definition for the grant compliance sequential workflow.

> **Note**: The exact YAML schema is determined by the Foundry portal's workflow engine. The structure below follows the patterns from the [Foundry workflow documentation](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/workflow) and may need adjustment based on the portal's current schema version.

```yaml
# grant-compliance-workflow.yaml
# Foundry Workflow Agent — Sequential pattern
# Orchestrates SummarizationAgent and ComplianceAgent for grant compliance review
#
# References:
#   https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/workflow
#   https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/vs-code-agents-workflow-low-code

kind: Sequential
name: GrantComplianceWorkflow
description: >-
  Sequential workflow for grant proposal compliance review.
  Summarizes the proposal, checks compliance against executive orders,
  and routes based on risk level.

nodes:
  # ── Node 1: Collect grant proposal text from user ──────────────
  - id: ask_proposal
    kind: Question
    settings:
      question: >-
        Please paste the full grant proposal text for compliance review.
      variable: ProposalText

  # ── Node 2: Summarization ─────────────────────────────────────
  - id: summarize
    kind: InvokeAgent
    settings:
      agentName: SummarizationAgent
      inputMessage: "{Local.ProposalText}"
      outputVariable: SummaryResult

  # ── Node 3: Compliance analysis with AI Search ────────────────
  - id: compliance_check
    kind: InvokeAgent
    settings:
      agentName: ComplianceAgent
      inputMessage: >-
        Analyze this grant proposal for compliance with executive orders.

        GRANT PROPOSAL TEXT:
        {Local.ProposalText}

        KEY CLAUSES FROM SUMMARY:
        {Local.SummaryResult}

        Search the knowledge base for relevant executive orders and provide
        a detailed compliance analysis with citations.
      outputVariable: ComplianceResult

  # ── Node 4: Risk-based routing ────────────────────────────────
  - id: risk_check
    kind: Condition
    settings:
      expression: >-
        "Non-Compliant" in Local.ComplianceResult
        || "Requires Review" in Local.ComplianceResult
      trueNextNode: flag_high_risk
      falseNextNode: approve_low_risk

  # ── Node 4a: High-risk path ──────────────────────────────────
  - id: flag_high_risk
    kind: SendMessage
    settings:
      message: >-
        ⚠️ **HIGH RISK — Attorney Review Required**

        The compliance analysis identified potential issues.
        Please review the full analysis below before proceeding.

        {Local.ComplianceResult}
      nextNode: final_report

  # ── Node 4b: Low-risk path ───────────────────────────────────
  - id: approve_low_risk
    kind: SendMessage
    settings:
      message: >-
        ✅ **Proposal Appears Compliant**

        No critical compliance issues were identified.
        Summary and full analysis are provided below.
      nextNode: final_report

  # ── Node 5: Final consolidated report ─────────────────────────
  - id: final_report
    kind: SendMessage
    settings:
      message: >-
        ## Grant Compliance Analysis Report

        ### Executive Summary
        {Local.SummaryResult}

        ### Compliance Analysis
        {Local.ComplianceResult}

        ---
        *Analysis generated by GrantComplianceWorkflow*
        *Service: Foundry Workflow Agent (preview)*
```

### YAML with Human-in-the-Loop Approval

To add an attorney approval step before the final report on high-risk proposals:

```yaml
  # Insert after flag_high_risk, before final_report:

  # ── Node 4c: Attorney approval gate ──────────────────────────
  - id: attorney_approval
    kind: Question
    settings:
      question: >-
        An attorney must review this proposal before it can proceed.

        Do you approve this proposal? (yes/no/needs-revision)
      variable: AttorneyDecision

  - id: approval_check
    kind: Condition
    settings:
      expression: Lower(Local.AttorneyDecision) = "yes"
      trueNextNode: final_report
      falseNextNode: rejection_message

  - id: rejection_message
    kind: SendMessage
    settings:
      message: >-
        ❌ **Proposal Not Approved**

        Attorney decision: {Local.AttorneyDecision}

        The proposal requires revision before resubmission.
```

---

## Step 4: Working with YAML in VS Code

The [Microsoft Foundry for VS Code extension](https://marketplace.visualstudio.com/items?itemName=TeamsDevApp.vscode-ai-foundry) lets you edit workflow YAML locally and deploy to Foundry.

### View and Edit

1. In the Foundry portal, open your workflow
2. Select the **YAML** button on the right-hand side
3. Select **Open in VS Code for Web** — opens a split view with YAML on the left and visual graph on the right
4. Edit the YAML; changes are reflected in the visualizer immediately
5. Select **Deploy** from the `...` menu to save changes back to Foundry

### Test Locally

1. In VS Code, open the **Microsoft Foundry** extension panel
2. Under **My Resources**, select your Foundry project
3. Select **Declarative Agents** → select the workflow version to test
4. The **Remote Agent Playground** opens — type a message to start the workflow
5. Verify each node completes and outputs match expectations

### File Organization

Store the YAML in the project repository for version control:

```
foundry-grant-eo-validation-demo/
├── workflows/
│   ├── grant-compliance-workflow.yaml          # Base sequential workflow
│   ├── grant-compliance-workflow-hitl.yaml     # With human-in-the-loop
│   └── README.md                               # Workflow documentation
├── src/agents/
│   ├── compliance_agent_foundry.py             # SDK fallback (existing)
│   ├── summarization_agent_foundry.py          # SDK fallback (existing)
│   └── sequential_workflow_orchestrator_foundry.py  # SDK fallback (existing)
```

---

## Step 5: Adding Human-in-the-Loop Approval

The current Python implementation has no built-in human approval step. Workflow agents make this trivial:

1. In the Foundry portal workflow visualizer, select the **+** icon after the compliance node
2. Select **Ask a question**
3. Enter: `An attorney must review this proposal. Approve, reject, or request revision?`
4. Save the response as `AttorneyDecision`
5. Add an **If/Else** node with condition: `Lower(Local.AttorneyDecision) = "yes"`
6. Route accordingly

This is a key advantage of Workflow agents — human-in-the-loop is a first-class feature rather than requiring custom code.

---

## Step 6: Adding If/Else Risk Branching

The Python orchestrator uses `RiskScoringAgent` to calculate numeric risk scores. In the workflow agent, use Power Fx conditions:

### Simple Status Check
```
"Non-Compliant" in Local.ComplianceResult
```

### Confidence Score Check (if using JSON schema output)
```
Value(Local.ComplianceOutput.confidence_score) < 60
```

### Combined Risk Assessment
```
"Non-Compliant" in Local.ComplianceResult
|| Value(Local.ComplianceOutput.confidence_score) < 60
|| "Requires Review" in Local.ComplianceResult
```

> **Tip**: Use JSON schema output format on the Compliance Agent to get structured data, making Power Fx conditions more reliable than parsing free text.

---

## Step 7: Converting YAML to Agent Framework Code

If you need to move from the declarative workflow back to code (for advanced customization), use the VS Code extension's built-in conversion:

1. Open the workflow YAML file in VS Code
2. Select the **Generate Code** button in the upper right
3. Select **Python** (or C#)
4. GitHub Copilot generates Agent Framework code based on the YAML
5. Review, modify, and run locally with the visual debugger
6. Right-click → **Deploy to Foundry** to publish as a Hosted agent

This gives you a migration path: **YAML workflow** → **Agent Framework code** → **Hosted agent** if you outgrow the declarative model.

---

## Agent Definitions Reference

### Summarization Agent

| Property | Value |
|----------|-------|
| **Name** | `SummarizationAgent` |
| **Type** | Prompt agent |
| **Model** | `gpt-4o` |
| **Tools** | None |
| **Output format** | JSON Schema (see below) |

### Compliance Agent

| Property | Value |
|----------|-------|
| **Name** | `ComplianceAgent` |
| **Type** | Prompt agent |
| **Model** | `gpt-4o` |
| **Tools** | Azure AI Search (`grant-compliance-index`, Simple query) |
| **Output format** | JSON Schema (see below) |

---

## JSON Schema Definitions

### Summarization Agent Output Schema

Configure on the Summarization Agent under **Details** → **Parameters** → **Text format** → **JSON Schema**:

```json
{
  "name": "summarization_response",
  "schema": {
    "type": "object",
    "properties": {
      "executive_summary": {
        "type": "string",
        "description": "3-4 sentence overview of the grant proposal"
      },
      "key_objectives": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Main goals and deliverables"
      },
      "budget_highlights": {
        "type": "string",
        "description": "Financial information mentioned in the proposal"
      },
      "timeline": {
        "type": "string",
        "description": "Key dates and milestones"
      },
      "key_topics": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Main themes identified (compliance, equity, climate, etc.)"
      },
      "key_clauses": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Specific verbatim phrases that may pose compliance risks"
      }
    },
    "required": [
      "executive_summary",
      "key_objectives",
      "key_topics",
      "key_clauses"
    ],
    "additionalProperties": false
  },
  "strict": true
}
```

### Compliance Agent Output Schema

Configure on the Compliance Agent under **Details** → **Parameters** → **Text format** → **JSON Schema**:

```json
{
  "name": "compliance_response",
  "schema": {
    "type": "object",
    "properties": {
      "compliance_status": {
        "type": "string",
        "enum": ["Compliant", "Non-Compliant", "Requires Review"],
        "description": "Overall compliance determination"
      },
      "confidence_score": {
        "type": "number",
        "description": "AI certainty about the analysis (0-100)"
      },
      "key_findings": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Key findings with citations to executive orders"
      },
      "relevant_executive_orders": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "eo_number": { "type": "string" },
            "title": { "type": "string" },
            "relevance": { "type": "string" }
          },
          "required": ["eo_number", "title"],
          "additionalProperties": false
        },
        "description": "List of applicable executive orders"
      },
      "concerns": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Compliance issues or risks identified"
      },
      "recommendations": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Actions needed to address issues"
      }
    },
    "required": [
      "compliance_status",
      "confidence_score",
      "key_findings",
      "relevant_executive_orders",
      "concerns",
      "recommendations"
    ],
    "additionalProperties": false
  },
  "strict": true
}
```

---

## Comparison Table

| Approach | Agent Type | Code | Orchestration | Human-in-the-Loop | Status |
|----------|-----------|------|--------------|-------------------|--------|
| `_foundry.py` (current) | Prompt agents | Python | Python code | Not built-in | GA |
| Single Prompt Agent ([PromptAgentRestructuring.md](PromptAgentRestructuring.md)) | Single Prompt agent | Python | Single prompt | Not built-in | GA |
| **Workflow Agent (this doc)** | Workflow agent (preview) | **None / YAML** | **Declarative** | **Built-in** | **Preview** |
| Hosted Agent | Hosted agent (preview) | Python/C# container | Custom code | Custom | Preview |

---

## Limitations and Considerations

### Preview Limitations
- Workflow agents are in **public preview** — the YAML schema and portal UI may change
- Some features (e.g., advanced Power Fx functions) may have limited availability
- Private networking is available for workflow agents, but verify your region supports it

### What Moves to the Workflow vs What Stays in Code
| Component | Workflow Agent | Stays in Code |
|-----------|---------------|---------------|
| Summarization | ✅ Invoke Agent node | — |
| Compliance check | ✅ Invoke Agent node | — |
| Risk branching | ✅ If/Else node with Power Fx | — |
| Human approval | ✅ Ask a Question node | — |
| Document ingestion (OCR) | ❌ | Python pre-processing |
| Risk score calculation | ❌ (simple) / ✅ (via conditions) | Complex scoring stays in Python |
| Email notification | ❌ | Azure Functions / Logic Apps |
| File upload handling | ❌ | Backend API |

### Recommended Hybrid Approach
Use the Workflow agent for the **AI orchestration** (summarization → compliance → branching → approval), and keep the **non-AI steps** in code:

1. **Backend API** receives file upload, runs document ingestion (OCR), extracts text
2. **Backend API** invokes the Foundry Workflow agent with the extracted text
3. **Workflow agent** runs summarization → compliance → risk routing → attorney approval
4. **Backend API** receives the workflow result, calculates detailed risk score, sends email

This separates concerns: the Workflow handles AI reasoning and human approval; code handles I/O and computation.

---

## References

- [What is Microsoft Foundry Agent Service?](https://learn.microsoft.com/en-us/azure/foundry/agents/overview)
- [Agent Types — Prompt, Workflow, Hosted](https://learn.microsoft.com/en-us/azure/foundry/agents/overview#agent-types)
- [Build a Workflow in Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/workflow)
- [Declarative Agent Workflows in VS Code](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/vs-code-agents-workflow-low-code)
- [Hosted (Pro-code) Agent Workflows in VS Code](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/vs-code-agents-workflow-pro-code)
- [Microsoft Agent Framework Workflow Orchestrations](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/orchestrations/overview)
- [Power Fx Overview](https://learn.microsoft.com/en-us/power-platform/power-fx/overview)
- [Tool Catalog](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/tool-catalog)
- [RBAC in Foundry](https://learn.microsoft.com/en-us/azure/foundry/concepts/rbac-foundry)
