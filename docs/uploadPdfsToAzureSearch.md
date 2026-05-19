# Uploading PDF Documents to Azure AI Search Knowledge Base

This guide provides step-by-step instructions for uploading PDF documents to Azure AI Search to use in the Grant Compliance Demo application.

## Overview

The system uses Azure AI Search as a knowledge base to store and retrieve executive orders and compliance documents. PDFs are processed with Azure Document Intelligence (OCR) and indexed for semantic search.

---

## Prerequisites

Before uploading PDFs, ensure you have:

### 1. Azure Resources Created

```bash
# Azure AI Search
az search service create \
  --name your-search-service \
  --resource-group your-rg \
  --sku basic \
  --location eastus

# Azure Document Intelligence
az cognitiveservices account create \
  --name your-doc-intelligence \
  --resource-group your-rg \
  --kind FormRecognizer \
  --sku S0 \
  --location eastus
```

### 2. Environment Variables Configured

Update your `.env` file with one of the following authentication methods:

**Option A: Managed Identity / Entra ID (Recommended for Production)**

```env
# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_INDEX_NAME=grant-compliance-index

# Use Managed Identity (no API key needed)
USE_MANAGED_IDENTITY=true

# Optional: Specify tenant ID if you have multiple tenants
# Find your tenant ID: az account show --query tenantId -o tsv
AZURE_TENANT_ID=your-tenant-id-here

# Azure Document Intelligence (optional)
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-region.api.cognitive.microsoft.com
# For Document Intelligence, you can also use managed identity or provide a key
AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your_doc_intel_key
```

**Option B: API Key Authentication (For Development)**

```env
# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_INDEX_NAME=grant-compliance-index
AZURE_SEARCH_API_KEY=your_search_admin_key

# Azure Document Intelligence (optional)
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-region.api.cognitive.microsoft.com
AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your_doc_intel_key

# Not using managed identity
USE_MANAGED_IDENTITY=false
```

**Note**: If your Azure Search service has key-based authentication disabled (common in production), you must use Option A.

### 3. Get Azure Credentials

```bash
# Get Search Service Admin Key (required for creating indexes)
az search admin-key show \
  --service-name your-search-service \
  --resource-group your-rg \
  --query "primaryKey" -o tsv

# Get Document Intelligence Key
az cognitiveservices account keys list \
  --name your-doc-intelligence \
  --resource-group your-rg \
  --query "key1" -o tsv
```

**Important**: Use the **Admin key** (not Query key) for index creation and document upload. Query keys only allow read operations.

### 4. Install Required Packages

```bash
# If using pip
uv add azure-search-documents azure-ai-documentintelligence azure-identity PyPDF2 python-dotenv

# If using uv (recommended for this project)
uv add azure-search-documents azure-ai-documentintelligence azure-identity PyPDF2 python-dotenv
```

**Note**: `azure-ai-documentintelligence` is optional. If not installed, the script will fall back to PyPDF2 for text extraction (no OCR support).

---

## Step-by-Step Upload Process

### Step 1: Prepare Your PDF Documents

1. **Organize PDFs in the correct directory**:

```bash
# For Executive Orders (compliance reference documents)
cp /path/to/your/executive_order.pdf knowledge_base/executive_orders/

# or copy to knowledge_base/sample_executive_orders/

# For Grant Guidelines
cp /path/to/your/guideline.pdf knowledge_base/grant_guidelines/
```

2. **Use recommended naming convention (For the purposes of this Demo)**:

```
EO_[NUMBER]_[Description].pdf

Examples:
✅ EO_14008_Climate_Crisis.pdf
✅ EO_14028_Cybersecurity.pdf
✅ EO_13985_Racial_Equity.pdf
```

This helps the system automatically extract metadata.

### Step 2: Verify Azure Connection

Test your Azure credentials before indexing:

```bash
# Test Azure AI Search connection
python -c "
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import os
from dotenv import load_dotenv

load_dotenv()
endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
key = os.getenv('AZURE_SEARCH_API_KEY')
index = os.getenv('AZURE_SEARCH_INDEX_NAME')

client = SearchClient(endpoint, index, AzureKeyCredential(key))
print('✅ Successfully connected to Azure AI Search')
"
```

