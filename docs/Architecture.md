# Architecture Documentation

## Overview

The Grant Proposal Compliance Automation system is built on a multi-agent architecture powered by the Azure AI Agent Framework. This document describes the system architecture, component interactions, and design decisions.

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Layer                                │
│  ┌──────────────────────┐         ┌──────────────────────┐        │
│  │   React Frontend     │         │  Streamlit Demo      │        │
│  │   (Production)       │         │  (Legacy)            │        │
│  └──────────┬───────────┘         └──────────┬───────────┘        │
└─────────────┼────────────────────────────────┼────────────────────┘
              │                                 │
              └─────────────┬───────────────────┘
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Application Layer                              │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │                  FastAPI Backend                          │     │
│  │  ┌────────────────────────────────────────────────────┐   │     │
│  │  │           Agent Orchestrator                       │   │     │
│  │  │  ┌──────────────────────────────────────────────┐ │   │     │
│  │  │  │  Multi-Agent Coordination Pipeline          │ │   │     │
│  │  │  │  1. Document Ingestion Agent                │ │   │     │
│  │  │  │  2. Summarization Agent                     │ │   │     │
│  │  │  │  3. Compliance Agent                        │ │   │     │
│  │  │  │  4. Risk Scoring Agent                      │ │   │     │
│  │  │  │  5. Email Trigger Agent                     │ │   │     │
│  │  │  └──────────────────────────────────────────────┘ │   │     │
│  │  └────────────────────────────────────────────────────┘   │     │
│  └───────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Azure Services Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  Azure AI    │  │  Azure       │  │  Azure       │            │
│  │  Foundry     │  │  OpenAI      │  │  AI Search   │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  Document    │  │  Key Vault   │  │  Azure       │            │
│  │  Intelligence│  │              │  │  Functions   │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Data Layer                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  SharePoint  │  │  Blob        │  │  Queue       │            │
│  │  Storage     │  │  Storage     │  │  Storage     │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Multi-Agent Architecture

### Agent Framework Design

The system uses the **Azure AI Agent Framework** to orchestrate specialized AI agents in a coordinated workflow:

```
Orchestrator Agent (Coordinator)
    ├── Document Ingestion Agent (Text Extraction)
    ├── Summarization Agent (Content Analysis)
    ├── Compliance Agent (Executive Order Validation)
    ├── Risk Scoring Agent (Risk Assessment)
    └── Email Trigger Agent (Notification Management)
```

### Agent Responsibilities

#### 1. Orchestrator Agent
**Purpose**: Coordinates the entire workflow and manages agent interactions

**Responsibilities**:
- Receives document upload requests
- Manages execution sequence of sub-agents
- Aggregates results from all agents
- Handles error recovery and retry logic
- Returns final comprehensive report

**Technology**: Python, Azure AI Agent Framework

#### 2. Document Ingestion Agent
**Purpose**: Extracts text and metadata from documents

**Responsibilities**:
- Process PDF, Word, and text files
- Perform OCR on scanned documents (via Azure Document Intelligence)
- Extract document metadata (title, date, author)
- Prepare clean text for downstream agents

**Technology**: Azure Document Intelligence, PyPDF2 (fallback)

#### 3. Summarization Agent
**Purpose**: Generates executive summaries and identifies key information

**Responsibilities**:
- Create concise executive summary
- Extract key clauses and requirements
- Identify key topics and themes
- Calculate document statistics (word count, page count)

**Technology**: Azure OpenAI GPT-4, Prompt Engineering

#### 4. Compliance Agent
**Purpose**: Validates grant proposals against executive orders

**Responsibilities**:
- Search knowledge base for relevant executive orders (Azure AI Search)
- Analyze proposal against EO requirements
- Generate structured citations with annotated regions
- Calculate confidence score
- Identify violations and warnings

**Technology**: Azure AI Search, Azure OpenAI GPT-4, Citation Framework

