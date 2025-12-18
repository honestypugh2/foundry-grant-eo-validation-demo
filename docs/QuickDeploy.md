# Quick Start: Deploy to Azure

Get your Grant EO Validation system running on Azure in under 10 minutes.

## Prerequisites ✅

1. **Azure Subscription** with Owner or Contributor access
2. **Azure Developer CLI** installed:
   ```bash
   # Linux/Mac
   curl -fsSL https://aka.ms/install-azd.sh | bash
   
   # Windows
   winget install microsoft.azd
   ```
3. **Azure CLI** (optional, for manual operations):
   ```bash
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```

## 🚀 One-Command Deployment

```bash
# 1. Clone repository
git clone https://github.com/honestypugh2/foundry-grant-eo-validation-demo.git
cd foundry-grant-eo-validation-demo

# 2. Login to Azure
azd auth login

# 3. Deploy everything (infrastructure + apps)
azd up
```

That's it! ☕ Grab a coffee while Azure provisions ~15 resources.

## What Gets Deployed

| Resource | Purpose | Cost/Month |
|----------|---------|------------|
| Azure AI Foundry | AI orchestration + GPT-4 | ~$250 |
| Document Intelligence | PDF processing | ~$50 |
| Azure AI Search | Semantic search | ~$75 |
| Storage Account | Document storage | ~$5 |
| App Services (2x) - Optional | Backend + Frontend hosting | ~$26 |

**Total: ~$406/month** + OpenAI usage

## Post-Deployment Steps

### 1. Get Your URLs

```bash
# View all outputs
azd show

# Or get specific URLs
azd env get-values | grep URL
```

### 2. Index Knowledge Base

```bash
# Install Python dependencies
uv sync
source .venv/bin/activate

# Upload executive orders to search index
python scripts/index_knowledge_base.py \
  --input knowledge_base/executive_orders/
```

### 3. Test the Application

```bash
# Open frontend in browser
azd show

# Test backend API
BACKEND_URL=$(azd env get-value BACKEND_URI)
curl $BACKEND_URL/health
```

## Environment Variables

Azure Developer CLI automatically configures:

```bash
# View all environment variables
azd env get-values

# Save to local .env file
azd env get-values > .env
```

## Common Commands

```bash
# Deploy app code only (after infrastructure exists)
azd deploy

# Update infrastructure
azd provision

# View logs
azd monitor

# Delete everything
azd down
```

## Troubleshooting

### Issue: "Subscription not found"
```bash
# Set subscription explicitly
azd env set AZURE_SUBSCRIPTION_ID $(az account show --query id -o tsv)
azd provision
```

### Issue: "OpenAI quota exceeded"
- Try different region: `azd env set AZURE_LOCATION westus`
- Or request quota increase in Azure Portal

### Issue: "Permission denied"
```bash
# Ensure you have proper role
az role assignment create \
  --assignee $(az ad signed-in-user show --query id -o tsv) \
  --role Owner \
  --scope /subscriptions/$(az account show --query id -o tsv)
```

## Alternative: Manual Deployment

If you prefer Terraform or Bicep without azd:

**Terraform:**
```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars
terraform init
terraform apply
```

**Bicep:**
```bash
cd infra
az deployment sub create \
  --location eastus \
  --template-file main.bicep \
  --parameters environmentName=dev
```

See [infra/README.md](../infra/README.md) for detailed instructions.

## Next Steps

- 📖 [User Guide](UserGuide.md) - How to use the application
- 🏗️ [Architecture](Architecture.md) - System design details
- 🔧 [Customize Agents](../README.md#agent-customization) - Tailor AI agents to your needs
- 📊 [Monitor Costs](https://portal.azure.com/#blade/Microsoft_Azure_CostManagement/Menu/overview) - Track Azure spending

## Clean Up

When you're done testing:

```bash
# Delete all Azure resources
azd down

# Keep environment config for later
azd down --purge
```

---

**Need help?** Open an issue or see [full deployment guide](../infra/README.md).
