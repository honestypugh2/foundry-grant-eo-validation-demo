# Grant Proposal Compliance Automation with Azure AI Foundry

> **Automating grant proposal review for executive order compliance using Azure AI Foundry, reducing manual review time while maintaining legal oversight.**

![React App - Upload & Analyze](images/reactapp_uploadanalyze.png)

## ⚠️ Preview Features & SDK Versions

This project uses **Azure AI Foundry Portal (preview)** and several **beta/preview SDK packages**. These features are under active development and may change before general availability.

### Preview SDKs Used
| Package | Version | Status |
|---------|---------|--------|
| `agent-framework` | 1.0.0b260114 | Beta |
| `azure-ai-projects` | 2.0.0b3 | Beta |
| `azure-ai-agents` | 1.2.0b5 | Beta |
| `azure-search-documents` | 11.7.0b2 | Beta |
| `azure-ai-inference` | 1.0.0b9 | Beta |
| `openai` | 2.15.0 | Stable |

### Installation Notes
```bash
# Preview packages require the --pre flag
pip install agent-framework-azure-ai --pre
pip install azure-ai-projects --pre

# Or install all from requirements.txt
pip install -r requirements.txt --pre
```

### Key Preview Features
- **Azure AI Foundry Portal**: View and debug agents created with `azure-ai-projects` SDK
- **Agent Framework**: Sequential workflow orchestration with event streaming
- **Foundry Agent Service**: Server-side agent persistence and thread management