### Step 3: Create Search Index (First Time Only)

The search index will be automatically created when you run the indexing script for the first time. The script includes index creation logic.

**Alternative Option 1: Create Index via REST API**

```bash
# Set your variables
SEARCH_SERVICE_NAME="your-search-service"
SEARCH_ADMIN_KEY="your-admin-key"
INDEX_NAME="grant-compliance-index"

# Create the index using REST API
curl -X PUT \
  "https://${SEARCH_SERVICE_NAME}.search.windows.net/indexes/${INDEX_NAME}?api-version=2024-07-01" \
  -H "Content-Type: application/json" \
  -H "api-key: ${SEARCH_ADMIN_KEY}" \
  -d '{
  "name": "grant-compliance-index",
  "fields": [
    {"name": "id", "type": "Edm.String", "key": true, "filterable": true, "sortable": true},
    {"name": "title", "type": "Edm.String", "searchable": true, "sortable": true, "analyzer": "en.microsoft"},
    {"name": "content", "type": "Edm.String", "searchable": true, "analyzer": "en.microsoft"},
    {"name": "document_type", "type": "Edm.String", "filterable": true, "sortable": true, "facetable": true},
    {"name": "executive_order_number", "type": "Edm.String", "searchable": true, "filterable": true, "sortable": true, "facetable": true},
    {"name": "effective_date", "type": "Edm.DateTimeOffset", "filterable": true, "sortable": true},
    {"name": "category", "type": "Collection(Edm.String)", "searchable": true, "filterable": true},
    {"name": "keywords", "type": "Collection(Edm.String)", "searchable": true},
    {"name": "compliance_areas", "type": "Collection(Edm.String)", "searchable": true, "filterable": true},
    {"name": "agency", "type": "Edm.String", "filterable": true},
    {"name": "status", "type": "Edm.String", "filterable": true},
    {"name": "summary", "type": "Edm.String", "searchable": true, "analyzer": "en.microsoft"},
    {"name": "chunk_number", "type": "Edm.Int32", "filterable": true, "sortable": true},
    {"name": "total_chunks", "type": "Edm.Int32", "filterable": true, "sortable": true},
    {"name": "content_vector", "type": "Collection(Edm.Single)", "searchable": true, "dimensions": 1536, "vectorSearchProfile": "vector-profile"}
  ],
  "vectorSearch": {
    "profiles": [{"name": "vector-profile", "algorithm": "hnsw-config", "vectorizer": "openai-vectorizer"}],
    "algorithms": [{"name": "hnsw-config", "kind": "hnsw", "hnswParameters": {"metric": "cosine"}}],
    "vectorizers": [{"name": "openai-vectorizer", "kind": "azureOpenAI", "azureOpenAIParameters": {"resourceUri": "https://your-openai-resource.openai.azure.com", "deploymentId": "text-embedding-3-small", "modelName": "text-embedding-3-small"}}]
  },
  "semantic": {
    "configurations": [{"name": "default-semantic-config", "prioritizedFields": {"titleField": {"fieldName": "title"}, "prioritizedContentFields": [{"fieldName": "content"}]}}]
  }
}'
```

**Verify index creation:**
```bash
curl -X GET \
  "https://${SEARCH_SERVICE_NAME}.search.windows.net/indexes/${INDEX_NAME}?api-version=2023-11-01" \
  -H "api-key: ${SEARCH_ADMIN_KEY}"
```

**Alternative Option 2: Create Index via Azure Portal**

1. Navigate to your Search Service in Azure Portal
2. Click "Indexes" → "+ Add index"
3. Manually configure fields based on `config/search_index.json` schema

**Note**: 
- The REST API schema above matches what the Python script creates (simple strings, not collections)
- The `config/search_index.json` file contains a more advanced schema with vector search and semantic configurations that can be used if you manually create the index through the portal

### Step 4: Run the Indexing Script

#### Basic Indexing (Executive Orders)

```bash
python scripts/index_knowledge_base.py \
  --input knowledge_base/executive_orders \
  --type executive_order
```

