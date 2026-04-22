# Deploying a Hosted Agent with Agent Framework via Azure Functions (Durable)

This guide covers deploying AI agents built with the [Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview/) to Azure using [Azure Functions (Durable)](https://learn.microsoft.com/en-us/agent-framework/integrations/azure-functions?tabs=bash&pivots=programming-language-python). This project includes a ready-to-deploy Azure Functions host at `src/functions/grant_compliance_host/`.

---

## Overview

Durable agents combine Agent Framework with Azure Durable Functions to create agents that:

- **Persist state** automatically across function invocations
- **Resume after failures** without losing conversation context
- **Scale automatically** based on demand (including scale-to-zero)
- **Orchestrate multi-agent workflows** with reliable execution guarantees

### When to Use Durable Agents

Choose durable agents when you need:

| Requirement | Why Durable Agents |
|---|---|
| Full code control | Deploy and manage your own compute while keeping serverless benefits |
| Complex orchestrations | Coordinate multiple agents with deterministic workflows that can run for days |
| Event-driven architecture | Integrate with Azure Functions triggers (HTTP, timers, queues) and bindings |
| Automatic conversation state | History is persisted without explicit state handling in your code |

> **Note**: This differs from Foundry Agent Service (`AGENT_SERVICE=foundry`), which provides fully managed infrastructure. Durable agents are ideal when you need code-first deployment with durable state management.

---

## Architecture

The grant compliance host (`src/functions/grant_compliance_host/`) implements:

```
AgentFunctionApp
├── Durable Agents (HTTP endpoints + orchestration participants)
│   ├── SummarizationAgent  – summarizes grant proposals
│   └── ComplianceAgent     – analyzes proposals against executive orders via AI Search
├── Activity Functions (non-LLM processing)
│   ├── ingest_document     – extracts text / metadata from files
│   ├── score_risk          – calculates risk scores from compliance results
│   └── send_notification   – prepares and optionally sends email alerts
└── Orchestration
    └── grant_compliance_workflow – sequential pipeline coordinating all five steps
```

### Auto-Created Endpoints

| Endpoint | Purpose |
|---|---|
| `POST /api/agents/SummarizationAgent/run` | Interact with the summarization agent directly |
| `POST /api/agents/ComplianceAgent/run` | Interact with the compliance agent directly |
| `POST /api/workflows/grant-compliance` | Start the full sequential compliance workflow |

---

## Prerequisites

Before you begin, ensure you have:

- [Python 3.10 or later](https://www.python.org/downloads/)
- [Azure Functions Core Tools v4.x](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local#install-the-azure-functions-core-tools)
- [Azure Developer CLI (azd)](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd)
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) installed and authenticated
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running (for local development)
- An Azure subscription with permissions to create resources

### Required Azure Resources

| Resource | Purpose |
|---|---|
| Azure OpenAI Service | LLM inference for agent responses |
| Azure AI Search | Knowledge base of executive orders |
| Azure Functions App (Flex Consumption) | Hosts the durable agents |
| Azure Storage Account | Functions runtime + durable storage |
| Durable Task Scheduler | Manages agent state and orchestrations |

---

## Getting Started

### 1. Install Dependencies

```bash
cd src/functions/grant_compliance_host
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The key packages:

```
agent-framework>=1.0.1
agent-framework-azurefunctions>=1.0.0b260409
azure-functions-durable>=1.5.0
azure-identity
```

### 2. Configure Local Settings

Copy the sample settings file and update with your Azure resource values:

```bash
cp local.settings.sample.json local.settings.json
```

Edit `local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "TASKHUB_NAME": "default",

    "AZURE_OPENAI_ENDPOINT": "https://<your-resource>.openai.azure.com",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4o",
    "AZURE_OPENAI_API_VERSION": "2024-12-01-preview",

    "AZURE_AI_FOUNDRY_PROJECT_ENDPOINT": "https://<your-resource>.services.ai.azure.com/api/projects/<project>",

    "AZURE_SEARCH_ENDPOINT": "https://<your-search>.search.windows.net",
    "AZURE_SEARCH_INDEX_NAME": "grant-compliance-index",
    "AZURE_SEARCH_API_KEY": "",
    "AI_SEARCH_QUERY_TYPE": "simple",

    "USE_AZURE": "true",
    "USE_MANAGED_IDENTITY": "true"
  }
}
```

### 3. Start Local Development Dependencies

You need two Docker containers running in separate terminals.

#### Terminal 1: Start Azurite (Azure Storage Emulator)

```bash
docker pull mcr.microsoft.com/azure-storage/azurite
docker run -p 10000:10000 -p 10001:10001 -p 10002:10002 mcr.microsoft.com/azure-storage/azurite
```

#### Terminal 2: Start the Durable Task Scheduler Emulator

```bash
docker pull mcr.microsoft.com/dts/dts-emulator:latest
docker run -p 8080:8080 -p 8082:8082 mcr.microsoft.com/dts/dts-emulator:latest
```

This exposes:
- **Port 8080**: gRPC endpoint for the Durable Task Scheduler
- **Port 8082**: Administrative dashboard at `http://localhost:8082`

