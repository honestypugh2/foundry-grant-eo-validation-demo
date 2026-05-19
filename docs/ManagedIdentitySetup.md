# Managed Identity Setup

This guide explains how to use Azure Managed Identities for authentication across all services in the Grant EO Validation Demo.

## Benefits of Managed Identity

- **Enhanced Security**: No API keys to manage or rotate
- **Simplified Credential Management**: Azure handles authentication automatically
- **Audit & Compliance**: Better tracking of resource access
- **Zero Trust Architecture**: Follows security best practices

## Overview of Managed Identities

This project uses three system-assigned managed identities:

| Identity | Resource | Purpose |
|----------|----------|---------|
| **Search Service MI** | Azure AI Search | Calls the integrated vectorizer (embedding endpoint) |
| **Foundry Project MI** | Azure AI Foundry Project | Queries and writes to the search index via AzureAISearchTool |
| **Account MI** | Azure AI Services (Cognitive Services) | Accesses search index for agent operations |

## Required Role Assignments

### 1. Search Service MI → AI Services (for Integrated Vectorizer)

The search service's managed identity needs permission to call the embedding model (`text-embedding-3-small`) on the AI Services resource:

```bash
# Get the Search Service MI principal ID
SEARCH_MI=$(az search service show \
  --name your-search-service \
  --resource-group your-rg \
  --query identity.principalId -o tsv)

# Get the AI Services resource ID
AI_SERVICES_ID=$(az cognitiveservices account show \
  --name your-ai-services \
  --resource-group your-rg \
  --query id -o tsv)

# Assign Cognitive Services OpenAI User
az role assignment create \
  --assignee $SEARCH_MI \
  --role "Cognitive Services OpenAI User" \
  --scope $AI_SERVICES_ID
```

> **Why**: The integrated vectorizer on the search index calls the embedding endpoint using the search service's identity. Without this role, vectorization returns 401 Unauthorized.

### 2. Foundry Project MI → Azure AI Search (for Agent Search Tool)

The Foundry project's managed identity needs permission to read/write the search index when agents use `AzureAISearchTool`:

```bash
# Get the Foundry Project MI principal ID
PROJECT_MI=$(az resource show \
  --ids /subscriptions/YOUR_SUB/resourceGroups/YOUR_RG/providers/Microsoft.CognitiveServices/accounts/YOUR_AI_SERVICES/projects/YOUR_PROJECT \
  --query identity.principalId -o tsv)

# Get the Search Service resource ID
SEARCH_ID=$(az search service show \
  --name your-search-service \
  --resource-group your-rg \
  --query id -o tsv)

# Assign Search roles
az role assignment create --assignee $PROJECT_MI --role "Search Index Data Reader" --scope $SEARCH_ID
az role assignment create --assignee $PROJECT_MI --role "Search Index Data Contributor" --scope $SEARCH_ID
az role assignment create --assignee $PROJECT_MI --role "Search Service Contributor" --scope $SEARCH_ID
```

### 3. Account MI → Azure AI Search (for Account-level Access)

The AI Services account identity also needs search access:

```bash
# Get the Account MI principal ID
ACCOUNT_MI=$(az cognitiveservices account show \
  --name your-ai-services \
  --resource-group your-rg \
  --query identity.principalId -o tsv)

# Assign Search roles
az role assignment create --assignee $ACCOUNT_MI --role "Search Index Data Reader" --scope $SEARCH_ID
az role assignment create --assignee $ACCOUNT_MI --role "Search Index Data Contributor" --scope $SEARCH_ID
```

### 4. Document Intelligence MI (Optional)

For Azure Document Intelligence access without API keys:

## Usage in Code

### Basic Usage

```python
from agents.document_ingestion_agent import DocumentIngestionAgent

# Initialize with managed identity
agent = DocumentIngestionAgent(
    use_azure=True,
    use_managed_identity=True
)

# Process document
result = agent.process_document("path/to/document.pdf")
print(result['text'])
```

### Using Environment Variable

```python
import os

# Set environment variable
os.environ['USE_MANAGED_IDENTITY'] = 'true'

# Agent will automatically use managed identity
agent = DocumentIngestionAgent(use_azure=True)
```

## Testing

### Run the Test Script

```bash
# Set the endpoint
export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://<your-resource>.cognitiveservices.azure.com/"

# Run the test
python tests/test_document_intelligence_managed_identity.py
```

The test script will:
1. Verify Azure credentials are available
2. Initialize the agent with managed identity only (no API key)
3. Process a test document
4. Display extracted text and metadata

### Local Development Testing

For local development without deploying to Azure:

```bash
# Login with Azure CLI
az login

# The DefaultAzureCredential will use your Azure CLI credentials
python tests/test_document_intelligence_managed_identity.py
```

## Troubleshooting

### "Failed to acquire token"

**Cause**: Not running in Azure environment or not logged in locally

**Solution**:
- For local development: Run `az login`
- For Azure resources: Enable managed identity in the portal
- Verify you have the correct role assignments

### "Access denied"

**Cause**: Managed identity doesn't have the required permissions

**Solution**:
- Verify role assignment: `az role assignment list --assignee <principal-id>`
- Ensure the role is **Cognitive Services User** or higher
- Wait a few minutes for role propagation

### "Endpoint not configured"

**Cause**: Missing `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` environment variable

**Solution**:
```bash
export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://<your-resource>.cognitiveservices.azure.com/"
```

## Security Best Practices

1. **Never commit API keys**: Use managed identity in production
2. **Principle of least privilege**: Grant only necessary roles
3. **Monitor access**: Use Azure Monitor to track resource access
4. **Use Key Vault for secrets**: Store other sensitive data in Azure Key Vault with managed identity access

## Migration from API Key to Managed Identity

1. **Enable managed identity** on your compute resource
2. **Assign roles** to the managed identity
3. **Set environment variable**: `USE_MANAGED_IDENTITY=true`
4. **Remove API key** from environment variables
5. **Test thoroughly** before removing API key from production
6. **Monitor logs** for authentication issues

## Additional Resources

- [Azure Managed Identity Documentation](https://docs.microsoft.com/azure/active-directory/managed-identities-azure-resources/)
- [Azure Document Intelligence Authentication](https://docs.microsoft.com/azure/ai-services/document-intelligence/authentication)
- [DefaultAzureCredential](https://docs.microsoft.com/python/api/azure-identity/azure.identity.defaultazurecredential)