#### Index Sample Executive Orders (Default)

```bash
# Uses default directory: knowledge_base/sample_executive_orders
python scripts/index_knowledge_base.py
```

#### Index Grant Guidelines

```bash
python scripts/index_knowledge_base.py \
  --input knowledge_base/grant_guidelines \
  --type grant_guideline
```

#### Index Multiple Directories

```bash
# Index sample executive orders
python scripts/index_knowledge_base.py --input knowledge_base/sample_executive_orders --type executive_order

# Index executive orders
python scripts/index_knowledge_base.py --input knowledge_base/executive_orders --type executive_order

# Index guidelines
python scripts/index_knowledge_base.py --input knowledge_base/grant_guidelines --type grant_guideline
```

#### Skip Index Check (if index already exists)

```bash
python scripts/index_knowledge_base.py \
  --input knowledge_base/executive_orders \
  --skip-index-check
```

**Note**: The `--dry-run` flag mentioned in earlier versions is not implemented in the current script.

### Step 5: Verify Upload Success

**Expected Output**:

```
======================================================================
📚 Knowledge Base PDF Indexer
======================================================================

✅ Search index 'grant-compliance-index' already exists

📄 Found 22 PDF files to index
📁 Directory: knowledge_base/executive_orders
🏷️  Document type: executive_order

[1/22] Processing: EO_14008_Climate_Crisis.pdf
  └─ Extracting text...
  └─ Chunking: 25847 chars → 14 chunks (2000 chars, 200 overlap)
  └─ ✅ Successfully processed

[2/22] Processing: EO_14028_Cybersecurity.pdf
  └─ Extracting text...
  └─ Chunking: 18234 chars → 10 chunks (2000 chars, 200 overlap)
  └─ ✅ Successfully processed

[3/22] Processing: EO_13985_Racial_Equity.pdf
  └─ Extracting text...
  └─ Chunking: 22156 chars → 12 chunks (2000 chars, 200 overlap)
  └─ ✅ Successfully processed

...

⬆️  Uploading 109 chunks to Azure AI Search...
✅ Successfully indexed 109/109 chunks from 22 documents

======================================================================
✅ Indexing complete: 22 PDFs → 109 chunks indexed
======================================================================
```

> **Note**: Each PDF is split into chunks of ~2000 characters with 200-character overlap at sentence boundaries. The integrated vectorizer (`text-embedding-3-small`) automatically generates embeddings for each chunk at indexing time — no client-side embedding needed.

If the index doesn't exist, you'll see:
```
⚠️  Index check via search failed, attempting to create...
📝 Creating search index 'grant-compliance-index'...
✅ Index created successfully
```

### Step 6: Verify Documents in Azure Search

Check that documents are searchable:

```bash
# Query Azure AI Search to verify documents
python -c "
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import os
from dotenv import load_dotenv

load_dotenv()
client = SearchClient(
    os.getenv('AZURE_SEARCH_ENDPOINT'),
    os.getenv('AZURE_SEARCH_INDEX_NAME'),
    AzureKeyCredential(os.getenv('AZURE_SEARCH_API_KEY'))
)

results = client.search('executive order', top=5)
for doc in results:
    print(f\"✅ {doc['title']}\")
"
```

Or use Azure Portal:
1. Navigate to your Search Service
2. Click "Search explorer"
3. Run a test search query

---

## Important Schema Notes

**Index Schema**: The `config/search_index.json` file is auto-generated from the live index and includes:

- **Chunking fields**: `chunk_number` (Int32) and `total_chunks` (Int32) track chunk position within source documents
- **Vector field**: `content_vector` (Collection(Edm.Single), 1536 dimensions) — populated automatically by the integrated vectorizer
- **Integrated vectorizer**: `openai-vectorizer` using `text-embedding-3-small` via managed identity (no API key needed)
- **Semantic config**: `default-semantic-config` with title + content prioritized
- **Collection fields**: `category`, `keywords`, and `compliance_areas` are `Collection(Edm.String)` arrays

---

## What the Indexing Script Does

The `index_knowledge_base.py` script performs the following:

1. **Reads PDFs** from the specified directory
2. **Extracts text** using Azure Document Intelligence (with OCR for scanned docs)
3. **Extracts metadata** from filenames (EO numbers, keywords)
4. **Identifies compliance areas** using keyword matching (climate, cybersecurity, equity, etc.)
5. **Chunks text** into ~2000-character segments with 200-character overlap, splitting at sentence boundaries to preserve context
6. **Creates search documents** for each chunk with structured fields:
   - `id`: Unique chunk identifier (`{doc_id}_chunk_{n}`)
   - `title`: Human-readable title (same for all chunks of a document)
   - `content`: Chunk text content
   - `chunk_number`: Zero-based index of this chunk within the document
   - `total_chunks`: Total number of chunks for the source document
   - `document_type`: executive_order, grant_guideline, etc.
   - `executive_order_number`: Extracted EO number
   - `category`: Document categories
   - `keywords`: Extracted keywords
   - `compliance_areas`: Identified compliance topics
   - `summary`: First 500 characters of the full document
7. **Uploads to Azure AI Search** in batch — the integrated vectorizer (`openai-vectorizer` using `text-embedding-3-small`) automatically generates the `content_vector` embedding for each chunk

---

## Using the Knowledge Base in Demo App

Once documents are indexed, they're automatically available in the demo:

### Step 1: Start the Demo App

```bash
./start.sh
```

### Step 2: Upload a Grant Proposal

1. Navigate to **"Document Upload"** page in the React frontend
2. Upload a grant proposal PDF
3. Click **"🚀 Analyze for Compliance"**

### Step 3: View Results

The compliance agent will:
- Query Azure AI Search for relevant executive orders
- Retrieve documents using semantic search
- Analyze grant proposal against knowledge base
- Provide compliance summary with citations

---

## Supported PDF Types

| PDF Type | Supported | Notes |
|----------|-----------|-------|
| **Text-based PDFs** | ✅ Yes | Native digital documents |
| **Scanned PDFs** | ✅ Yes | OCR automatically applied |
| **Form-based PDFs** | ✅ Yes | Form fields extracted |
| **Multi-column layouts** | ✅ Yes | Layout preserved |
| **Tables** | ✅ Yes | Tables extracted as structured data |
| **Handwritten text** | ✅ Yes | Recognized with Document Intelligence |
| **Mixed content** | ✅ Yes | Text, images, and forms |

### File Size Limits

- **Azure Document Intelligence**: Up to 500MB per file
- **Recommended size**: Under 50MB for faster processing
- **Batch processing**: Multiple files can be queued

---

## Troubleshooting

### Error: "Invalid tenant ID" or "You can locate your tenant ID..."

**Problem**: The script is trying to use Managed Identity but doesn't have a valid tenant ID configured.

**Solution**:

1. Find your Azure tenant ID:
```bash
az account show --query tenantId -o tsv
```

2. Add it to your `.env` file:
```env
AZURE_TENANT_ID=00000000-0000-0000-0000-000000000000
USE_MANAGED_IDENTITY=true
```

3. Login with the correct tenant:
```bash
az login --tenant your-tenant-id
```

4. Run the script again:
```bash
python scripts/index_knowledge_base.py --input knowledge_base/executive_orders
```

### Error: "AuthenticationTypeDisabled" or "Key based authentication is disabled"

**Problem**: Your Azure Search service has key-based authentication disabled and requires Managed Identity or Entra ID authentication.

**Solution 1: Use Managed Identity** (Recommended for production)

1. Update your `.env` file:
```env
USE_MANAGED_IDENTITY=true
# Remove or comment out AZURE_SEARCH_API_KEY
```

2. Authenticate with Azure:
```bash
# If running locally
az login

# If running in Azure (VM, App Service, Container Instance, etc.)
# Managed Identity will be automatically detected
```

