# SharePoint Integration Guide

## Overview

This guide explains how to integrate SharePoint document access into the Grant Compliance Automation system using Azure AI Foundry agents with the SharePoint grounding tool.

**Official Documentation**: [SharePoint Tool for Azure AI Foundry Agents](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/sharepoint)

## Features

- 🔍 **Semantic Search**: Search SharePoint documents using natural language
- 📄 **Document Access**: Retrieve and process documents from SharePoint
- 🤖 **AI Grounding**: Agent responses grounded in SharePoint content
- 🔐 **Secure Access**: Uses Azure AD authentication
- 📚 **Library Integration**: Access multiple document libraries

## Prerequisites

### Azure Resources

1. **Azure AI Foundry Project**
   - Project created in Azure AI Foundry
   - Connection string available

2. **SharePoint Site**
   - SharePoint Online site with document libraries
   - Grant proposals and executive orders stored in SharePoint

3. **Azure AD App Registration**
   - Application registered in Azure AD
   - API permissions configured for SharePoint
   - Client secret generated

### Required Permissions

Your Azure AD app needs the following Microsoft Graph API permissions:

| Permission | Type | Purpose |
|------------|------|---------|
| `Sites.Read.All` | Application | Read SharePoint sites and documents |
| `Files.Read.All` | Application | Read files from SharePoint |

Grant admin consent for these permissions in Azure AD.

## Setup Instructions

### Step 1: Create Azure AD App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Configure:
   - Name: `Grant Compliance SharePoint Access`
   - Supported account types: `Single tenant`
   - Click **Register**

5. Note the following values:
   - **Application (client) ID**
   - **Directory (tenant) ID**