**Output Structure**:
```python
{
    "compliance_score": 85.0,
    "confidence_score": 90.0,
    "overall_status": "COMPLIANT",
    "violations": [],
    "warnings": [],
    "relevant_executive_orders": [...],
    "citations": [
        {
            "title": "EO 14008: Climate Crisis",
            "url": "...",
            "snippet": "...",
            "annotated_regions": [...],
            "additional_properties": {...}
        }
    ]
}
```

#### 5. Risk Scoring Agent
**Purpose**: Calculates composite risk scores for decision-making

**Responsibilities**:
- Calculate overall risk score using weighted formula
- Assess compliance risk (60% weight)
- Assess quality risk (25% weight)
- Assess completeness risk (15% weight)
- Include relevant executive orders in risk report
- Generate actionable recommendations
- Determine if attorney notification is required

**Formula**: `Risk = (Compliance × 60%) + (Quality × 25%) + (Completeness × 15%)`

**Technology**: Python, Business Logic

#### 6. Email Trigger Agent
**Purpose**: Sends attorney notifications for high-risk proposals

**Responsibilities**:
- Determine if notification is required (risk < 75%)
- Format email with all analysis results
- Send via Azure Functions or Microsoft Graph API
- Track notification status

**Technology**: Azure Functions, Microsoft Graph API

---

## Data Flow

### Document Processing Pipeline

```
1. Document Upload
   └─> FastAPI receives file upload
       └─> Store temporarily in memory/disk

2. Document Ingestion
   └─> Extract text using Azure Document Intelligence
       └─> Parse metadata
           └─> Return structured document data

3. Summarization
   └─> Generate executive summary using GPT-4
       └─> Extract key clauses and topics
           └─> Return summary data

4. Compliance Analysis
   └─> Search Azure AI Search for relevant EOs
       └─> Analyze proposal against EOs using GPT-4
           └─> Generate citations with text spans
               └─> Return compliance report

5. Risk Assessment
   └─> Calculate risk scores
       └─> Include relevant executive orders
           └─> Generate recommendations
               └─> Return risk report

6. Email Notification (Conditional)
   └─> IF risk < 75%
       └─> Format email
           └─> Send notification
               └─> Return email status

7. Final Response
   └─> Aggregate all agent results
       └─> Return comprehensive report to frontend
```

---

## Key Design Patterns

### 1. Multi-Agent Orchestration Pattern
- **Coordinator**: Orchestrator manages all sub-agents
- **Specialization**: Each agent has single responsibility
- **Sequential Execution**: Agents run in dependency order
- **Data Passing**: Results flow between agents via orchestrator

### 2. Knowledge Base Retrieval Pattern (RAG)
- **Index**: Executive orders indexed in Azure AI Search
- **Retrieve**: Semantic search finds relevant documents
- **Augment**: Search results provided as context to GPT-4
- **Generate**: LLM generates grounded compliance analysis

### 3. Human-in-the-Loop Pattern
- **AI Analysis**: Automated compliance checking
- **Human Validation**: Attorney reviews and approves
- **Feedback Loop**: Attorney decisions improve future analysis

### 4. Citation and Provenance Pattern
- **Citations**: All findings linked to source documents
- **Text Spans**: Precise character ranges for citations
- **Metadata**: Additional properties (page, section, date)
- **Traceability**: Full audit trail from finding to source

---

## Technology Stack

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type-safe JavaScript
- **TailwindCSS**: Utility-first styling
- **Vite**: Build tool and dev server

### Backend
- **FastAPI**: Python async web framework
- **Pydantic**: Data validation
- **Azure AI Agent Framework**: Multi-agent orchestration
- **Python 3.10+**: Core language

### Azure Services
- **Azure AI Foundry**: Agent deployment and management
- **Azure OpenAI**: GPT-4 LLM inference
- **Azure AI Search**: Semantic search and vector indexing
- **Azure Document Intelligence**: OCR and document processing
- **Azure Functions**: Serverless compute for notifications
- **Azure Key Vault**: Secrets management
- **Azure Monitor**: Logging and observability

