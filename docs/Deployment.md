# Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Grant Proposal Compliance Automation system to Azure. It covers both development/staging and production deployments.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Azure Resource Provisioning](#azure-resource-provisioning)
- [Application Deployment](#application-deployment)
- [Post-Deployment Configuration](#post-deployment-configuration)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

1. **Azure CLI** (v2.50.0+)
   ```bash
   # Install Azure CLI
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   
   # Login to Azure
   az login
   
   # Set subscription
   az account set --subscription "your-subscription-id"
   ```

2. **Azure Functions Core Tools** (v4.x)
   ```bash
   npm install -g azure-functions-core-tools@4 --unsafe-perm true
   ```

3. **Node.js & npm** (v18.x or higher)
   ```bash
   node --version
   npm --version
   ```

4. **Python** (3.10 or higher)
   ```bash
   python --version
   pip --version
   ```

5. **Git**
   ```bash
   git --version
   ```

### Azure Permissions

Required Azure RBAC roles:
- **Contributor**: To create and manage resources
- **User Access Administrator**: To assign managed identities
- **Cognitive Services Contributor**: To deploy AI services

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/foundry-grant-eo-validation-demo.git
cd foundry-grant-eo-validation-demo
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
pip install agent-framework-azure-ai --pre

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Azure credentials
nano .env
```

### 4. Run Locally

```bash
# Start backend and frontend
./start.sh

# Or manually:
# Terminal 1 - Backend
cd backend && python main.py

# Terminal 2 - Frontend
cd frontend && npm run dev
```

---

## Azure Resource Provisioning

### Option 1: Using Bicep Templates (Recommended)

```bash
# Set variables
RESOURCE_GROUP="rg-grant-compliance-prod"
LOCATION="eastus"
DEPLOYMENT_NAME="grant-compliance-$(date +%Y%m%d-%H%M%S)"

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Deploy infrastructure
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file deployment/main.bicep \
  --parameters deployment/parameters.json \
  --name $DEPLOYMENT_NAME
```

### Option 2: Manual Resource Creation

#### 1. Azure AI Foundry Project

```bash
# Create AI Foundry workspace
az ml workspace create \
  --name "aiw-grant-compliance" \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Create AI Foundry project
az ml project create \
  --name "grant-compliance-project" \
  --workspace-name "aiw-grant-compliance" \
  --resource-group $RESOURCE_GROUP
```

#### 2. Azure OpenAI

```bash
# Create OpenAI resource
az cognitiveservices account create \
  --name "oai-grant-compliance" \
  --resource-group $RESOURCE_GROUP \
  --kind OpenAI \
  --sku S0 \
  --location $LOCATION

# Deploy GPT-4 model
az cognitiveservices account deployment create \
  --name "oai-grant-compliance" \
  --resource-group $RESOURCE_GROUP \
  --deployment-name "gpt-4" \
  --model-name "gpt-4" \
  --model-version "0613" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name "Standard"
```

#### 3. Azure AI Search

```bash
# Create AI Search service
az search service create \
  --name "srch-grant-compliance" \
  --resource-group $RESOURCE_GROUP \
  --sku Standard \
  --location $LOCATION

# Get admin key
az search admin-key show \
  --service-name "srch-grant-compliance" \
  --resource-group $RESOURCE_GROUP
```

#### 4. Azure Document Intelligence

```bash
# Create Document Intelligence
az cognitiveservices account create \
  --name "docint-grant-compliance" \
  --resource-group $RESOURCE_GROUP \
  --kind FormRecognizer \
  --sku S0 \
  --location $LOCATION
```

#### 5. Azure Storage

```bash
# Create storage account
az storage account create \
  --name "stgrantcompliance" \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# Create blob containers
az storage container create \
  --name "documents" \
  --account-name "stgrantcompliance"

az storage container create \
  --name "knowledge-base" \
  --account-name "stgrantcompliance"
```

#### 6. Azure Key Vault

```bash
# Create Key Vault
az keyvault create \
  --name "kv-grant-compliance" \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Store secrets
az keyvault secret set \
  --vault-name "kv-grant-compliance" \
  --name "AzureOpenAIKey" \
  --value "your-openai-key"

az keyvault secret set \
  --vault-name "kv-grant-compliance" \
  --name "AzureSearchKey" \
  --value "your-search-key"
```

#### 7. Azure App Service (Backend)

```bash
# Create App Service Plan
az appservice plan create \
  --name "asp-grant-compliance" \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku P1V2 \
  --is-linux

# Create Web App
az webapp create \
  --name "app-grant-compliance-api" \
  --resource-group $RESOURCE_GROUP \
  --plan "asp-grant-compliance" \
  --runtime "PYTHON:3.10"
```

#### 8. Azure Static Web Apps (Frontend)

```bash
# Create Static Web App
az staticwebapp create \
  --name "swa-grant-compliance" \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard
```

#### 9. Azure Functions (Email Notifications)

```bash
# Create Function App
az functionapp create \
  --name "func-grant-compliance-email" \
  --resource-group $RESOURCE_GROUP \
  --storage-account "stgrantcompliance" \
  --consumption-plan-location $LOCATION \
  --runtime python \
  --runtime-version 3.10 \
  --functions-version 4
```

---

## Application Deployment

### Backend Deployment (FastAPI)

#### Option 1: Deploy to Azure App Service

```bash
cd backend

# Create startup script
cat > startup.sh << 'EOF'
#!/bin/bash
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
EOF

chmod +x startup.sh

# Configure App Service
az webapp config set \
  --name "app-grant-compliance-api" \
  --resource-group $RESOURCE_GROUP \
  --startup-file "startup.sh"

# Deploy code
az webapp up \
  --name "app-grant-compliance-api" \
  --resource-group $RESOURCE_GROUP \
  --runtime "PYTHON:3.10"
```

#### Option 2: Deploy via GitHub Actions

Create `.github/workflows/deploy-backend.yml`:

```yaml
name: Deploy Backend

on:
  push:
    branches: [ main ]
    paths:
      - 'backend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Deploy to Azure Web App
        uses: azure/webapps-deploy@v2
        with:
          app-name: 'app-grant-compliance-api'
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
          package: ./backend
```

### Frontend Deployment (React)

#### Option 1: Deploy to Azure Static Web Apps

```bash
cd frontend

# Build production bundle
npm run build

# Deploy to Static Web Apps
az staticwebapp deploy \
  --name "swa-grant-compliance" \
  --resource-group $RESOURCE_GROUP \
  --app-location "./dist"
```

#### Option 2: Deploy via GitHub Actions

Create `.github/workflows/deploy-frontend.yml`:

```yaml
name: Deploy Frontend

on:
  push:
    branches: [ main ]
    paths:
      - 'frontend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install and Build
        run: |
          cd frontend
          npm install
          npm run build
      
      - name: Deploy to Azure Static Web Apps
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          action: "upload"
          app_location: "frontend"
          output_location: "dist"
```

### Azure Functions Deployment (Email Notifications)

```bash
cd functions/email_notifier

# Install dependencies
pip install -r requirements.txt --target .python_packages/lib/site-packages

# Deploy function
func azure functionapp publish func-grant-compliance-email
```

---

## Post-Deployment Configuration

### 1. Configure App Settings

```bash
# Backend App Service
az webapp config appsettings set \
  --name "app-grant-compliance-api" \
  --resource-group $RESOURCE_GROUP \
  --settings \
    AZURE_OPENAI_ENDPOINT="https://oai-grant-compliance.openai.azure.com/" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4" \
    AZURE_SEARCH_ENDPOINT="https://srch-grant-compliance.search.windows.net" \
    AZURE_SEARCH_INDEX_NAME="grant-compliance-index" \
    USE_MANAGED_IDENTITY="true"

# Function App
az functionapp config appsettings set \
  --name "func-grant-compliance-email" \
  --resource-group $RESOURCE_GROUP \
  --settings \
    SMTP_SERVER="smtp.office365.com" \
    SMTP_PORT="587"
```

### 2. Configure Managed Identity

```bash
# Enable system-assigned managed identity for Web App
az webapp identity assign \
  --name "app-grant-compliance-api" \
  --resource-group $RESOURCE_GROUP

# Get identity principal ID
IDENTITY_ID=$(az webapp identity show \
  --name "app-grant-compliance-api" \
  --resource-group $RESOURCE_GROUP \
  --query principalId -o tsv)

# Grant Key Vault access
az keyvault set-policy \
  --name "kv-grant-compliance" \
  --object-id $IDENTITY_ID \
  --secret-permissions get list

# Grant Azure OpenAI access
az role assignment create \
  --assignee $IDENTITY_ID \
  --role "Cognitive Services OpenAI User" \
  --scope "/subscriptions/your-subscription-id/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/oai-grant-compliance"
```

### 3. Index Knowledge Base

```bash
# Upload executive orders to Azure AI Search
python scripts/index_knowledge_base.py \
  --input knowledge_base/executive_orders \
  --endpoint "https://srch-grant-compliance.search.windows.net" \
  --index "grant-compliance-index"
```

### 4. Configure Custom Domain (Optional)

```bash
# Frontend
az staticwebapp hostname set \
  --name "swa-grant-compliance" \
  --resource-group $RESOURCE_GROUP \
  --hostname "compliance.yourdomain.com"

# Backend
az webapp config hostname add \
  --webapp-name "app-grant-compliance-api" \
  --resource-group $RESOURCE_GROUP \
  --hostname "api.yourdomain.com"
```

### 5. Configure SSL/TLS

```bash
# Enable HTTPS only
az webapp update \
  --name "app-grant-compliance-api" \
  --resource-group $RESOURCE_GROUP \
  --https-only true
```

---

## Monitoring & Maintenance

### Enable Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app "appinsights-grant-compliance" \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP

# Connect to Web App
az webapp config appsettings set \
  --name "app-grant-compliance-api" \
  --resource-group $RESOURCE_GROUP \
  --settings \
    APPLICATIONINSIGHTS_CONNECTION_STRING="your-connection-string"
```

### Set Up Alerts

```bash
# Create action group
az monitor action-group create \
  --name "ag-grant-compliance" \
  --resource-group $RESOURCE_GROUP \
  --short-name "GrantAlert" \
  --email-receiver \
    name="AdminEmail" \
    email-address="admin@yourdomain.com"

# Create alert rule for errors
az monitor metrics alert create \
  --name "alert-high-error-rate" \
  --resource-group $RESOURCE_GROUP \
  --scopes "/subscriptions/your-subscription-id/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/app-grant-compliance-api" \
  --condition "avg Http5xx > 5" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action "ag-grant-compliance"
```

### Backup Strategy

```bash
# Enable automatic backups for Web App
az webapp config backup create \
  --resource-group $RESOURCE_GROUP \
  --webapp-name "app-grant-compliance-api" \
  --container-url "https://stgrantcompliance.blob.core.windows.net/backups?<SAS-token>" \
  --backup-name "daily-backup" \
  --frequency 1d \
  --retention-period-in-days 30
```

---

## Troubleshooting

### Common Issues

#### 1. Application won't start
```bash
# Check logs
az webapp log tail \
  --name "app-grant-compliance-api" \
  --resource-group $RESOURCE_GROUP

# Check configuration
az webapp config show \
  --name "app-grant-compliance-api" \
  --resource-group $RESOURCE_GROUP
```

#### 2. Authentication errors
```bash
# Verify managed identity
az webapp identity show \
  --name "app-grant-compliance-api" \
  --resource-group $RESOURCE_GROUP

# Check role assignments
az role assignment list \
  --assignee $IDENTITY_ID
```

#### 3. Slow performance
```bash
# Scale up App Service
az appservice plan update \
  --name "asp-grant-compliance" \
  --resource-group $RESOURCE_GROUP \
  --sku P2V2

# Enable auto-scaling
az monitor autoscale create \
  --resource-group $RESOURCE_GROUP \
  --name "autoscale-grant-compliance" \
  --resource "/subscriptions/your-subscription-id/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/serverFarms/asp-grant-compliance" \
  --min-count 1 \
  --max-count 5 \
  --count 2
```

---

## Rollback Procedure

```bash
# List deployment history
az webapp deployment list \
  --name "app-grant-compliance-api" \
  --resource-group $RESOURCE_GROUP

# Rollback to previous deployment
az webapp deployment source config-zip \
  --name "app-grant-compliance-api" \
  --resource-group $RESOURCE_GROUP \
  --src previous-version.zip
```

---

## References

- [Azure App Service Documentation](https://learn.microsoft.com/azure/app-service/)
- [Azure Static Web Apps Documentation](https://learn.microsoft.com/azure/static-web-apps/)
- [Azure Functions Documentation](https://learn.microsoft.com/azure/azure-functions/)
- [Azure CLI Reference](https://learn.microsoft.com/cli/azure/)

---

**Last Updated**: November 2025  
**Version**: 1.0
