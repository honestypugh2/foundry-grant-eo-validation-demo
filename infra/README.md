# Infrastructure Deployment Guide

This directory contains Infrastructure as Code (IaC) templates for deploying the Grant EO Validation Demo using **Bicep**, managed by **Azure Developer CLI (azd)**.

> **📝 Note**: These templates have been updated based on the actual deployed resources from the original demo (`main_fromorigdemo.bicep`). Key updates include:
> - RAI (Responsible AI) content filtering policies (Microsoft.Default and Microsoft.DefaultV2)
> - Enhanced storage account configuration with RAGRS replication and retention policies
> - GlobalStandard SKU for OpenAI deployment with 110K TPM capacity
> - Improved network security settings and managed identity support

## 📁 Directory Structure

```
infra/
├── bicep/                      # Bicep templates
│   ├── main.bicep             # Main resource definitions
│   └── abbreviations.json     # Resource naming abbreviations
├── main.bicep                 # Subscription-level Bicep entry point
├── main.parameters.json       # Bicep parameters (uses azd variables)
└── README.md                  # This file
```

## 🏗️ Deployed Resources

> **📝 Note**: This infrastructure has been updated to use the **new Microsoft Foundry (2025-04-01-preview API)**. Projects are deployed via IaC templates with the required `allowProjectManagement: true` property.

The Bicep templates deploy the following Azure resources:

### Core Azure Services

| Service | Purpose | SKU/Configuration |
|---------|---------|------------------|
| **Azure AI Foundry Resource** | AI Foundry resource with project management enabled | S0, AIServices kind, allowProjectManagement: true |
| **Azure AI Foundry Project** | Project for organizing AI work, agents, and files | System-assigned managed identity, deployed via IaC |
| **Azure OpenAI Deployment** | GPT-4o language model deployment | GlobalStandard SKU, 110K TPM, with RAI policies |
| **Azure Document Intelligence** | Document processing and OCR extraction | S0, Form recognition + layout analysis |
| **Azure AI Search** | Hybrid search (text + vector) with semantic reranking | Basic tier, integrated vectorizer (`text-embedding-3-small`), HNSW vector index |
| **Azure Blob Storage** | Document storage and management | Standard RAGRS with 7-day retention |
| **Azure Key Vault (not used for Demo)** | Secrets management | Standard, RBAC-enabled (commented out) |
| **Azure Monitor** | Logging and monitoring | Log Analytics + Application Insights |
| **Azure Function Apps (optional)** | Serverless hosting via Agent Framework `AgentFunctionApp` | Consumption (Y1), Python 3.11 (commented out in IaC; see `src/functions/`) |
| **App Service Plan (not used for Demo)** | Web application hosting | B1 (Basic) - Linux (commented out) |
| **Backend App Service** | FastAPI REST API | Python 3.12 runtime (commented out) |
| **Frontend App Service** | React/Vite web UI | Node.js 20 LTS runtime (commented out) |

### Security Features

| Feature | Configuration |
|---------|---------------|
| **RAI Content Filtering** | Microsoft.DefaultV2 policy with Hate, Sexual, Violence, Selfharm, Jailbreak, and Protected Material filters |
| **Storage Security** | Shared access key disabled, public network access enabled (for demo), TLS 1.2 minimum |
| **Network Security** | Azure Services bypass enabled, default action: Allow |
| **Data Protection** | 7-day soft delete retention for blobs and containers |

### AI & ML Services

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **Azure OpenAI Service** | Large language models for compliance analysis | GPT-4o (2024-08-06), 110K TPM, GlobalStandard SKU |
| **Microsoft Agent Framework v1.0.1** | Agent orchestration and workflow management | `SequentialBuilder`, `@tool`, `Agent`, `FoundryChatClient` |
| **Agent Framework Azure Functions** | Durable hosting of agents as serverless functions | `AgentFunctionApp`, activity triggers, orchestration triggers |

### Managed Identities & RBAC

All services use **System-Assigned Managed Identities** with proper role assignments:

**User Principal (for development):**
- User Principal → Azure AI User
- User Principal → Azure AI Developer
- User Principal → Cognitive Services OpenAI User
- User Principal → Search Index Data Contributor
- User Principal → Search Service Contributor
- User Principal → Storage Blob Data Contributor

**Search Service MI (for integrated vectorizer):**
- Search Service MI → Cognitive Services OpenAI User on AI Services resource

**Foundry Project MI (for AzureAISearchTool in agents):**
- Foundry Project MI → Search Index Data Reader on Search Service
- Foundry Project MI → Search Index Data Contributor on Search Service
- Foundry Project MI → Search Service Contributor on Search Service

**AI Services Account MI (for account-level search access):**
- Account MI → Search Index Data Reader on Search Service
- Account MI → Search Index Data Contributor on Search Service

> **Important**: The Search Service MI → Cognitive Services OpenAI User role is required for the integrated vectorizer to generate embeddings. Without it, vector search returns 401.

---

## 🚀 Deployment Options

### Option 1: Azure Developer CLI (azd) - Recommended ✅

The Azure Developer CLI provides the simplest deployment experience with automatic environment management.

#### Prerequisites
```bash
# Install Azure Developer CLI
curl -fsSL https://aka.ms/install-azd.sh | bash

# Or on Windows
winget install microsoft.azd

# Login to Azure
azd auth login
```

#### Deploy with Bicep (Default)
```bash
# One-command deployment - prompts for all parameters interactively
azd up

# You'll be prompted for:
# - Environment name (e.g., dev, staging, prod, demo, test)
# - Azure region (default: eastus)
# - Resource naming prefix (default: grant-eo)
# - User principal ID (auto-detected if left empty)

# Or set parameters non-interactively before deployment
azd env set AZURE_ENV_NAME demo
azd env set AZURE_LOCATION eastus
azd env set AZURE_RESOURCE_PREFIX grant-eo
azd up

# Or provision only (no app deployment)
azd provision
```

**Environment Name Suggestions:**
- `dev` - Development environment
- `staging` - Pre-production testing
- `prod` - Production environment
- `demo` - Demonstration/proof-of-concept
- `test` - Testing environment
- `personal-<name>` - Personal development (e.g., `personal-john`)

**Note:** The deployment automatically detects your Azure user principal ID for RBAC role assignments. No need to run `azd init` - just `azd up`!

**The project is automatically created via IaC** - no portal setup required!

#### Useful azd Commands
```bash
# Deploy application code only (after infrastructure exists)
azd deploy

# View environment variables
azd env get-values

# Monitor deployed applications
azd monitor

# Tear down all resources
azd down

# Tear down all resources and purge (complete cleanup)
azd down --purge --force
```

---

### Option 2: Bicep (Azure CLI)

#### Prerequisites
```bash
# Azure CLI must be installed
az --version

# Login to Azure
az login

# Set subscription
az account set --subscription <subscription-id>
```

#### Deploy
```bash
cd infra

# Get your user principal ID for role assignments
PRINCIPAL_ID=$(az ad signed-in-user show --query id -o tsv)

# Deploy to subscription scope
az deployment sub create \
  --location eastus \
  --template-file main.bicep \
  --parameters environmentName=dev \
  --parameters location=eastus \
  --parameters resourcePrefix=grant-eo \
  --parameters principalId=$PRINCIPAL_ID
```

#### View Outputs
```bash
az deployment sub show \
  --name main \
  --query properties.outputs
```

---

## 🔧 Post-Deployment Configuration

After deploying infrastructure, complete these steps:

### 1. Configure Environment Variables

**If using azd:**
```bash
# Environment variables are automatically set
azd env get-values > .env
```

**If using Bicep:**
```bash
# Manually create .env from deployment outputs
az deployment sub show --name main --query properties.outputs
```

### 2. Index Knowledge Base

Upload executive order PDFs to Azure AI Search (documents are chunked automatically):

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Index documents (splits into ~2000-char chunks with 200-char overlap)
python scripts/index_knowledge_base.py \
  --input knowledge_base/executive_orders/