### Storage
- **Azure Blob Storage**: Document storage
- **Azure Queue Storage**: Async task queue
- **SharePoint Online**: Enterprise document management (optional)

---

## Security Architecture

### Authentication & Authorization
- **Azure AD**: Identity provider
- **Managed Identity**: Service-to-service authentication
- **RBAC**: Role-based access control for resources
- **API Keys**: Secured in Azure Key Vault

### Data Security
- **Encryption at Rest**: All storage encrypted
- **Encryption in Transit**: TLS 1.2+ for all connections
- **Private Endpoints**: VNet integration for Azure services
- **Network Security Groups**: Firewall rules

### Compliance
- **Data Residency**: Configurable Azure regions
- **Audit Logging**: All operations logged
- **Data Retention**: Configurable retention policies
- **PII Protection**: Sensitive data handling

---

## Scalability & Performance

### Horizontal Scaling
- **Frontend**: CDN distribution, multiple instances
- **Backend**: Auto-scaling App Service or Kubernetes
- **Agents**: Parallel processing where possible
- **Azure Services**: Managed scaling (OpenAI, Search, Functions)

### Performance Optimization
- **Caching**: Knowledge base search results
- **Async Processing**: Non-blocking agent execution
- **Batch Processing**: Multiple documents via queue
- **Connection Pooling**: Efficient Azure SDK usage

### Performance Targets
- **Document Upload**: < 2 seconds
- **Text Extraction**: 10-60 seconds (depends on OCR)
- **Compliance Analysis**: 30-120 seconds
- **Total Workflow**: 2-5 minutes per document

---

## Monitoring & Observability

### Logging
- **Application Insights**: Application-level logging
- **Azure Monitor**: Infrastructure-level monitoring
- **Structured Logging**: JSON-formatted logs
- **Correlation IDs**: Request tracing across services

### Metrics
- **Agent Performance**: Execution time per agent
- **API Latency**: Request/response times
- **Error Rates**: Failed operations
- **Resource Utilization**: CPU, memory, tokens

### Alerting
- **Error Alerts**: High error rate triggers notification
- **Performance Alerts**: Slow response time warnings
- **Cost Alerts**: Budget threshold notifications
- **Health Checks**: Service availability monitoring

---

## Deployment Architecture

### Development
- **Local Development**: Docker Compose or direct execution
- **Environment**: `.env` file configuration
- **Hot Reload**: Vite (frontend), Uvicorn (backend)

### Staging
- **Azure App Service**: Web app hosting
- **Azure Functions**: Serverless compute
- **Managed Azure Services**: OpenAI, Search, etc.
- **Private Endpoints**: VNet integration

### Production
- **Azure Kubernetes Service (AKS)**: Container orchestration (optional)
- **Azure App Service**: Web app hosting (recommended)
- **Azure Front Door**: Global load balancing and CDN
- **Multiple Regions**: High availability
- **Disaster Recovery**: Backup region failover

---

## Future Architecture Enhancements

### Planned Improvements
1. **Distributed Caching**: Redis for performance
2. **Event-Driven Architecture**: Event Grid for decoupling
3. **Advanced Analytics**: Power BI integration
4. **Mobile Apps**: Native iOS/Android clients
5. **Webhook API**: Third-party integrations
6. **Batch Processing**: Bulk document analysis
7. **A/B Testing**: Prompt optimization framework
8. **Fine-tuned Models**: Custom model training

---

## References

- [Azure AI Foundry Architecture](https://learn.microsoft.com/azure/ai-studio/)
- [Azure Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/)
- [Multi-Agent Systems](https://learn.microsoft.com/azure/ai-services/agents/)
- [RAG Pattern](https://learn.microsoft.com/azure/search/retrieval-augmented-generation-overview)

---

**Last Updated**: November 2025  
**Version**: 1.0