### 4. Run the Function App

In a third terminal:

```bash
cd src/functions/grant_compliance_host
func start
```

You should see output listing the available endpoints:

```
Functions:
     http-SummarizationAgent: [POST] http://localhost:7071/api/agents/SummarizationAgent/run
     http-ComplianceAgent: [POST] http://localhost:7071/api/agents/ComplianceAgent/run
     start_grant_workflow: [POST] http://localhost:7071/api/workflows/grant-compliance
     dafx-SummarizationAgent: entityTrigger
     dafx-ComplianceAgent: entityTrigger
```

---

## Testing Locally

### Interact with Individual Agents

Send a message to the summarization agent:

```bash
curl -i -X POST http://localhost:7071/api/agents/SummarizationAgent/run \
  -H "Content-Type: text/plain" \
  -d "Summarize this grant proposal: The City of Springfield requests $2.5M for a community resilience program addressing climate adaptation and workforce development..."
```

The response includes the agent's reply as plain text, with a `x-ms-thread-id` header for continuing the conversation:

```
HTTP/1.1 200 OK
Content-Type: text/plain
x-ms-thread-id: @dafx-summarizationagent@abc123...

**Executive Summary**: The City of Springfield seeks $2.5M for a community resilience program...
```

#### Continue a Conversation

```bash
curl -X POST "http://localhost:7071/api/agents/SummarizationAgent/run?thread_id=@dafx-summarizationagent@abc123..." \
  -H "Content-Type: text/plain" \
  -d "What are the key compliance risks?"
```

### Run the Full Workflow

Start the complete grant compliance pipeline:

```bash
curl -X POST http://localhost:7071/api/workflows/grant-compliance \
  -H "Content-Type: application/json" \
  -d '{"file_path": "knowledge_base/sample_proposals/sample_grant_proposal.pdf", "send_email": false}'
```

This returns status-query URLs for async polling:

```json
{
  "id": "abc123def456",
  "statusQueryGetUri": "http://localhost:7071/runtime/webhooks/durabletask/instances/abc123def456",
  "sendEventPostUri": "http://localhost:7071/runtime/webhooks/durabletask/instances/abc123def456/raiseEvent/{eventName}",
  "terminatePostUri": "http://localhost:7071/runtime/webhooks/durabletask/instances/abc123def456/terminate"
}
```

Poll the status endpoint until `runtimeStatus` is `Completed`:

```bash
curl http://localhost:7071/runtime/webhooks/durabletask/instances/abc123def456
```

---

## Monitoring with the Durable Task Scheduler Dashboard

### Local Dashboard

1. Open `http://localhost:8082` in your browser
2. Select the **default** task hub
3. Select the gear icon → enable **Agent pages** under Preview Features

### Agent Session Insights

Navigate to the **Agents** tab to view:

- **Conversation history**: Complete chat history for each agent session
- **Task timing**: How long specific agent interactions take
- **Token usage**: Prompt and completion token counts

### Orchestration Insights

Navigate to the **Orchestrations** tab to view:

- **Multi-agent visualization**: Execution flow across agents
- **Sequential pipeline**: Document ingestion → Summarization → Compliance → Risk → Email
- **Timing and duration**: Per-step performance metrics
- **Execution history**: Detailed logs for each orchestration instance

---

## Deploying to Azure

### Option 1: Azure Developer CLI (Recommended)

If you used `azd` to set up the quickstart template:

```bash
# Provision Azure resources
azd provision

# Deploy the function app
azd deploy
```