```

> **Note**: The index uses an integrated vectorizer (`openai-vectorizer` with `text-embedding-3-small`) that automatically generates embeddings for each chunk. Ensure the Search Service MI has the "Cognitive Services OpenAI User" role on the AI Services resource before indexing.

### 3. Deploy Application Code

**If using azd:**
```bash
# Deploy both backend and frontend
azd deploy
```

**If using Azure CLI (manual):**
```bash
# Deploy backend
cd backend
zip -r backend.zip .
az webapp deployment source config-zip \
  --resource-group <rg-name> \
  --name <backend-app-name> \
  --src backend.zip

# Deploy frontend
cd frontend
npm run build
cd dist
zip -r frontend.zip .
az webapp deployment source config-zip \
  --resource-group <rg-name> \
  --name <frontend-app-name> \
  --src frontend.zip
```

### 4. Verify Deployment

```bash
# Test backend API
curl https://<backend-url>/health

# Open frontend in browser
azd show

# Or manually
echo "Frontend: https://<frontend-app-name>.azurewebsites.net"
```

---

## 🔄 Update Infrastructure

### Using azd
```bash
# Update infrastructure only
azd provision

# Update application code only
azd deploy
```

### Using Bicep
```bash
cd infra

# Modify bicep/*.bicep files
az deployment sub create \
  --location eastus \
  --template-file main.bicep \
  --parameters @main.parameters.json
```

---

## 🧹 Clean Up Resources

### Using azd (Recommended)
```bash
# Delete all resources
azd down

# Delete resources but keep azd environment
azd down --no-purge
```

### Using Azure CLI
```bash
# Delete resource group (deletes all resources)
az group delete --name rg-grant-eo-dev --yes
```

---

## 📊 Cost Estimation

**Monthly cost estimate (Basic SKUs):**
- Azure AI Foundry (S0): ~$250/month
- Azure OpenAI (30 TPM): ~$90/month (usage-based)
- Document Intelligence (S0): ~$50/month (usage-based)
- Azure AI Search (Basic): ~$75/month
- Storage Account (LRS): ~$5/month
- App Service Plan (B1): ~$13/month

**Total: ~$483/month** (excluding OpenAI token usage)

💡 **Cost Optimization Tips:**
- Use Free tier for Azure AI Search during development
- Scale down App Service to F1 (Free) for testing
- Delete resources when not in use with `azd down`

---

## 🔐 Security Considerations

This deployment uses **Managed Identities** and **RBAC** for secure access:

✅ **Implemented:**
- System-assigned managed identities for all services
- RBAC role assignments (no access keys stored)
- HTTPS-only communication
- TLS 1.2 minimum
- No public blob access

⚠️ **For Production:**
- Enable Private Endpoints for all services
- Use Azure Virtual Network (VNet) integration
- Enable Azure Defender for Cloud
- Implement Azure Policy for governance
- Enable diagnostic logging to Log Analytics
- Configure Azure Key Vault for additional secrets
- Set up Azure Front Door with WAF

See [Production Readiness Checklist](../README.md#%EF%B8%8F-important-demonstration-purposes-only) in main README.

---

## 📚 Additional Resources

- [Azure Developer CLI Documentation](https://learn.microsoft.com/azure/developer/azure-developer-cli/)
- [Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [Azure Architecture Center](https://learn.microsoft.com/azure/architecture/)

---

## ❓ Troubleshooting

### Issue: azd provision fails with "subscription not found"
```bash
# Set subscription explicitly
azd env set AZURE_SUBSCRIPTION_ID <subscription-id>
azd provision
```

### Issue: Role assignment failed
```bash
# Ensure you have Owner or User Access Administrator role
az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv) --all
```

### Issue: OpenAI deployment quota exceeded
- Check quota limits: `az cognitiveservices account list-skus`
- Request quota increase in Azure Portal
- Use different region with available quota

---

**For more help, see [Deployment.md](../docs/Deployment.md) or open an issue in the repository.**