3. Assign the required role to your identity:
```bash
# Get your user principal ID (for local development)
USER_ID=$(az ad signed-in-user show --query id -o tsv)

# Or get your managed identity principal ID (for Azure resources)
# MANAGED_IDENTITY_ID=$(az identity show --name your-identity --resource-group your-rg --query principalId -o tsv)

# Assign Search Index Data Contributor role
az role assignment create \
  --assignee $USER_ID \
  --role "Search Index Data Contributor" \
  --scope /subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RG/providers/Microsoft.Search/searchServices/YOUR_SEARCH_SERVICE

# Assign Search Service Contributor role (for index creation)
az role assignment create \
  --assignee $USER_ID \
  --role "Search Service Contributor" \
  --scope /subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RG/providers/Microsoft.Search/searchServices/YOUR_SEARCH_SERVICE
```

4. Run the script:
```bash
python scripts/index_knowledge_base.py --input knowledge_base/executive_orders
```

**Solution 2: Enable Key-Based Authentication** (For development/testing)

1. Go to Azure Portal → Your Search Service
2. Navigate to Settings → Keys
3. Under "API Access Control", enable "Both" or "API Keys"
4. Copy the Admin Key
5. Update your `.env` file:
```env
AZURE_SEARCH_API_KEY=your_admin_key_here
USE_MANAGED_IDENTITY=false
```

### Error: "Azure AI Search not configured"

**Solution**: Check your `.env` file has required variables:
```env
AZURE_SEARCH_ENDPOINT=https://your-service.search.windows.net
AZURE_SEARCH_INDEX_NAME=grant-compliance-index
AZURE_SEARCH_API_KEY=your_key
```

### Error: "Index does not exist"

**Solution 1**: Let the script create the index automatically (recommended):
```bash
python scripts/index_knowledge_base.py --input knowledge_base/executive_orders
```

**Solution 2**: Create the index manually via REST API (see Step 3 above)

**Solution 3**: Create via Azure Portal:
- Navigate to your Search Service → Indexes → Add index

### Error: "403 Forbidden" when creating index via REST

**Solution**: Ensure you're using an **Admin key**, not a Query key:
```bash
# Get the correct admin key
az search admin-key show \
  --service-name your-search-service \
  --resource-group your-rg \
  --query "primaryKey" -o tsv
```

Query keys only allow search operations, not index creation or document upload.

### Error: "Document Intelligence authentication failed"

**Solution**: Verify Document Intelligence credentials:
```bash
# Get new keys
az cognitiveservices account keys list \
  --name your-doc-intelligence \
  --resource-group your-rg
```

### Fallback to PyPDF2

If Document Intelligence is not configured, the script automatically falls back to PyPDF2:

```
⚠️  Azure Document Intelligence not configured. Will extract text using PyPDF2.
```

**Note**: PyPDF2 has limitations:
- No OCR for scanned documents
- Basic text extraction only
- No layout or form recognition

### Documents Not Appearing in Search

1. **Verify upload succeeded**: Check script output for errors
2. **Wait for indexing**: Azure Search indexing can take 1-2 minutes
3. **Check index configuration**: Ensure fields are searchable
4. **Test with Azure Portal**: Use Search Explorer to verify

---

## Advanced Options

### View All Command-Line Arguments

```bash
python scripts/index_knowledge_base.py --help
```

Available arguments:
- `--input`: Directory containing PDF files (default: `knowledge_base/sample_executive_orders`)
- `--type`: Document type - choices: `executive_order`, `grant_guideline`, `policy`, `regulation` (default: `executive_order`)
- `--skip-index-check`: Skip index existence check (use if index already verified to exist)

### Custom Document Types

```bash
python scripts/index_knowledge_base.py \
  --input /path/to/documents \
  --type policy  # Options: executive_order, grant_guideline, policy, regulation
```

### Batch Processing Multiple Directories

```bash
#!/bin/bash
# Index all knowledge base directories

python scripts/index_knowledge_base.py --input knowledge_base/sample_executive_orders --type executive_order
python scripts/index_knowledge_base.py --input knowledge_base/executive_orders --type executive_order
python scripts/index_knowledge_base.py --input knowledge_base/grant_guidelines --type grant_guideline

# If you have additional directories:
# python scripts/index_knowledge_base.py --input knowledge_base/sample_proposals --type grant_guideline
```

### Update Existing Documents

To update documents already in the index:

1. Delete the old document:
```bash
python -c "
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import os
from dotenv import load_dotenv

load_dotenv()
client = SearchClient(
    os.getenv('AZURE_SEARCH_ENDPOINT'),
    os.getenv('AZURE_SEARCH_INDEX_NAME'),
    AzureKeyCredential(os.getenv('AZURE_SEARCH_API_KEY'))
)

# Delete document by ID (ID must match the one created by script)
result = client.delete_documents(documents=[{'id': 'EO_14008_Climate_Crisis'}])
print(f'Deleted: {list(result)}')
"
```

2. Re-run indexing script with updated PDF

**Note**: Document IDs are generated from filenames with special characters removed. For `EO_14008_Climate_Crisis.pdf`, the ID would be `EO_14008_Climate_Crisis`.

### REST API Operations

You can also manage the search index using the Azure Search REST API:

**List all indexes:**
```bash
curl -X GET \
  "https://${SEARCH_SERVICE_NAME}.search.windows.net/indexes?api-version=2023-11-01" \
  -H "api-key: ${SEARCH_ADMIN_KEY}"
```

**Get index statistics:**
```bash
curl -X GET \
  "https://${SEARCH_SERVICE_NAME}.search.windows.net/indexes/${INDEX_NAME}/stats?api-version=2023-11-01" \
  -H "api-key: ${SEARCH_ADMIN_KEY}"
```

**Delete the index:**
```bash
curl -X DELETE \
  "https://${SEARCH_SERVICE_NAME}.search.windows.net/indexes/${INDEX_NAME}?api-version=2023-11-01" \
  -H "api-key: ${SEARCH_ADMIN_KEY}"
```

**Search documents via REST:**
```bash
curl -X POST \
  "https://${SEARCH_SERVICE_NAME}.search.windows.net/indexes/${INDEX_NAME}/docs/search?api-version=2023-11-01" \
  -H "Content-Type: application/json" \
  -H "api-key: ${SEARCH_ADMIN_KEY}" \
  -d '{
    "search": "executive order climate",
    "top": 5,
    "select": "id,title,executive_order_number"
  }'
```

For more REST API operations, see the [Azure Search REST API documentation](https://learn.microsoft.com/rest/api/searchservice/).

### Monitor Indexing Progress

For large batches, monitor progress:

```bash
# Run with verbose output
python scripts/index_knowledge_base.py \
  --input knowledge_base/executive_orders 2>&1 | tee indexing.log
```

---

## Best Practices

### 1. Document Naming
- Use consistent naming: `EO_[NUMBER]_[Description].pdf`
- Include document numbers for automatic metadata extraction
- Use underscores instead of spaces

### 2. Document Organization
- Keep executive orders separate from guidelines
- Organize by category or topic when possible
- Remove duplicate or outdated documents before indexing

### 3. Batch Uploads
- Index documents in batches of 50-100 for optimal performance
- Monitor for errors and re-run failed batches
- Use dry-run mode to test before uploading

### 4. Content Quality
- Ensure PDFs are not password-protected
- Use high-quality scans (300 DPI or higher) for OCR
- Verify extracted text quality after indexing

### 5. Maintenance
- Regularly update knowledge base with new executive orders
- Remove obsolete documents from index
- Re-index documents when metadata changes

---

## Next Steps

After uploading PDFs to Azure AI Search:

1. **Test the Application**:
   ```bash
   ./start.sh
   ```

2. **Upload Grant Proposals**: Test compliance analysis with real proposals

3. **Review Results**: Verify citations reference your uploaded documents

4. **Iterate**: Add more executive orders and refine compliance areas

---

## Additional Resources

- [Azure AI Search Documentation](https://learn.microsoft.com/azure/search/)
- [Azure Document Intelligence Documentation](https://learn.microsoft.com/azure/ai-services/document-intelligence/)
- [Project README](../README.md)
- [PDF Processing Guide](PDF_GUIDE.md)

---

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review script output logs for error messages
3. Verify Azure resource configuration in Azure Portal
4. Open an issue in the project repository

---

**Last Updated**: December 2025
**Verified**: CLI commands and script arguments verified against actual implementation