> **Note**: Preview features may not be suitable for production workloads. Monitor the [Azure AI Foundry documentation](https://learn.microsoft.com/azure/ai-foundry/) for updates and breaking changes.

More images can be found at [images directory](images/).

> **📌 Note**: To use the Streamlit app, navigate to the project root directory before running `streamlit run app/streamlit_app_new.py`.

---

## ⚠️ IMPORTANT: DEMONSTRATION PURPOSES ONLY

**This repository is a demonstration/proof-of-concept and is NOT intended for production workloads.**

Before deploying to production, you must address:

### 🔐 Security Requirements
- Implement proper authentication and authorization (Azure AD, RBAC)
- Enable encryption at rest and in transit for all data
- Secure all secrets using Azure Key Vault (no hardcoded credentials)
- Implement network security with Private Endpoints and VNets
- Enable Azure AD Managed Identity for service-to-service authentication
- Conduct security review and penetration testing

### 🏗️ Architecture & Governance
- Follow [Azure Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/) principles
- Implement proper resource tagging and naming conventions
- Set up Azure Policy for governance and compliance
- Configure disaster recovery and business continuity plans
- Implement proper logging, monitoring, and alerting (Azure Monitor, Application Insights)

### 💰 Cost Management
- Right-size all resources based on actual workload requirements
- Implement Azure Cost Management and budgets
- Use Reserved Instances or Savings Plans where applicable
- Set up cost alerts and regular cost reviews
- Consider Azure Advisor recommendations for cost optimization

### 🛡️ Reliability & Performance
- Implement high availability with multiple regions/zones
- Set up automated backups and test restore procedures
- Configure auto-scaling for variable workloads
- Perform load testing and capacity planning
- Implement proper error handling and retry logic

### 📋 Compliance & Legal
- Ensure compliance with data residency requirements
- Implement data retention and deletion policies
- Obtain legal review for AI-generated content use
- Establish human-in-the-loop validation workflows
- Document data processing activities (GDPR, privacy laws)

**Recommended Next Steps:**
1. Review [Azure Landing Zones](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/landing-zone/) and [Aure AI Landing Zones](https://github.com/Azure/AI-Landing-Zones) for enterprise deployment
2. Implement [Azure Security Baseline](https://learn.microsoft.com/security/benchmark/azure/)
3. Follow [AI Responsible AI Standard](https://www.microsoft.com/ai/responsible-ai)
4. Engage Azure Architecture Center for [reference architectures](https://learn.microsoft.com/azure/architecture/)

---

## Table of Contents
- [Overview](#overview)
- [Use Case](#use-case)
- [Solution Architecture](#solution-architecture)
- [Key Features](#key-features)
- [Products Used](#products-used)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Demo Application](#demo-application)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [Resources](#resources)

## Overview

This solution accelerator demonstrates how to automate the review of grant proposals for compliance with executive orders using Azure AI services. The system reduces manual attorney workload while ensuring legal accuracy through human-in-the-loop validation.

**Problem**: County departments manually email grant proposals to legal offices for compliance review against executive orders—a time-consuming process prone to delays.

**Solution**: An AI-powered document analysis system that automatically extracts, indexes, and analyzes grant proposals against a knowledge base of executive orders, providing attorneys with structured compliance summaries for validation.

## Use Case

### Customer Scenario
Currently, county departments submit grant proposals and related documents via email to the legal office. Attorneys must manually review each document for compliance with relevant executive orders before responding to clients. This manual process is:
- **Time-intensive**: Each proposal requires careful analysis
- **Resource-heavy**: Attorneys spend significant time on repetitive compliance checks
- **Delay-prone**: Manual processes create bottlenecks

### Target Users
- **Legal Departments**: County/municipal legal offices handling grant proposal reviews
- **Government Agencies**: Departments submitting grant proposals requiring compliance validation
- **Attorneys**: Legal professionals providing compliance oversight and final validation

## Solution Architecture

![Grant Proposal Compliance Automation Architecture](images/architecture_diagram.png)

## Key Features

### 🤖 **AI-Powered Document Analysis**
- Automated OCR and content extraction using Azure Document Intelligence
- Semantic search against executive order knowledge base
- Structured compliance summaries with confidence scores

### 📚 **Knowledge Base Integration**
- Curated repository of executive orders and grant compliance rules
- Local and cloud-based document access for demo flexibility
- Semantic indexing with Azure AI Search for accurate retrieval
- **Optional SharePoint integration** for enterprise document management

### 🔔 **Intelligent Notification System**
- Azure Function Apps trigger attorney notifications
- Email includes document links, AI analysis, and confidence scores
- Prioritization based on complexity and confidence levels

### 👨‍⚖️ **Human-in-the-Loop Validation**
- All AI-generated analyses require attorney review
- Structured format facilitates quick validation
- Attorneys can approve, modify, or reject AI recommendations

### 📊 **Continuous Improvement**
- Prompt engineering tracked in Azure AI Foundry
- Output evaluation and iterative refinement
- Feedback loop for improved accuracy over time

## Orchestrators

This project includes **four orchestrator implementations** to coordinate the compliance validation workflow:

### 1. **Original Orchestrator** ([agents/orchestrator.py](agents/orchestrator.py))
- **Pattern**: Manual async coordination
- **Structure**: Single class with async methods
- **Best For**: Simple, straightforward workflows
- **SDK Support**: Agent Framework only (`AGENT_SERVICE=agent-framework`)
- **Usage**: Production-ready, battle-tested implementation

### 2. **Sequential Workflow Orchestrator** ([agents/sequential_workflow_orchestrator.py](agents/sequential_workflow_orchestrator.py))
- **Pattern**: Agent Framework Sequential Workflow
- **Structure**: Separate Executor classes for each step
- **Best For**: Complex, observable, extensible workflows
- **Key Benefits**:
  - 🎯 Clear separation of concerns (one executor = one responsibility)
  - 🔧 Flexible pipeline configuration via edge connections
  - 👀 Real-time event streaming for monitoring
  - 🚨 Better error handling with executor-level events
  - ♻️ Reusable components across workflows
  - 📈 Scalable architecture for easy extension

### 3. **Foundry Orchestrator** ([agents/sequential_workflow_orchestrator_foundry.py](agents/sequential_workflow_orchestrator_foundry.py)) ✨ NEW
- **Pattern**: Azure AI Projects SDK (`azure-ai-projects`)
- **Structure**: Agents created in Azure AI Foundry
- **Best For**: Foundry portal integration, debugging agents
- **Key Benefits**:
  - 👁️ Agents visible in Azure AI Foundry portal
  - 🔍 Inspect conversation threads for debugging
  - ⚙️ Optional agent persistence (`PERSIST_FOUNDRY_AGENTS=true`)
  - 🔗 Azure AI Search tool integration

### 4. **Standalone Foundry Agents**
- [agents/compliance_agent_foundry.py](agents/compliance_agent_foundry.py)
- [agents/summarization_agent_foundry.py](agents/summarization_agent_foundry.py)

**Selecting an Orchestrator**:
```bash
# Use Agent Framework SDK (default)
export AGENT_SERVICE=agent-framework

# Use Azure AI Foundry Agent Service
export AGENT_SERVICE=foundry
```

**Quick Comparison**:
```python
# Original Orchestrator
from agents.orchestrator import AgentOrchestrator
orchestrator = AgentOrchestrator(use_azure=True)
results = orchestrator.process_grant_proposal("proposal.pdf")

# Sequential Workflow Orchestrator
from agents.sequential_workflow_orchestrator import SequentialWorkflowOrchestrator
orchestrator = SequentialWorkflowOrchestrator(use_azure=True)
results = orchestrator.process_grant_proposal("proposal.pdf")

# Foundry Orchestrator
from agents.sequential_workflow_orchestrator_foundry import SequentialWorkflowOrchestratorFoundry
orchestrator = SequentialWorkflowOrchestratorFoundry(use_azure=True)
results = await orchestrator.process_grant_proposal_async("proposal.pdf")
```

📖 **See [docs/SequentialWorkflowOrchestrator.md](docs/SequentialWorkflowOrchestrator.md) for detailed documentation and comparison.**

## Scoring System

The system uses three complementary scores to evaluate grant proposals and guide decision-making:

### 1. **Confidence Score** (0-100)
- **Purpose**: Measures how certain the AI is about its compliance analysis
- **Source**: Generated by ComplianceAgent during executive order analysis
- **Interpretation**:
  - **90-100** (Very High): AI is very certain—proceed with standard review
  - **70-89** (High): Generally reliable—may need minor clarification
  - **50-69** (Moderate): Significant uncertainty—prioritize manual review
  - **<50** (Low): Unreliable—require immediate expert review
- **Decision Impact**: Low confidence (<60%) increases risk score and triggers priority attorney review

### 2. **Compliance Score** (0-100)
- **Purpose**: Measures alignment with executive order requirements
- **Source**: Calculated from ComplianceAgent's status and analysis findings
- **Calculation**: Based on compliance status (compliant/requires_review/non_compliant) with adjustments for positive/negative indicators found in the analysis text
- **Interpretation**:
  - **90-100** (Excellent): Fully compliant with all applicable executive orders
  - **70-89** (Good): Generally compliant with minor clarifications needed
  - **50-69** (Fair): Partial compliance with concerns requiring attention
  - **<50** (Poor): Significant compliance issues identified
- **Decision Impact**: Primary factor in risk calculation (60% weight)

### 3. **Risk Score** (0-100)
- **Purpose**: Composite score measuring overall proposal risk
- **Source**: Calculated by RiskScoringAgent using weighted formula
- **Calculation**: `Risk = (Compliance × 60%) + (Quality × 25%) + (Completeness × 15%)`
- **Interpretation**:
  - **90-100** (Low Risk): Approve
  - **75-89** (Medium Risk): Recommend approval with minor revisions
  - **60-74** (Medium-High Risk): Approve with major revisions required
  - **<60** (High Risk): Recommend rejection or major rework
- **Decision Impact**: Final determination for approval workflow

### Why This Scoring Approach?

**Three-Dimensional Assessment**: Separating confidence (AI certainty), compliance (regulatory alignment), and risk (overall assessment) provides clarity at each decision point.

**Conservative Bias**: The 60% weighting on compliance ensures legal/regulatory concerns are prioritized—appropriate for government context where compliance failures have serious consequences.

**Actionable Thresholds**: Clear score ranges (90, 75, 60) map directly to approval actions, making decisions straightforward for attorneys and submitters.

**For complete scoring documentation**, see [docs/ScoringSystem.md](docs/ScoringSystem.md).

## Products Used

### Core Azure Services

| Service | Purpose | Key Features |
|---------|---------|--------------|
| **Azure AI Foundry** | AI orchestration and agent management | Prompt flow design, agent orchestration, evaluation tracking |
| **Azure Document Intelligence** | Document processing and extraction | OCR, form recognition, layout analysis, content extraction |
| **Azure AI Search** | Semantic search and retrieval | Vector search, semantic ranking, knowledge base indexing |
| **Azure Blob Storage** | Document storage and management | Scalable storage, file organization, integration with processing services |
| **Azure Function Apps (not deployed in this demo)** | Serverless notifications and workflows | Email triggers, event-driven processing, scalable execution |
| **SharePoint (not used in this demo)** | Document storage and management | Centralized document repository, access control |
| **Azure Key Vault (not deployed in this demo)** | Secrets management | Secure credential storage, managed identity integration |
| **Azure Monitor** | Logging and monitoring | Application insights, performance tracking |

### Optional Azure Services

| Service | Purpose | Use Case |
|---------|---------|----------|
| **Azure Container Registry** | Container image management | Store and manage Docker container images for deployment |
| **Azure App Service** | Web application hosting | Host Streamlit or FastAPI applications in production |
| **Azure Queue Storage** | Asynchronous message queue | Queue document processing jobs, decouple workflows |
| **SharePoint Online** | Document management (optional) | Store and access grant proposals and executive orders in SharePoint |

### AI & ML Services

- **Azure OpenAI Service**: Large language models for compliance analysis
- **Microsoft Agent Framework**: Agent orchestration and workflow management
- **Semantic Kernel**: AI plugin ecosystem and function calling

### Development Tools

- **React 19.2.3**: Modern UI framework (CVE-2025-55182 patched)
- **Streamlit**: Interactive demo application with async processing
- **FastAPI**: High-performance async Python web framework
- **Python 3.10+**: Primary development language
- **TypeScript 5.7.3**: Type-safe JavaScript development
- **Microsoft Agent Framework**: Agent development SDK

## Agent Customization

Each agent in the `/agents` folder is fully customizable to adapt to your specific compliance requirements:

### What You Can Customize

**Prompts & Instructions**
- System prompts that define agent behavior and tone
- Task-specific instructions for analysis depth
- Example: Modify `compliance_agent.py` to emphasize specific regulatory frameworks

**Text Processing**
- Preprocessing pipelines (cleaning, normalization, formatting)
- Token truncation limits for context management
- Example: Adjust `max_tokens=4000` in `summarization_agent.py` for longer/shorter summaries

**Integration Points**
- Custom ML models for specialized classification
- Third-party APIs for domain-specific analysis
- Azure Cognitive Services for enhanced capabilities
- Example: Add sentiment analysis to `risk_scoring_agent.py` using Azure Text Analytics

**Scoring & Logic**
- Risk calculation formulas and weights
- Confidence thresholds and escalation rules
- Example: Modify compliance weight from 60% to 70% in `risk_scoring_agent.py`

### Customization Examples

```python
# agents/compliance_agent.py - Custom prompt
system_prompt = """
You are a legal compliance expert specializing in environmental regulations.
Focus on: Clean Air Act, Clean Water Act, and state-specific environmental orders.
Provide citations to specific CFR sections when applicable.
"""

# agents/summarization_agent.py - Text truncation
max_input_tokens = 8000  # Increase for longer documents
max_output_tokens = 1000  # Adjust summary length

# agents/risk_scoring_agent.py - Custom ML integration
from azure.ai.textanalytics import TextAnalyticsClient
sentiment_score = text_analytics_client.analyze_sentiment(document_text)
risk_factors.append({"factor": "negative_sentiment", "weight": 0.1})
```

### Critical: Document Ingestion & Summarization Customization

⚠️ **The Document Ingestion and Summarization agents are foundational to the entire workflow.** These agents determine what information is extracted from PDFs and how it's structured—directly impacting downstream compliance analysis, risk scoring, and citation accuracy.

**Why Customization Matters:**
- **Complex PDF Variability**: Grant proposals vary widely in structure, formatting, and content organization
- **Downstream Dependencies**: Compliance and risk agents rely on the quality and completeness of extracted information
- **Garbage In, Garbage Out**: Poor document extraction leads to missed compliance requirements, inaccurate citations, and unreliable risk scores

**What You Should Review & Customize:**

**Document Structure Extraction**
- Which sections are critical? (Budget, Timeline, Scope, Objectives, Compliance Statements)
- How are sections identified? (Headers, page breaks, table of contents)
- Example: Configure `document_ingestion_agent.py` to prioritize "Compliance Plan" and "Budget Narrative" sections

**Content Processing Requirements**
- Do you need tables extracted? (Budget tables, staffing plans, performance metrics)
- Are images/charts important? (Project diagrams, site maps, organizational charts)
- Should form fields be preserved? (Standard grant application forms)
- Example: Enable table extraction in Azure Document Intelligence: `features=["tables", "keyValuePairs"]`

**Text Extraction Strategies**
- OCR quality settings for scanned documents (DPI, language detection)
- Layout preservation vs. pure text extraction
- Handling multi-column formats, footnotes, headers/footers
- Example: Adjust `read_order="natural"` in Document Intelligence for logical reading flow

**Summarization Focus**
- Which content should summaries emphasize? (Compliance statements, budget, deliverables)
- What level of detail? (High-level overview vs. section-by-section breakdown)
- Should original citations be preserved in summaries?
- Example: Modify `summarization_agent.py` prompt to highlight compliance-related text:
  ```python
  summary_prompt = """
  Summarize this grant proposal with emphasis on:
  1. Explicit compliance statements and executive order references
  2. Budget allocation and timeline commitments
  3. Measurable outcomes and performance metrics
  Preserve exact phrases related to legal/regulatory compliance.
  """
  ```

**Impact on Downstream Workflow:**
- **Compliance Agent**: Relies on extracted compliance statements and section structure
- **Risk Scoring Agent**: Uses budget data, timeline information, and completeness metrics
- **Citation Display**: Depends on accurate section identification and text mapping
- **Email Notifications**: Includes summary content and key extracted information

**Recommended Approach:**
1. **Analyze Sample Documents**: Review 5-10 representative grant proposals to identify patterns
2. **Define Extraction Requirements**: Document which sections, tables, and content types are essential
3. **Configure Document Intelligence**: Adjust OCR and extraction settings based on document types
4. **Test Extraction Quality**: Validate that critical information is captured accurately
5. **Iterate Summarization**: Refine prompts to produce summaries that support downstream analysis
6. **Measure Impact**: Evaluate how extraction changes affect compliance accuracy and risk scores

### Best Practices

- **Version Control**: Track prompt changes in git for A/B testing
- **Evaluation**: Use Azure AI Foundry evaluation tools to measure impact
- **Documentation**: Comment custom logic thoroughly for team collaboration
- **Testing**: Test agents individually before orchestrator integration

For detailed agent architecture, see [docs/Architecture.md](docs/Architecture.md).

## Prerequisites

### Azure Resources

#### Required Resources
- Azure subscription with appropriate permissions
- **Azure AI Foundry resource** (AIServices account with project management enabled)
- **Azure AI Foundry project** (child project under the Foundry resource)
- Azure AI Search service
- Azure Document Intelligence resource
- Azure Blob Storage (for document storage and processing)

#### Optional Resources
- Azure Function App (for production deployment - optional)
- SharePoint Online (optional - for enterprise document management)
- Azure Container Registry (for containerized deployments)
- Azure App Service (for hosting web applications)
- Azure Queue Storage (for asynchronous processing workflows)

### Development Environment
- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer (recommended)
- Azure CLI installed and configured
- Visual Studio Code (recommended)
- Git

> **💻 Development Note**: This project was developed and tested in a **WSL2 Ubuntu environment**. While it should work on native Linux, macOS, and Windows (with appropriate shell adjustments), WSL2 Ubuntu is the validated development environment.

### Knowledge & Skills
- Basic understanding of Azure services
- Python programming
- Document processing concepts
- AI/ML fundamentals (helpful but not required)

## Getting Started

> **⚠️ Infrastructure Required**: For full functionality with Azure AI services, you must deploy infrastructure first. See [Manual Setup with Azure Infrastructure](#manual-setup-with-azure-infrastructure) below. The Quick Start option uses **demo mode with local sample data only**.

### Quick Start (Demo Mode Only)

Get the demo application running with sample data in 3 steps. This mode uses local knowledge base files and does **not** require Azure infrastructure.

#### 1. Clone the Repository

```bash
git clone https://github.com/your-org/foundry-grant-eo-validation-demo.git
cd foundry-grant-eo-validation-demo
```

#### 2. Configure Environment

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Update `.env` for demo mode (minimal configuration):

```env
# Demo Mode - Uses local sample data
DEMO_MODE=true
KNOWLEDGE_BASE_SOURCE=local

# Azure AI Foundry (still required for LLM calls)
AZURE_AI_FOUNDRY_PROJECT_ENDPOINT=your_foundry_project_endpoint_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_KEY=your_api_key_here

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_INDEX_NAME=grant-compliance-index
AZURE_SEARCH_API_KEY=your_search_api_key_here

# Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-region.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your_doc_intel_key_here

# Authentication Method
# USE_MANAGED_IDENTITY depends on AGENT_SERVICE selection:
#   - AGENT_SERVICE=agent-framework → USE_MANAGED_IDENTITY=true (recommended)
#   - AGENT_SERVICE=foundry → USE_MANAGED_IDENTITY=false (required for local dev)
USE_MANAGED_IDENTITY=true

# Agent Service Selection
# "agent-framework" - Agent Framework SDK (default, supports Managed Identity)
# "foundry" - Azure AI Foundry Agent Service (requires API keys for local dev)
AGENT_SERVICE=agent-framework

# Foundry Agent Persistence (only when AGENT_SERVICE=foundry)
# Set to "true" to keep agents visible in Foundry portal after runs
PERSIST_FOUNDRY_AGENTS=false

# Demo Configuration
DEMO_MODE=true

# Knowledge Base Configuration
# Set to "azure" to use Azure AI Search, "local" to use local file system
KNOWLEDGE_BASE_SOURCE=local
KNOWLEDGE_BASE_PATH=./knowledge_base
KNOWLEDGE_BASE_EXECUTIVE_ORDERS_PATH=./knowledge_base/sample_executive_orders
SAMPLE_PROPOSALS_PATH=./knowledge_base/sample_proposals
```

#### 3. Start the Application

**Linux/Mac:**
```bash
# One command starts everything
./start.sh
```

This will:
- ✅ Check prerequisites (Python, Node.js, npm)
- ✅ Install all dependencies automatically (uv sync, npm install)
- ✅ Start FastAPI backend on port 8000
- ✅ Start React frontend on port 3000
- ✅ Open browser automatically at http://localhost:3000

**To stop services:**
```bash
./stop.sh    # Linux/Mac
```

---

### Manual Setup with Azure Infrastructure

For full functionality with Azure AI Search, Document Intelligence, and Foundry Agent Service, follow these steps to deploy infrastructure first.

#### 1. Clone the Repository

```bash
git clone https://github.com/your-org/foundry-grant-eo-validation-demo.git
cd foundry-grant-eo-validation-demo
```

#### 2. Install Dependencies

```bash
# Install dependencies using uv (recommended)
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Alternative: Use pip
# python -m venv .venv
# source .venv/bin/activate
# pip install -r requirements.txt --pre
```

> **Note**: `uv` automatically creates a virtual environment and installs all dependencies from `pyproject.toml`.

#### 3. Deploy Azure Infrastructure

Before configuring environment variables, deploy the required Azure resources:

```bash
# Using Azure Developer CLI (recommended)
azd up

# Or deploy infrastructure only
azd provision
```

This deploys:
- ✅ Azure AI Foundry with GPT-4
- ✅ Azure Document Intelligence
- ✅ Azure AI Search
- ✅ Azure Storage Account

📖 **See [docs/Deployment.md](docs/Deployment.md) for detailed deployment instructions and options.**

#### 4. Configure Environment

After infrastructure is deployed, create and configure your `.env` file:

```bash
cp .env.example .env
```

Update `.env` with your deployed Azure resource credentials (values from `azd` output or Azure Portal):

```env
# Production Mode - Uses Azure services
DEMO_MODE=false
KNOWLEDGE_BASE_SOURCE=azure

# Azure AI Foundry
AZURE_AI_FOUNDRY_PROJECT_ENDPOINT=https://your-deployed-foundry.services.ai.azure.com/api/projects/your-project
AZURE_OPENAI_ENDPOINT=https://your-deployed-foundry.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# Azure AI Search (from deployed resources)
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_INDEX_NAME=grant-compliance-index
AZURE_SEARCH_API_KEY=your_search_api_key

# Azure Document Intelligence (from deployed resources)
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-doc-intel.cognitiveservices.azure.com/

# Authentication - depends on AGENT_SERVICE
# Agent Framework: USE_MANAGED_IDENTITY=true (recommended)
# Foundry Agent Service: USE_MANAGED_IDENTITY=false (required for local dev)
USE_MANAGED_IDENTITY=true
AGENT_SERVICE=agent-framework
```

#### 5. Start Backend and Frontend

```bash
./start.sh # Recommended
```

```bash
# Terminal 1 - Start Backend
cd backend
python main.py
# Backend runs at http://localhost:8000

# Terminal 2 - Start Frontend
cd frontend
npm install
npm run dev
# Frontend runs at http://localhost:3000
```

**Alternative: Run Streamlit Demo (Legacy)**
```bash
# Activate virtual environment first
source .venv/bin/activate
streamlit run app/streamlit_app_new.py
# Opens at http://localhost:8501
```

---

### 4. Add Your PDF Documents

#### Uploading PDFs to Azure AI Search Knowledge Base

For production use with semantic search capabilities:

**Quick Steps**:
1. Place PDF executive orders in `knowledge_base/executive_orders/`
2. Configure Azure credentials in `.env` file
3. Run the indexing script:
   ```bash
   python scripts/index_knowledge_base.py --input knowledge_base/executive_orders
   ```

**📤 [Complete Upload Instructions](docs/uploadPdfsToAzureSearch.md)** - Detailed step-by-step guide  
**⚡ [Quick Upload Reference](docs/pdfQuickReference.md)** - 3-step quick reference card

#### Adding Knowledge Base Documents (Executive Orders)

Place your PDF executive orders in the knowledge base directory:

```bash
# Copy your executive order PDFs
cp /path/to/your/executive_order.pdf knowledge_base/executive_orders/
cp /path/to/your/executive_order.pdf knowledge_base/sample_executive_orders/

# Example structure:
# knowledge_base/executive_orders/
#   ├── EO_14008_Climate_Crisis.pdf
#   ├── EO_14028_Cybersecurity.pdf
#   ├── EO_13985_Racial_Equity.pdf
#   └── your_executive_order.pdf
```

#### Adding Grant Proposals for Review

Place PDF grant proposals that need validation:

```bash
# Copy grant proposal PDFs to sample proposals directory
cp /path/to/your/grant_proposal.pdf knowledge_base/sample_proposals/

# Example structure:
# knowledge_base/sample_proposals/
#   ├── affordable_housing_grant.pdf
#   ├── education_program_grant.pdf
#   └── your_grant_proposal.pdf
```

**Note**: In the demo mode, you can also upload PDFs directly through the Application interface. For production deployment with Azure Document Intelligence, PDFs will be automatically processed for OCR and text extraction.

#### PDF Document Processing

For production use with Azure services:

1. **Index Knowledge Base PDFs** (Executive Orders)
   ```bash
   # Activate virtual environment
   source .venv/bin/activate
   
   # Run indexing script to process PDFs and upload to Azure AI Search
   python scripts/index_knowledge_base.py --input knowledge_base/sample_executive_orders/
   ```

2. **Process Grant Proposal PDFs** (Documents for Review)
   - Upload through the web interface (React or Streamlit)
   - Place in SharePoint document library (production setup)
   - Submit via email (triggers Azure Function App in production)

The Azure Document Intelligence service will automatically:
- Perform OCR on scanned documents
- Extract text with layout preservation
- Identify form fields and tables
- Extract metadata (dates, document types, etc.)

### 5. Using the Application

The application is now running! Access it at:
- **React Frontend**: http://localhost:3000 (recommended)
- **FastAPI Backend**: http://localhost:8000/docs (API documentation)
- **Streamlit Demo**: http://localhost:8501 (if running legacy demo)

**Note**: If you used `./start.sh`, the React app may have opened automatically in your browser.

## Demo Application

The application provides both a modern React frontend and a legacy Streamlit interface:

### React Frontend (Recommended)
Modern, production-ready interface with:
- **Document Upload**: Drag-and-drop for grant proposals (PDF, Word, text)
- **Real-time Processing**: Watch multi-agent analysis in action
- **Compliance Dashboard**: Visual compliance status with detailed citations
- **Knowledge Base**: Browse and download executive orders
- **Risk Analysis**: Comprehensive risk scoring with recommendations

### Streamlit Demo (Legacy)
Original demo interface available for reference:
```bash
# Activate virtual environment
source .venv/bin/activate

# Run Streamlit demo
streamlit run app/streamlit_app_new.py
```

The Streamlit app will open at `http://localhost:8501`.

### Working with PDF Documents

#### Upload PDF Grant Proposals
1. Navigate to "📝 Document Upload" page
2. Use the file uploader to select your PDF
3. In demo mode: Text preview will be shown (full OCR requires Azure Document Intelligence)
4. Click "🚀 Analyze for Compliance" to process

#### PDF Knowledge Base Documents
- PDF executive orders in `knowledge_base/executive_orders/` are used for compliance checking
- In production mode, these are indexed in Azure AI Search with full text extraction
- Demo mode uses pre-extracted text versions for immediate testing

#### Production PDF Processing
When connected to Azure Document Intelligence:
- **Automatic OCR**: Scanned documents are converted to searchable text
- **Layout Analysis**: Document structure (headings, sections, tables) is preserved
- **Form Recognition**: Key-value pairs and form fields are extracted
- **Metadata Extraction**: Document properties (dates, authors, types) are identified

**File Size Limits**:
- Demo upload: Up to 10MB per file
- Azure Document Intelligence: Up to 500MB per file
- Batch processing: Multiple documents can be queued

**Supported PDF Types**:
- ✅ Text-based PDFs (native digital documents)
- ✅ Scanned PDFs (OCR automatically applied)
- ✅ Mixed content PDFs (text + images)
- ✅ Form-based PDFs (AcroForms, fillable PDFs)

## Deployment

### Local Development
Follow the [Getting Started](#getting-started) steps above.

### Azure Deployment

Deploy the complete infrastructure and application using Azure Developer CLI (azd):

```bash
# One-command deployment
azd up

# Or step-by-step
azd init           # Initialize environment
azd provision      # Deploy infrastructure
azd deploy         # Deploy applications
```

This deploys:
- ✅ Azure AI Foundry with GPT-4 (can be changed before deployment or after)
- ✅ Azure Document Intelligence
- ✅ Azure AI Search
- ✅ Azure Storage Account
- ✅ Backend API (FastAPI)
- ✅ Frontend (React/Vite)

**Alternative deployment methods:**
- **Bicep**: `az deployment sub create --template-file infra/main.bicep`
- **Terraform**: `cd infra/terraform && terraform apply`

**Detailed deployment instructions:**
- 📖 [Infrastructure Deployment Guide](infra/README.md) - Complete azd/Bicep/Terraform guide
- 📖 [Deployment Documentation](docs/Deployment.md) - Additional deployment scenarios

## Project Structure

```
foundry-grant-eo-validation-demo/
├── frontend/                      # React + TypeScript UI (Primary)
│   ├── src/
│   │   ├── pages/                 # React pages (About, Upload, Results, Knowledge Base)
│   │   └── components/            # Reusable UI components
│   └── package.json               # Frontend dependencies
├── backend/
│   ├── main.py                    # FastAPI REST API
│   ├── requirements.txt           # Backend dependencies
│   └── test_server.py             # Backend test utilities
├── app/
│   ├── streamlit_app.py           # Streamlit demo interface
│   ├── components/                # Streamlit UI components
│   ├── pages/                     # Streamlit multi-page sections
│   ├── assets/                    # Static assets (images, CSS)
│   └── utils/                     # Helper functions
├── agents/                        # AI Agents & Orchestrators
│   ├── __init__.py
│   ├── orchestrator.py            # Original orchestrator (Agent Framework only)
│   ├── sequential_workflow_orchestrator.py      # ✅ Agent Framework Sequential Workflow
│   ├── sequential_workflow_orchestrator_foundry.py # ✅ Foundry Orchestrator (azure-ai-projects)
│   ├── compliance_agent.py        # ✅ Agent Framework - Compliance checking
│   ├── compliance_agent_foundry.py # ✅ Foundry Agent - Compliance checking
│   ├── summarization_agent.py     # ✅ Agent Framework - Summary generation
│   ├── summarization_agent_foundry.py # ✅ Foundry Agent - Summary generation
│   ├── document_ingestion_agent.py # Document processing (traditional class)
│   ├── risk_scoring_agent.py      # Risk assessment (traditional class)
│   ├── email_trigger_agent.py     # Email notification (traditional class)
│   └── config/                    # Agent configurations
├── examples/
│   └── document_ingestion_with_managed_identity.py # Managed Identity example
├── knowledge_base/
│   ├── executive_orders/          # 📄 Executive order text files
│   ├── sample_executive_orders/   # 📄 Sample executive order PDFs
│   ├── grant_guidelines/          # Grant compliance rules
│   └── sample_proposals/          # 📄 Grant proposal PDFs for review
├── functions/
│   ├── document_processor/        # Azure Function for document ingestion
│   ├── email_notifier/            # Azure Function for email notifications
│   └── sharepoint_webhook_handler/ # Azure Function for SharePoint webhooks
├── infra/                         # Infrastructure as Code
│   ├── main.bicep                 # Primary Bicep template
│   ├── main.parameters.json       # Deployment parameters
│   ├── bicep/                     # Modular Bicep templates
│   └── terraform/                 # Terraform alternative
├── config/
│   └── search_index.json          # Azure AI Search index definition
├── docs/
│   ├── Architecture.md            # Detailed architecture documentation
│   ├── ComplianceWorkflowDiagram.md # Visual workflow diagram
│   ├── CostEstimation.md          # Azure cost analysis
│   ├── Deployment.md              # Deployment guide
│   ├── DeploymentChecklist.md     # Pre-deployment checklist
│   ├── EvaluationMethodology.md   # AI evaluation approach
│   ├── ManagedIdentitySetup.md    # Managed Identity configuration
│   ├── pdfGuide.md                # Working with PDF documents
│   ├── pdfQuickReference.md       # PDF command reference
│   ├── QuickDeploy.md             # Quick deployment guide
│   ├── ScoringSystem.md           # Confidence/compliance/risk scores
│   ├── SequentialWorkflowOrchestrator.md # Orchestrator documentation
│   ├── sharepointIntegration.md   # SharePoint integration guide
│   ├── sharepointQuickstart.md    # SharePoint quick start
│   ├── uploadPdfsToAzureSearch.md # PDF indexing guide
│   └── UserGuide.md               # End-user documentation
├── tests/
│   ├── run_all_agent_tests.py     # Test runner for all agents
│   ├── test_azure_search.py       # Azure AI Search tests
│   ├── test_compliance_agent.py   # Compliance agent tests
│   ├── test_compliance_agent_citations.py # Citation tests
│   ├── test_document_ingestion_agent.py # Document processing tests
│   ├── test_email_notification.py # Email notification tests
│   ├── test_graph_api_email.py    # Microsoft Graph email tests
│   ├── test_orchestrator.py       # Orchestrator tests
│   ├── test_orchestrator_quick.py # Quick orchestrator tests
│   ├── test_risk_scoring_agent.py # Risk scoring tests
│   ├── test_smtp_email.py         # SMTP email tests
│   ├── test_summarization_agent.py # Summarization tests
│   ├── test_upload.py             # Upload functionality tests
│   └── test_workflow_dataflow.py  # End-to-end workflow tests
├── scripts/
│   ├── index_knowledge_base.py    # Index PDFs to Azure AI Search
│   ├── verify_azure_search.py     # Verify search index health
│   ├── generate_architecture_diagram.py # Generate architecture diagram
│   ├── sharepoint_integration.py  # SharePoint document access
│   ├── setup_sharepoint_webhooks.py # Configure SharePoint webhooks
│   └── deploy_webhook_function.sh # Deploy Azure Function webhooks
├── data/
│   ├── uploads/                   # Uploaded grant proposals
│   └── docs_need_review/          # Documents queued for review
├── workflows/                     # Workflow definitions (future use)
├── logs/                          # Application logs
├── images/                        # Screenshots and diagrams
├── .env.example                   # Environment variables template
├── azure.yaml                     # Azure Developer CLI configuration
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Project configuration (uv/pip)
├── uv.lock                        # uv dependency lock file
├── start.sh                       # Start frontend & backend (Linux/Mac)
├── stop.sh                        # Stop services (Linux/Mac)
├── contributing.md                # Contribution guidelines
├── CHANGELOG.md                   # Version history
├── LICENSE                        # MIT License
└── README.md                      # This file
```

### Document Organization

**Knowledge Base PDFs** (`knowledge_base/executive_orders/` or `knowledge_base/sample_executive_orders/`):
- Place all executive order PDFs here
- These documents form the compliance reference library
- Indexed in Azure AI Search for semantic retrieval
- Used by AI agents to validate grant proposals

**Grant Proposal PDFs** (`knowledge_base/sample_proposals/`):
- Place grant proposals that need compliance review
- Can be uploaded through Streamlit UI or placed directly
- Processed by Azure Document Intelligence for text extraction
- Analyzed against knowledge base for compliance

**Best Practices for PDF Organization**:
- Use descriptive filenames (e.g., `EO_14008_Climate_Action.pdf`)
- Include document metadata in filename when possible
- Keep original PDFs in their native format
- Store text-extracted versions separately for faster demo mode

## Contributing

This project welcomes contributions and suggestions. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

For recent changes and version history, see [CHANGELOG.md](CHANGELOG.md).

## Resources

### Documentation
- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [Azure Document Intelligence](https://learn.microsoft.com/azure/ai-services/document-intelligence/)
- [Azure AI Search](https://learn.microsoft.com/azure/search/)
- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)

### Project Guides
- [📝 CHANGELOG](CHANGELOG.md) - **Version history and recent updates**
- [⚡ Quick Deploy to Azure](docs/QuickDeploy.md) - **Deploy to Azure in under 10 minutes**
- [⚛️ React App Quick Start](docs/ReactQuickstart.md) - **Get the React frontend running in 60 seconds**
- [🏗️ System Architecture](docs/Architecture.md) - **Comprehensive architecture documentation**
- [🚀 Deployment Guide](docs/Deployment.md) - **Azure deployment instructions**
- [📖 User Guide](docs/UserGuide.md) - **End-user documentation and workflows**
- [📤 Upload PDFs to Azure AI Search](docs/uploadPdfsToAzureSearch.md) - Step-by-step guide for indexing PDF documents
- [📄 PDF Document Guide](docs/pdfGuide.md) - Working with PDF executive orders and proposals
- [⚡ PDF Quick Reference](docs/pdfQuickReference.md) - One-page PDF command reference
- [📁 SharePoint Integration (Optional)](docs/sharepointIntegration.md) - Access documents from SharePoint
- [⚡ SharePoint Quick Start](docs/sharepointQuickstart.md) - Quick SharePoint setup guide
- [🔄 Compliance Workflow](docs/ComplianceWorkflowDiagram.md) - Visual workflow diagram
- [📊 Scoring System](docs/ScoringSystem.md) - Understanding confidence, compliance, and risk scores

### Related Solution Accelerators
- [Document Knowledge Mining Solution Accelerator](https://github.com/microsoft/Document-Knowledge-Mining-Solution-Accelerator)
- [Azure AI Search OpenAI Demo](https://github.com/Azure-Samples/azure-search-openai-demo)

### Support
For questions or issues, please open an issue in this repository or contact the development team.

---

**License**: MIT  
**Maintainer**: Your Organization  
**Last Updated**: December 2025
