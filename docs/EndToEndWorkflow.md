# End-to-End Workflow

> How a grant proposal moves through the system — from upload to attorney review.

---

## Quick Summary

A user uploads a PDF grant proposal → the system extracts text, summarizes it, checks compliance against executive orders, scores risk, and (optionally) emails an attorney — all in one request/response cycle.

```
User Upload → Document Ingestion → Summarization → Compliance Analysis → Risk Scoring → Notification
                   (OCR)              (LLM)            (LLM + Search)       (Local calc)     (Email)
```

---

## Sequence Diagram — Full Pipeline

```mermaid
sequenceDiagram
    participant U as User (Browser)
    participant FE as React Frontend<br/>:3000
    participant BE as FastAPI Backend<br/>:8000
    participant O as Sequential Workflow<br/>Orchestrator
    participant DI as Document Ingestion<br/>Agent
    participant SA as Summarization<br/>Agent
    participant CA as Compliance<br/>Agent
    participant RS as Risk Scoring<br/>Agent
    participant EN as Email Notification<br/>Agent
    participant DocIntel as Azure Document<br/>Intelligence
    participant LLM as Azure OpenAI<br/>(GPT-4o)
    participant Search as Azure AI Search
    participant Email as Email Service<br/>(Graph/SMTP)

    U->>FE: Upload PDF + options
    FE->>BE: POST /api/process/upload<br/>(FormData: file, send_email, use_azure)
    BE->>BE: Validate file type (.pdf/.docx/.txt)
    BE->>BE: Save to temp file
    BE->>O: process_grant_proposal_async(file_path)

    Note over O: Step 1: Document Ingestion
    O->>DI: DocumentIngestionExecutor.run(file_path)
    alt Azure mode (use_azure=true)
        DI->>DocIntel: begin_analyze_document(prebuilt-layout)
        DocIntel-->>DI: text, pages, tables, key-value pairs
    else Local fallback
        DI->>DI: PyPDF2 / python-docx / open()
    end
    DI->>DI: extract_metadata(document_data)
    DI-->>O: WorkflowState {document_data, metadata}

    Note over O: Step 2: Summarization
    O->>SA: SummarizationExecutor.run(state)
    SA->>LLM: Agent prompt: "Analyze this grant proposal..."
    LLM-->>SA: Structured summary (objectives, budget, key clauses)
    SA->>SA: _parse_summary_response() → structured dict
    SA-->>O: state + {summary}

    Note over O: Step 3: Compliance Analysis
    O->>CA: ComplianceValidationExecutor.run(state)
    CA->>LLM: Agent prompt: "Legal compliance analyst..."
    LLM->>CA: Tool call: search_executive_orders(query)
    CA->>Search: Semantic search (top 5 results)
    Search-->>CA: Executive order matches + scores
    CA->>LLM: Tool results → continue analysis
    LLM-->>CA: Compliance status, citations, violations
    CA->>CA: _calculate_compliance_score()
    CA-->>O: state + {compliance_report}

    Note over O: Step 4: Risk Scoring
    O->>RS: RiskScoringExecutor.run(state)
    RS->>RS: Local calculation:<br/>Risk = Compliance(60%) + Quality(25%) + Completeness(15%)
    RS-->>O: state + {risk_report}

    Note over O: Step 5: Email Notification
    O->>EN: EmailNotificationExecutor.run(state)
    alt requires_notification=true AND send_email=true
        EN->>Email: Send risk report to attorney
        Email-->>EN: message_id
    else
        EN->>EN: Skip or simulate
    end
    EN-->>O: state + {email_sent, notification_result}

    O-->>BE: Final results dict
    BE->>BE: Cleanup temp file
    BE-->>FE: JSONResponse (200)
    FE-->>U: Render results in 5 tabs
```

---

## Data Transformation at Each Step

### Request Flow

| Step | Input | Output | Azure Service |
|------|-------|--------|---------------|
| **Frontend** | User selects file | `FormData {file, send_email, use_azure}` | — |
| **Backend** | FormData | `file_path` (temp file on disk) | — |
| **1. Ingestion** | `file_path` | `{text, page_count, word_count, metadata}` | Document Intelligence |
| **2. Summarization** | `document_data.text` + `metadata` | `{executive_summary, key_objectives, budget_highlights, key_clauses}` | Azure OpenAI |
| **3. Compliance** | `document_data.text` + `summary` | `{compliance_score, status, violations, citations, relevant_executive_orders}` | Azure OpenAI + AI Search |
| **4. Risk Scoring** | `compliance_report` + `summary` + `metadata` | `{overall_score, risk_level, risk_breakdown, recommendations}` | — (local) |
| **5. Notification** | `risk_report` + all prior state | `{email_sent, method, status}` | Graph API / SMTP |

### Response to Frontend

The final JSON response contains all accumulated state:

```json
{
  "status": "completed",
  "file_path": "proposal.pdf",
  "metadata": {
    "document_type": "grant_proposal",
    "word_count": 4500,
    "page_count": 12,
    "processing_timestamp": "2026-07-02T10:30:00Z"
  },
  "summary": {
    "executive_summary": "...",
    "key_objectives": ["..."],
    "budget_highlights": "...",
    "key_clauses": ["..."]
  },
  "compliance_report": {
    "compliance_score": 78.5,
    "overall_status": "requires_review",
    "confidence_score": 85.0,
    "violations": [{"message": "...", "executive_order": "EO 14091", "severity": "medium"}],
    "warnings": [...],
    "relevant_executive_orders": [...],
    "citations": [...]
  },
  "risk_report": {
    "overall_score": 72.0,
    "risk_level": "medium-high",
    "risk_breakdown": {
      "compliance_risk": {"score": 65, "factors": [...]},
      "quality_risk": {"score": 80, "factors": [...]},
      "completeness_risk": {"score": 85, "factors": [...]}
    },
    "recommendations": ["Address EO 14091 requirements...", "..."]
  },
  "email_sent": false,
  "overall_status": "requires_review"
}
```