6. Create a client secret:
   - Go to **Certificates & secrets**
   - Click **New client secret**
   - Add description: `SharePoint Access Secret`
   - Set expiration (recommend: 24 months)
   - Click **Add**
   - **Copy the secret value immediately** (you won't see it again)

### Step 2: Configure API Permissions

1. In your app registration, go to **API permissions**
2. Click **Add a permission**
3. Select **Microsoft Graph**
4. Choose **Application permissions**
5. Add these permissions:
   - `Sites.Read.All`
   - `Files.Read.All`
6. Click **Grant admin consent** (requires admin)

### Step 3: Configure SharePoint Site

1. Open your SharePoint site
2. Note the full site URL (e.g., `https://contoso.sharepoint.com/sites/GrantCompliance`)
3. Ensure document libraries exist:
   - `GrantProposals` - For submitted proposals
   - `ExecutiveOrders` - For reference documents
   - `Documents` - For general files

4. Grant permissions:
   - Go to **Site permissions**
   - Add your Azure AD app as a site member

### Step 4: Configure Environment Variables

Add the following to your `.env` file:

```bash
# SharePoint Configuration (Optional)
SHAREPOINT_SITE_URL=https://yourtenant.sharepoint.com/sites/yoursite
SHAREPOINT_CLIENT_ID=your_client_id_here
SHAREPOINT_CLIENT_SECRET=your_client_secret_here
AZURE_TENANT_ID=your_tenant_id_here

# These should already be configured:
AZURE_AI_PROJECT_ENDPOINT=https://your-resource.services.ai.azure.com/api/projects/your-project
```

**Note:** The Azure AI Project endpoint can be found in the Azure AI Foundry portal under your Project's Overview page.

### Step 5: Install Dependencies

```bash
# Install Azure AI Projects SDK
uv pip install azure-ai-projects

# Install Azure Identity
uv pip install azure-identity
```

### Step 6: Test the Integration

```bash
# Run the SharePoint integration script
python scripts/sharepoint_integration.py
```

This will:
- Validate your configuration
- Test the SharePoint connection
- List available document libraries
- Run example searches

## Usage

### Basic Usage

```python
from scripts.sharepoint_integration import SharePointDocumentAccess

# Initialize SharePoint access
sp_access = SharePointDocumentAccess()

# Search for documents
results = sp_access.search_sharepoint_documents(
    query="grant proposals submitted in 2024",
    document_library="GrantProposals",
    max_results=10
)

# List available libraries
libraries = sp_access.list_document_libraries()

# Get document content
content = sp_access.get_document_content(
    "https://tenant.sharepoint.com/sites/site/Documents/proposal.pdf"
)
```

### Integration with Compliance Agent

```python
from agents.compliance_agent import ComplianceAgent
from scripts.sharepoint_integration import SharePointDocumentAccess

# Initialize
sp_access = SharePointDocumentAccess()
compliance_agent = ComplianceAgent(
    project_endpoint=os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT"),
    model_deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    search_index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
    azure_search_document_truncation_size=2000,
    use_managed_identity=False
)

# Search for executive orders in SharePoint
eo_results = sp_access.search_sharepoint_documents(
    query="executive orders on climate action",
    document_library="ExecutiveOrders"
)

# Use results in compliance validation
for doc_info in eo_results:
    # Process document content
    content = sp_access.get_document_content(doc_info['url'])
    # Validate compliance
    compliance_agent.validate_against_document(content)
```

### Create Agent with SharePoint Access

```python
from scripts.sharepoint_integration import SharePointDocumentAccess

sp_access = SharePointDocumentAccess()

# Create agent with SharePoint grounding
agent = sp_access.create_agent_with_sharepoint(
    agent_name="Grant Compliance Assistant"
)

# Agent can now access SharePoint documents automatically
response = agent.run(
    "Find all grant proposals related to affordable housing and "
    "check them against the Climate Crisis executive order"
)
```

## Workflow Integration

### Option 1: Replace Local Knowledge Base

Use SharePoint as the primary source for executive orders:

```python
# agents/compliance_validator_agent.py

from scripts.sharepoint_integration import SharePointDocumentAccess

class ComplianceValidatorAgent:
    def __init__(self, use_azure=False, use_sharepoint=False):
        self.use_sharepoint = use_sharepoint
        
        if self.use_sharepoint:
            self.sp_access = SharePointDocumentAccess()
    
    def _search_executive_orders(self, query):
        if self.use_sharepoint:
            # Search SharePoint instead of local files
            return self.sp_access.search_sharepoint_documents(
                query=query,
                document_library="ExecutiveOrders"
            )
        else:
            # Use local knowledge base
            return self._search_local_kb(query)
```

### Option 2: Hybrid Approach

Use both SharePoint and local storage:

```python
def _search_knowledge_base(self, query):
    results = []
    
    # Search local files
    local_results = self._search_local_kb(query)
    results.extend(local_results)
    
    # Search SharePoint if available
    if self.use_sharepoint:
        try:
            sp_results = self.sp_access.search_sharepoint_documents(
                query=query,
                document_library="ExecutiveOrders"
            )
            results.extend(sp_results)
        except Exception as e:
            logger.warning(f"SharePoint search failed: {e}")
    
    return results
```

### Option 3: Production Deployment

In production, use SharePoint as the primary document store:

1. **Document Submission**:
   - Users submit proposals to SharePoint library
   - SharePoint webhook triggers Azure Function
   - Function initiates compliance workflow

2. **Processing**:
   - Agent retrieves document from SharePoint
   - Searches executive orders in SharePoint
   - Performs compliance analysis

3. **Results Storage**:
   - Store analysis results back to SharePoint
   - Add metadata tags
   - Trigger attorney notification

## Configuration Options

### Document Libraries

Recommended SharePoint library structure:

```
SharePoint Site: Grant Compliance
│
├── GrantProposals/
│   ├── Pending/           # Submitted proposals awaiting review
│   ├── UnderReview/       # Currently being analyzed
│   ├── Approved/          # Compliance approved
│   └── NeedsRevision/     # Requires changes
│
├── ExecutiveOrders/
│   ├── Federal/           # Federal executive orders
│   ├── State/             # State-level orders
│   └── Local/             # County/municipal orders
│
├── ComplianceReports/
│   └── [Year]/            # Organized by year
│
└── Templates/
    ├── ProposalTemplates/
    └── ReviewForms/
```

### Metadata Tags

Configure SharePoint columns for better organization:

| Column Name | Type | Purpose |
|-------------|------|---------|
| ComplianceStatus | Choice | Pending, Approved, Rejected, Needs Revision |
| SubmissionDate | Date | When proposal was submitted |
| ReviewDate | Date | When review was completed |
| AssignedAttorney | Person | Attorney reviewing the proposal |
| RiskLevel | Choice | Low, Medium, High, Critical |
| ExecutiveOrders | Lookup | Related EOs checked |
| AIConfidence | Number | Confidence score (0-100) |

## Troubleshooting

### Common Issues

#### 1. Authentication Failed

**Error**: `Authentication failed` or `Unauthorized`

**Solutions**:
- Verify Client ID and Secret are correct
- Check that admin consent was granted for API permissions
- Ensure app has access to the SharePoint site
- Verify tenant ID is correct

#### 2. SharePoint Site Not Found

**Error**: `Site not found` or `Access denied`

**Solutions**:
- Confirm site URL is correct (include `/sites/sitename`)
- Check that the site exists and is accessible
- Verify app permissions include `Sites.Read.All`
- Add app to site permissions explicitly

#### 3. Documents Not Appearing

**Error**: Search returns no results

**Solutions**:
- Wait for SharePoint indexing (can take 15 minutes for new docs)
- Check document library name is correct
- Verify documents are not in folders (adjust search if needed)
- Ensure app has `Files.Read.All` permission

#### 4. Import Error

**Error**: `ModuleNotFoundError: No module named 'azure.ai.projects'`

**Solutions**:
```bash
uv pip install azure-ai-projects azure-identity
```

### Debug Mode

Enable detailed logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('azure.ai.projects')
logger.setLevel(logging.DEBUG)
```

## Security Best Practices

### 1. Secure Credential Storage

Never commit credentials to source control:

```bash
# Add to .gitignore
.env
.env.local
secrets/
```

### 2. Use Azure Key Vault

For production, store secrets in Azure Key Vault:

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(
    vault_url="https://your-vault.vault.azure.net/",
    credential=credential
)

sharepoint_secret = client.get_secret("sharepoint-client-secret").value
```

### 3. Managed Identity

Use managed identity in Azure deployments:

```python
from azure.identity import ManagedIdentityCredential

credential = ManagedIdentityCredential()
# No client secret needed!
```

### 4. Least Privilege

Only grant minimum required permissions:
- Use `Sites.Selected` instead of `Sites.Read.All` when possible
- Restrict to specific site collections
- Review permissions regularly

## Performance Optimization

### 1. Caching

Cache frequently accessed documents:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_document(url):
    return sp_access.get_document_content(url)
```

### 2. Batch Operations

Process multiple documents efficiently:

```python
def batch_process_proposals(library_name, max_docs=50):
    results = sp_access.search_sharepoint_documents(
        query="status:pending",
        document_library=library_name,
        max_results=max_docs
    )
    
    for doc in results:
        # Process in parallel if possible
        process_document(doc)
```

### 3. Incremental Sync

Only process new/modified documents:

```python
last_sync = get_last_sync_time()

# Search for documents modified since last sync
results = sp_access.search_sharepoint_documents(
    query=f"modified >= {last_sync}",
    document_library="GrantProposals"
)
```

## Automatic Document Indexing & Updates

### Overview

The system can automatically detect, index, and process new documents added to SharePoint using webhooks and Azure Functions, eliminating the need for manual intervention.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Automatic Indexing Flow                          │
└─────────────────────────────────────────────────────────────────────┘

   SharePoint                Azure Event Grid          Azure Function
   Document Library          Subscription              Handler
   ┌─────────────┐          ┌──────────────┐          ┌──────────────┐
   │             │          │              │          │              │
   │ New File    │          │  Document    │          │  Process &   │
   │ Uploaded    │─────────>│  Change      │─────────>│  Index       │
   │             │  Webhook │  Event       │  Trigger │  Document    │
   │             │          │              │          │              │
   └─────────────┘          └──────────────┘          └──────────────┘
         │                                                    │
         │                                                    │
         v                                                    v
   ┌─────────────┐          ┌──────────────┐          ┌──────────────┐
   │             │          │              │          │              │
   │ SharePoint  │          │  Azure AI    │          │  Update      │
   │ Metadata    │<─────────│  Search      │<─────────│  Search      │
   │ Updated     │  Update  │  Index       │  Index   │  Embeddings  │
   │             │  Tags    │              │  Content │              │
   └─────────────┘          └──────────────┘          └──────────────┘
                                   │
                                   │
                                   v
                            ┌──────────────┐
                            │              │
                            │  Available   │
                            │  for Agent   │
                            │  Queries     │
                            │              │
                            └──────────────┘
```

### Implementation Steps

#### Step 1: Configure SharePoint Webhooks

SharePoint webhooks notify your application when content changes.

**Create Webhook Subscription:**

```python
import requests
import os
from datetime import datetime, timedelta

def create_sharepoint_webhook(site_url, list_id, notification_url):
    """
    Create a webhook subscription for a SharePoint list/library.
    
    Args:
        site_url: SharePoint site URL
        list_id: GUID of the document library
        notification_url: Your Azure Function endpoint URL
    """
    endpoint = f"{site_url}/_api/web/lists(guid'{list_id}')/subscriptions"
    
    # Webhook expires after 6 months (max)
    expiration = (datetime.utcnow() + timedelta(days=180)).isoformat() + 'Z'
    
    payload = {
        "resource": f"{site_url}/_api/web/lists(guid'{list_id}')",
        "notificationUrl": notification_url,
        "expirationDateTime": expiration,
        "clientState": "your-secret-state-value"  # For validation
    }
    
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    response = requests.post(endpoint, json=payload, headers=headers)
    
    if response.status_code == 201:
        subscription = response.json()
        print(f"✓ Webhook created: {subscription['id']}")
        return subscription
    else:
        print(f"✗ Webhook creation failed: {response.text}")
        return None

# Usage
webhook = create_sharepoint_webhook(
    site_url="https://yourtenant.sharepoint.com/sites/GrantCompliance",
    list_id="your-library-guid-here",
    notification_url="https://your-function-app.azurewebsites.net/api/SharePointWebhookHandler"
)
```

**Renew Webhook Subscription:**

Webhooks expire after 6 months. Set up automatic renewal:

```python
def renew_webhook_subscription(site_url, list_id, subscription_id):
    """Renew webhook subscription before expiration."""
    endpoint = f"{site_url}/_api/web/lists(guid'{list_id}')/subscriptions('{subscription_id}')"
    
    expiration = (datetime.utcnow() + timedelta(days=180)).isoformat() + 'Z'
    
    payload = {
        "expirationDateTime": expiration
    }
    
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    response = requests.patch(endpoint, json=payload, headers=headers)
    return response.status_code == 204
```

#### Step 2: Create Azure Function for Webhook Handler

Create an Azure Function to receive and process webhook notifications.

**Function Code (Python):**

```python
# function_app.py
import azure.functions as func
import json
import logging
from datetime import datetime

app = func.FunctionApp()

@app.route(route="SharePointWebhookHandler", auth_level=func.AuthLevel.FUNCTION)
async def sharepoint_webhook_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    Handle SharePoint webhook notifications.
    This function is triggered when documents are added/modified in SharePoint.
    """
    logging.info('SharePoint webhook triggered')
    
    try:
        # Validate webhook request
        validation_token = req.params.get('validationtoken')
        if validation_token:
            # Initial webhook validation
            logging.info(f"Webhook validation: {validation_token}")
            return func.HttpResponse(
                validation_token,
                status_code=200,
                mimetype="text/plain"
            )
        
        # Process webhook notification
        req_body = req.get_json()
        
        # Verify client state
        if req_body.get('value'):
            for notification in req_body['value']:
                client_state = notification.get('clientState')
                
                if client_state != os.getenv('WEBHOOK_CLIENT_STATE'):
                    logging.warning("Invalid client state")
                    return func.HttpResponse(
                        "Invalid client state",
                        status_code=401
                    )
                
                # Process the notification
                resource = notification.get('resource')
                site_url = notification.get('siteUrl')
                web_id = notification.get('webId')
                
                logging.info(f"Processing changes for: {resource}")
                
                # Queue document processing
                await queue_document_processing(notification)
        
        # Return success (must return 200 within 5 seconds)
        return func.HttpResponse(
            json.dumps({"status": "accepted"}),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


async def queue_document_processing(notification):
    """
    Queue document for indexing and processing.
    Uses Azure Storage Queue for asynchronous processing.
    """
    from azure.storage.queue import QueueClient
    
    queue_client = QueueClient.from_connection_string(
        os.getenv('AZURE_STORAGE_CONNECTION_STRING'),
        "document-processing-queue"
    )
    
    message = {
        "notification_id": notification.get('subscriptionId'),
        "resource": notification.get('resource'),
        "site_url": notification.get('siteUrl'),
        "timestamp": datetime.utcnow().isoformat(),
        "action": "index_document"
    }
    
    queue_client.send_message(json.dumps(message))
    logging.info(f"Queued document processing: {message}")
```

**Function Requirements (requirements.txt):**

```txt
azure-functions
azure-identity
azure-storage-queue
azure-ai-projects
azure-search-documents
```

**Function Configuration (host.json):**

```json
{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true
      }
    }
  },
  "functionTimeout": "00:05:00"
}
```

#### Step 3: Create Document Processor Function

Process queued documents asynchronously:

```python
@app.queue_trigger(
    arg_name="msg",
    queue_name="document-processing-queue",
    connection="AzureWebJobsStorage"
)
async def process_document_queue(msg: func.QueueMessage):
    """
    Process documents from the queue.
    Retrieves changed documents and indexes them in Azure AI Search.
    """
    logging.info('Processing document from queue')
    
    try:
        message = json.loads(msg.get_body().decode('utf-8'))
        
        # Get changed items from SharePoint
        changed_items = await get_changed_items(
            message['site_url'],
            message['resource']
        )
        
        for item in changed_items:
            await process_and_index_document(item)
            
    except Exception as e:
        logging.error(f"Error processing document: {str(e)}")
        raise


async def get_changed_items(site_url, resource):
    """
    Retrieve changed items from SharePoint.
    Uses change token to get only new/modified items.
    """
    import requests
    
    # Get change token from storage (or start fresh)
    change_token = await get_last_change_token(resource)
    
    endpoint = f"{site_url}/_api/web/lists/getbyid('{get_list_id(resource)}')/GetChanges"
    
    query = {
        "ChangeTokenStart": change_token,
        "Add": True,
        "Update": True,
        "Item": True
    }
    
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    response = requests.post(endpoint, json={"query": query}, headers=headers)
    
    if response.status_code == 200:
        changes = response.json().get('value', [])
        
        # Save new change token
        if changes:
            await save_change_token(resource, changes[-1]['ChangeToken'])
        
        return changes
    
    return []


async def process_and_index_document(item):
    """
    Download document, extract text, create embeddings, and index.
    """
    from azure.search.documents import SearchClient
    from azure.core.credentials import AzureKeyCredential
    
    # Download document from SharePoint
    document_url = item['ServerRelativeUrl']
    content = await download_document(document_url)
    
    # Extract text (using Azure Document Intelligence or similar)
    extracted_text = await extract_document_text(content, item['Name'])
    
    # Create search document
    search_doc = {
        "id": item['UniqueId'],
        "title": item['Name'],
        "content": extracted_text,
        "file_path": document_url,
        "last_modified": item['Modified'],
        "author": item['Author']['Title'],
        "document_type": get_document_type(item['Name']),
        "indexed_date": datetime.utcnow().isoformat()
    }
    
    # Add to Azure AI Search
    search_client = SearchClient(
        endpoint=os.getenv('AZURE_SEARCH_ENDPOINT'),
        index_name=os.getenv('AZURE_SEARCH_INDEX_NAME'),
        credential=AzureKeyCredential(os.getenv('AZURE_SEARCH_API_KEY'))
    )
    
    result = search_client.upload_documents([search_doc])
    logging.info(f"✓ Indexed document: {item['Name']}")
    
    # Update SharePoint metadata
    await update_sharepoint_metadata(document_url, {
        "IndexedDate": datetime.utcnow().isoformat(),
        "IndexStatus": "Indexed"
    })
```

#### Step 4: Deploy Azure Function

**Deploy using Azure CLI:**

```bash
# Create Function App
az functionapp create \
  --resource-group your-resource-group \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name grant-compliance-webhook-handler \
  --storage-account yourstorageaccount \
  --os-type Linux

# Configure app settings
az functionapp config appsettings set \
  --name grant-compliance-webhook-handler \
  --resource-group your-resource-group \
  --settings \
    SHAREPOINT_CLIENT_ID="your-client-id" \
    SHAREPOINT_CLIENT_SECRET="your-client-secret" \
    AZURE_TENANT_ID="your-tenant-id" \
    WEBHOOK_CLIENT_STATE="your-secret-state" \
    AZURE_SEARCH_ENDPOINT="your-search-endpoint" \
    AZURE_SEARCH_API_KEY="your-search-key" \
    AZURE_SEARCH_INDEX_NAME="grant-compliance-index"

# Deploy function code
func azure functionapp publish grant-compliance-webhook-handler
```

#### Step 5: Set Up Webhook Subscriptions

Create webhooks for all document libraries:

```python
# scripts/setup_sharepoint_webhooks.py
from sharepoint_integration import SharePointDocumentAccess

def setup_all_webhooks():
    """Set up webhooks for all relevant SharePoint libraries."""
    
    sp = SharePointDocumentAccess()
    
    libraries = [
        {
            "name": "GrantProposals",
            "list_id": "your-grant-proposals-guid"
        },
        {
            "name": "ExecutiveOrders", 
            "list_id": "your-executive-orders-guid"
        },
        {
            "name": "ComplianceReports",
            "list_id": "your-compliance-reports-guid"
        }
    ]
    
    function_url = "https://grant-compliance-webhook-handler.azurewebsites.net/api/SharePointWebhookHandler"
    
    for library in libraries:
        print(f"\nSetting up webhook for {library['name']}...")
        
        webhook = create_sharepoint_webhook(
            site_url=os.getenv('SHAREPOINT_SITE_URL'),
            list_id=library['list_id'],
            notification_url=function_url
        )
        
        if webhook:
            print(f"✓ Webhook ID: {webhook['id']}")
            print(f"  Expires: {webhook['expirationDateTime']}")
        else:
            print(f"✗ Failed to create webhook")

if __name__ == "__main__":
    setup_all_webhooks()
```

### Monitoring & Maintenance

#### Monitor Webhook Health

```python
def check_webhook_status(site_url, list_id):
    """Check status of all webhooks for a list."""
    endpoint = f"{site_url}/_api/web/lists(guid'{list_id}')/subscriptions"
    
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Accept": "application/json"
    }
    
    response = requests.get(endpoint, headers=headers)
    
    if response.status_code == 200:
        subscriptions = response.json().get('value', [])
        
        for sub in subscriptions:
            expiration = datetime.fromisoformat(sub['expirationDateTime'].rstrip('Z'))
            days_until_expiry = (expiration - datetime.utcnow()).days
            
            print(f"Webhook ID: {sub['id']}")
            print(f"  Expires in {days_until_expiry} days")
            print(f"  Notification URL: {sub['notificationUrl']}")
            
            if days_until_expiry < 30:
                print(f"  ⚠️  NEEDS RENEWAL")
                renew_webhook_subscription(site_url, list_id, sub['id'])
    
    return subscriptions
```

#### Automated Renewal with Azure Logic App

Create a Logic App to automatically renew webhooks:

```json
{
  "definition": {
    "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
    "triggers": {
      "Recurrence": {
        "type": "Recurrence",
        "recurrence": {
          "frequency": "Month",
          "interval": 1
        }
      }
    },
    "actions": {
      "RenewWebhooks": {
        "type": "Function",
        "inputs": {
          "functionName": "RenewSharePointWebhooks",
          "method": "POST"
        }
      }
    }
  }
}
```

### Testing Automatic Indexing

#### Test 1: Upload New Document

```python
# test_automatic_indexing.py
import time
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

def test_automatic_indexing():
    """Test that new documents are automatically indexed."""
    
    print("1. Upload a test document to SharePoint...")
    # Upload via SharePoint UI or API
    
    print("2. Wait for webhook processing (5-10 seconds)...")
    time.sleep(10)
    
    print("3. Check if document appears in search index...")
    search_client = SearchClient(
        endpoint=os.getenv('AZURE_SEARCH_ENDPOINT'),
        index_name=os.getenv('AZURE_SEARCH_INDEX_NAME'),
        credential=AzureKeyCredential(os.getenv('AZURE_SEARCH_API_KEY'))
    )
    
    results = search_client.search(
        search_text="your test document name",
        top=5
    )
    
    found = False
    for result in results:
        print(f"✓ Found: {result['title']}")
        found = True
    
    if found:
        print("\n✅ Automatic indexing is working!")
    else:
        print("\n❌ Document not found in index")
        print("Check Azure Function logs for errors")

if __name__ == "__main__":
    test_automatic_indexing()
```

#### Test 2: Update Existing Document

```python
def test_document_update():
    """Test that document updates trigger re-indexing."""
    
    print("1. Modify an existing document in SharePoint...")
    # Edit document via SharePoint
    
    print("2. Wait for webhook processing...")
    time.sleep(10)
    
    print("3. Verify updated content in search index...")
    # Check if modified date is updated
```

### Performance Optimization

#### Batch Processing

Process multiple document changes efficiently:

```python
async def process_batch_changes(changes):
    """Process multiple document changes in parallel."""
    import asyncio
    
    # Group changes by type
    added = [c for c in changes if c['ChangeType'] == 1]
    updated = [c for c in changes if c['ChangeType'] == 2]
    
    # Process in parallel
    tasks = []
    for item in added + updated:
        task = process_and_index_document(item)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success_count = sum(1 for r in results if not isinstance(r, Exception))
    print(f"✓ Processed {success_count}/{len(tasks)} documents")
```

#### Rate Limiting

Respect SharePoint API limits:

```python
from time import sleep
from functools import wraps

def rate_limit(max_calls_per_minute=600):
    """Decorator to rate limit SharePoint API calls."""
    interval = 60.0 / max_calls_per_minute
    
    def decorator(func):
        last_called = [0.0]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = interval - elapsed
            
            if left_to_wait > 0:
                sleep(left_to_wait)
            
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        
        return wrapper
    return decorator

@rate_limit(max_calls_per_minute=600)
def call_sharepoint_api(endpoint):
    """Rate-limited SharePoint API call."""
    pass
```

### Troubleshooting Automatic Indexing

#### Issue: Webhook Not Triggered

**Check:**
1. Verify webhook subscription exists: `check_webhook_status()`
2. Check webhook hasn't expired
3. Verify Azure Function is running
4. Check Function App logs in Azure Portal

**Solution:**
```bash
# View Function App logs
az functionapp log tail \
  --name grant-compliance-webhook-handler \
  --resource-group your-resource-group
```

#### Issue: Documents Not Appearing in Search

**Check:**
1. Verify document processing queue is working
2. Check Azure AI Search index status
3. Verify document extraction succeeded

**Debug:**
```python
# Check processing queue
from azure.storage.queue import QueueClient

queue_client = QueueClient.from_connection_string(
    os.getenv('AZURE_STORAGE_CONNECTION_STRING'),
    "document-processing-queue"
)

# Get message count
properties = queue_client.get_queue_properties()
print(f"Messages in queue: {properties.approximate_message_count}")

# Peek at messages
messages = queue_client.peek_messages(max_messages=5)
for msg in messages:
    print(f"Message: {msg.content}")
```

#### Issue: Webhook Expired

**Solution:**
```python
# Renew all expired webhooks
def renew_expired_webhooks():
    libraries = get_all_libraries()
    
    for lib in libraries:
        subscriptions = check_webhook_status(
            site_url=os.getenv('SHAREPOINT_SITE_URL'),
            list_id=lib['list_id']
        )
        
        for sub in subscriptions:
            expiration = datetime.fromisoformat(
                sub['expirationDateTime'].rstrip('Z')
            )
            
            if expiration < datetime.utcnow():
                print(f"Renewing expired webhook: {sub['id']}")
                renew_webhook_subscription(
                    os.getenv('SHAREPOINT_SITE_URL'),
                    lib['list_id'],
                    sub['id']
                )
```

### Alternative: Event Grid Integration

For more robust event handling, use Azure Event Grid:

```python
# Subscribe to SharePoint events via Event Grid
from azure.eventgrid import EventGridPublisherClient
from azure.core.credentials import AzureKeyCredential

def setup_event_grid_subscription():
    """
    Set up Event Grid subscription for SharePoint events.
    More reliable than webhooks for production scenarios.
    """
    
    # Create Event Grid topic
    topic_endpoint = "https://your-topic.region.eventgrid.azure.net/api/events"
    
    client = EventGridPublisherClient(
        topic_endpoint,
        AzureKeyCredential(os.getenv('EVENT_GRID_ACCESS_KEY'))
    )
    
    # Configure SharePoint to send events to Event Grid
    # This provides better reliability and built-in retry logic
```

### Complete Indexing Flow Summary

1. **Document Upload**: User uploads document to SharePoint
2. **Webhook Trigger**: SharePoint sends notification within seconds
3. **Azure Function**: Receives webhook, validates, queues processing
4. **Queue Processing**: Background job retrieves and processes document
5. **Text Extraction**: Extract text using Azure Document Intelligence
6. **Create Embeddings**: Generate vector embeddings for semantic search
7. **Index Document**: Add to Azure AI Search index
8. **Update Metadata**: Mark document as indexed in SharePoint
9. **Agent Access**: Document immediately available for agent queries

**End-to-End Timing:**
- Webhook notification: < 5 seconds
- Queue processing: 5-30 seconds
- Document indexing: 10-60 seconds
- **Total**: Documents available in 20-90 seconds after upload

## Next Steps

1. **Test Integration**: Run `python scripts/sharepoint_integration.py`
2. **Configure Libraries**: Set up SharePoint document libraries
3. **Update Agents**: Integrate SharePoint access into compliance agents
4. **Deploy Webhooks**: Set up SharePoint webhooks for real-time processing
5. **Configure Auto-Indexing**: Deploy Azure Functions for automatic indexing
6. **Monitor Usage**: Track API calls and performance
7. **Set Up Alerts**: Configure monitoring for webhook failures

## Resources

- [Azure AI Foundry SharePoint Tool](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/sharepoint)
- [Microsoft Graph API - SharePoint](https://learn.microsoft.com/en-us/graph/api/resources/sharepoint)
- [Azure AD App Registration](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- [SharePoint REST API](https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/get-to-know-the-sharepoint-rest-service)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Azure AI Foundry logs
3. Consult Microsoft documentation
4. Open an issue in this repository

---

**Note**: SharePoint integration is optional. The system works with local file storage if SharePoint is not configured.