This creates:
- Azure OpenAI service with a model deployment
- Azure Functions app with Flex Consumption hosting plan
- Azure Storage account for the runtime and durable storage
- Durable Task Scheduler instance (Consumption plan)
- Necessary networking and identity configurations

### Option 2: Manual Deployment with Azure CLI

#### 1. Create a Resource Group

```bash
az group create --name rg-grant-compliance --location eastus2
```

#### 2. Create Azure Storage Account

```bash
az storage account create \
  --name stgrantcompliance \
  --resource-group rg-grant-compliance \
  --location eastus2 \
  --sku Standard_LRS
```

#### 3. Create the Function App (Flex Consumption)

```bash
az functionapp create \
  --name func-grant-compliance \
  --resource-group rg-grant-compliance \
  --storage-account stgrantcompliance \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --os-type Linux \
  --plan-type FlexConsumption
```

#### 4. Create the Durable Task Scheduler

```bash
az durabletask scheduler create \
  --name dts-grant-compliance \
  --resource-group rg-grant-compliance \
  --location eastus2 \
  --sku consumption

az durabletask taskhub create \
  --scheduler-name dts-grant-compliance \
  --resource-group rg-grant-compliance \
  --name default
```

#### 5. Configure Application Settings

```bash
az functionapp config appsettings set \
  --name func-grant-compliance \
  --resource-group rg-grant-compliance \
  --settings \
    AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o" \
    AZURE_OPENAI_API_VERSION="2024-12-01-preview" \
    AZURE_SEARCH_ENDPOINT="https://<your-search>.search.windows.net" \
    AZURE_SEARCH_INDEX_NAME="grant-compliance-index" \
    USE_AZURE="true" \
    USE_MANAGED_IDENTITY="true"
```

#### 6. Enable Managed Identity and Assign Roles

```bash
# Enable system-assigned managed identity
az functionapp identity assign \
  --name func-grant-compliance \
  --resource-group rg-grant-compliance

# Grant Cognitive Services OpenAI User role for Azure OpenAI
IDENTITY_ID=$(az functionapp identity show --name func-grant-compliance --resource-group rg-grant-compliance --query principalId -o tsv)

az role assignment create \
  --assignee "$IDENTITY_ID" \
  --role "Cognitive Services OpenAI User" \
  --scope "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<openai-resource>"

# Grant Search Index Data Reader for Azure AI Search
az role assignment create \
  --assignee "$IDENTITY_ID" \
  --role "Search Index Data Reader" \
  --scope "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Search/searchServices/<search-resource>"
```

#### 7. Deploy the Code

```bash
cd src/functions/grant_compliance_host
func azure functionapp publish func-grant-compliance
```

---

## Testing the Deployed Agent

### Get the Function Key

```bash
API_KEY=$(az functionapp function keys list \
  --name func-grant-compliance \
  --resource-group rg-grant-compliance \
  --function-name http-SummarizationAgent \
  --query default -o tsv)
```

### Test an Agent

```bash
curl -i -X POST "https://func-grant-compliance.azurewebsites.net/api/agents/SummarizationAgent/run?code=$API_KEY" \
  -H "Content-Type: text/plain" \
  -d "Summarize this proposal..."
```

### Test the Full Workflow

```bash
SYSTEM_KEY=$(az functionapp keys list \
  --name func-grant-compliance \
  --resource-group rg-grant-compliance \
  --query "systemKeys.durabletask_extension" -o tsv)

curl -X POST "https://func-grant-compliance.azurewebsites.net/api/workflows/grant-compliance?code=$SYSTEM_KEY" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "knowledge_base/sample_proposals/sample_grant_proposal.pdf", "send_email": false}'
```

### Monitor the Deployed Agent