---

## Scoring at a Glance

Three independent scores guide the attorney's decision:

```mermaid
graph LR
    A[Confidence Score<br/>0-100<br/>How certain is the AI?] --> D{Attorney<br/>Decision}
    B[Compliance Score<br/>0-100<br/>How compliant is<br/>the proposal?] --> D
    C[Risk Score<br/>0-100<br/>Overall risk level?] --> D
    D --> E[Approve]
    D --> F[Approve with Conditions]
    D --> G[Reject / Rework]
```

| Score | Meaning | Calculated By |
|-------|---------|---------------|
| **Confidence** (0–100) | AI's certainty about its own analysis | LLM self-assessment during compliance step |
| **Compliance** (0–100) | How well the proposal aligns with executive orders | Rule-based from compliance status + keyword analysis |
| **Risk** (0–100) | Composite assessment (higher = lower risk) | Weighted formula: Compliance 60% + Quality 25% + Completeness 15% |

See [ScoringSystem.md](ScoringSystem.md) for full details.

---

## Alternative Entry Points

### Sample Document Processing

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant BE as Backend
    participant O as Orchestrator

    U->>FE: Click "Analyze Sample"
    FE->>BE: POST /api/process/sample<br/>{sample_name, send_email, use_azure}
    BE->>BE: Load from knowledge_base/sample_proposals/
    BE->>O: process_grant_proposal_async(sample_path)
    Note over O: Same 5-step pipeline as upload
    O-->>BE: Results
    BE-->>FE: JSONResponse
    FE-->>U: Render results
```

### Azure Functions (Durable) Hosting

When deployed as Azure Functions, each step becomes a durable activity/agent with automatic state persistence:

```mermaid
sequenceDiagram
    participant C as Client
    participant F as Azure Functions
    participant DTS as Durable Task<br/>Scheduler
    participant Agents as Agent Pipeline

    C->>F: POST /api/workflows/grant-compliance
    F->>DTS: Start orchestration instance
    DTS->>Agents: Activity: ingest_document
    Agents-->>DTS: checkpoint
    DTS->>Agents: Durable Agent: SummarizationAgent
    Agents-->>DTS: checkpoint
    DTS->>Agents: Durable Agent: ComplianceAgent
    Agents-->>DTS: checkpoint
    DTS->>Agents: Activity: score_risk
    Agents-->>DTS: checkpoint
    DTS->>Agents: Activity: send_notification
    Agents-->>DTS: checkpoint
    DTS-->>F: Orchestration complete
    F-->>C: Results (or poll status endpoint)
```

Key difference: Durable Functions **checkpoint after each step**, so failures resume from the last successful step rather than restarting.

---

## Error Handling & Fallbacks

```mermaid
flowchart TD
    A[Start Pipeline] --> B{Azure Document Intelligence<br/>available?}
    B -->|Yes| C[OCR extraction]
    B -->|No| D[Local PyPDF2/docx extraction]
    C --> E{FoundryChatClient<br/>connected?}
    D --> E
    E -->|Yes| F[LLM Summarization]
    E -->|No| G[❌ 500 Error<br/>Cannot proceed without LLM]
    F --> H{Azure AI Search<br/>reachable?}
    H -->|Yes| I[Semantic search for EOs]
    H -->|No| J[Local knowledge base fallback]
    I --> K[Risk Scoring - always local]
    J --> K
    K --> L{Email configured?}
    L -->|Graph API| M[Send via Microsoft Graph]
    L -->|SMTP| N[Send via SMTP]
    L -->|Neither| O[Simulate - log only]
    M --> P[Done]
    N --> P
    O --> P
```

**Critical dependency**: Azure OpenAI (LLM) is required for summarization and compliance analysis. If it's unreachable, the pipeline fails with a 500 error — which is the error you see when `AZURE_AI_FOUNDRY_PROJECT_ENDPOINT` is misconfigured or the service is down.

---

## Frontend Result Display

The React frontend renders results across 5 tabs:

| Tab | Shows | Source Field |
|-----|-------|-------------|
| **Overview** | Status, risk level, key metrics | `overall_status`, `risk_report.risk_level` |
| **Summary** | Executive summary, objectives, budget | `summary.*` |
| **Compliance** | Status, violations, citations, EO matches | `compliance_report.*` |
| **Risk** | Score breakdown, factors, recommendations | `risk_report.*` |
| **Email** | Notification status, preview | `email_sent`, `notification_result` |

---

## Environment Variables That Control Behavior

| Variable | Effect on Pipeline |
|----------|-------------------|
| `ORCHESTRATOR_TYPE=sequential` | Uses SequentialWorkflowOrchestrator (default) |
| `AGENT_SERVICE=agent-framework` | Uses Agent Framework + FoundryChatClient |
| `AGENT_SERVICE=foundry` | Uses Azure AI Foundry Prompt agents |
| `USE_AZURE=true` | Enables Document Intelligence for OCR |
| `USE_MANAGED_IDENTITY=true` | Authenticates via Managed Identity (not API keys) |
| `AI_SEARCH_QUERY_TYPE=semantic` | Semantic reranking on search queries |
