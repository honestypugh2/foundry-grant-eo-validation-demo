# Managed Identity Setup for Document Intelligence

This guide explains how to use Azure Managed Identity for authentication with Azure Document Intelligence instead of API keys.

## Benefits of Managed Identity

- **Enhanced Security**: No API keys to manage or rotate
- **Simplified Credential Management**: Azure handles authentication automatically
- **Audit & Compliance**: Better tracking of resource access
- **Zero Trust Architecture**: Follows security best practices

## Prerequisites

1. Azure Document Intelligence resource deployed
2. System-assigned or user-assigned managed identity enabled on your compute resource (VM, App Service, Function App, etc.)
3. Role assignment: Grant the managed identity **Cognitive Services User** role on the Document Intelligence resource

## Configuration

### 1. Enable Managed Identity on Your Azure Resource

**For App Service / Function App:**
```bash
az webapp identity assign --name <app-name> --resource-group <resource-group>
```

**For Virtual Machine:**
```bash
az vm identity assign --name <vm-name> --resource-group <resource-group>
```

### 2. Grant Permissions

Assign the **Cognitive Services User** role to the managed identity:

```bash
# Get the principal ID of the managed identity
PRINCIPAL_ID=$(az webapp identity show --name <app-name> --resource-group <resource-group> --query principalId -o tsv)

# Get the Document Intelligence resource ID
DI_RESOURCE_ID=$(az cognitiveservices account show --name <doc-intelligence-name> --resource-group <resource-group> --query id -o tsv)

# Assign the role
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Cognitive Services User" \
  --scope $DI_RESOURCE_ID
```

### 3. Configure Environment Variables

Set **ONLY** the endpoint (no API key needed):

```bash
export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://<your-resource>.cognitiveservices.azure.com/"
export USE_MANAGED_IDENTITY="true"
```

**Do NOT set** `AZURE_DOCUMENT_INTELLIGENCE_API_KEY` when using managed identity.

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