1. Get the DTS name: `az durabletask scheduler list --resource-group rg-grant-compliance`
2. Open the [Azure portal](https://portal.azure.com/) and navigate to your Durable Task Scheduler resource
3. Select the **default** task hub → **Open Dashboard**
4. View agent conversations and orchestration history

---

## Understanding the Code

### Agent Definition Pattern

The agents are defined using `FoundryChatClient` from `agent_framework.foundry`, which routes through the Foundry project for tracing and observability:

```python
from agent_framework import Agent, tool
from agent_framework.azure import AgentFunctionApp
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential

_credential = DefaultAzureCredential()

# Define a tool the agent can use
@tool(name="search_executive_orders", description="Search the knowledge base")
def search_executive_orders(query: str) -> str:
    # ... search implementation
    pass

# Create the agent with FoundryChatClient
agent = Agent(
    client=FoundryChatClient(
        project_endpoint=os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT"),
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
        credential=_credential,
    ),
    name="ComplianceAgent",
    instructions="You are a legal compliance analyst...",
    tools=[search_executive_orders],
)

# Host it in Azure Functions with durable state
app = AgentFunctionApp(
    agents=[agent],
    enable_health_check=True,
    max_poll_retries=50,
)
```

### Sequential Orchestration Pattern

The grant compliance workflow uses a durable orchestration to coordinate agents and activities:

```python
import azure.durable_functions as df

@app.orchestration_trigger(context_name="context")
def grant_compliance_workflow(context: df.DurableOrchestrationContext):
    input_data = context.get_input()

    # Step 1: Document Ingestion (activity function)
    doc = yield context.call_activity("ingest_document", input_data["file_path"])

    # Step 2: Summarization (durable agent)
    summary_agent = app.get_agent(context, "SummarizationAgent")
    summary = yield summary_agent.run(messages=f"Summarize: {doc['text']}")

    # Step 3: Compliance Analysis (durable agent with tools)
    compliance_agent = app.get_agent(context, "ComplianceAgent")
    compliance = yield compliance_agent.run(messages=f"Analyze: {doc['text']}")

    # Step 4: Risk Scoring (activity function)
    risk = yield context.call_activity("score_risk", compliance)

    return {"summary": summary, "compliance": compliance, "risk": risk}
```

### Activity Functions vs Durable Agents

| Component | Type | Use Case |
|---|---|---|
| `SummarizationAgent` | Durable Agent | LLM-powered summarization with tools |
| `ComplianceAgent` | Durable Agent | LLM-powered compliance analysis with AI Search |
| `ingest_document` | Activity Function | Deterministic document processing (no LLM) |
| `score_risk` | Activity Function | Deterministic risk calculation (no LLM) |
| `send_notification` | Activity Function | Email preparation and sending (no LLM) |

**Use durable agents** for LLM-powered tasks that benefit from conversation state and tool use.
**Use activity functions** for deterministic, non-LLM processing steps.

---

## Cost Considerations

When hosted on [Azure Functions Flex Consumption](https://learn.microsoft.com/en-us/azure/azure-functions/flex-consumption-plan):

- **Pay only for execution time** — no idle compute costs
- **Scale to zero** when no requests are active
- **Scale to thousands** of concurrent instances under load
- **Human-in-the-loop workflows** cost only seconds of compute, not hours of waiting

For the grant compliance workflow processing 50 proposals/month:
- Estimated Azure Functions cost: **< $2/month** (well within free tier)
- Primary costs are Azure OpenAI tokens and Azure AI Search (see [CostEstimation.md](CostEstimation.md))

---

## Comparison with Other Hosting Options

| Feature | Azure Functions (Durable) | Foundry Agent Service | Direct Agent Framework |
|---|---|---|---|
| Hosting | Serverless (Flex Consumption) | Fully managed | Self-hosted |
| State Management | Durable Task Scheduler | Foundry-managed | Manual |
| Scale | Auto (0 to thousands) | Managed | Manual |
| Multi-Agent Orchestration | Durable orchestrations | Manual coordination | SequentialBuilder |
| Observability | DTS Dashboard | Foundry Portal | Custom logging |
| Cost Model | Pay-per-execution | Service-based | Compute-based |
| Code Control | Full | Limited | Full |
| Portal Visibility | DTS Dashboard | Azure AI Foundry | None |

---

## Next Steps

- [Agent Framework Azure Functions Documentation](https://learn.microsoft.com/en-us/agent-framework/integrations/azure-functions?tabs=bash&pivots=programming-language-python)
- [Durable Task Scheduler Overview](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-task-scheduler/durable-task-scheduler)
- [Azure Functions Flex Consumption Plan](https://learn.microsoft.com/en-us/azure/azure-functions/flex-consumption-plan)
- [Durable Functions Patterns](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview?tabs=in-process%2Cnodejs-v3%2Cv1-model&pivots=csharp)
- [Project Architecture](Architecture.md)
- [Cost Estimation](CostEstimation.md)
