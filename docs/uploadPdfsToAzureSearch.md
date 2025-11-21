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

Update your `.env` file:

```env
# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_INDEX_NAME=grant-compliance-index
AZURE_SEARCH_API_KEY=your_search_key

# Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-region.api.cognitive.microsoft.com
AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your_doc_intel_key

# Or use Managed Identity (recommended for production)
USE_MANAGED_IDENTITY=true
```

### 3. Get Azure Credentials

```bash
# Get Search Service Key
az search admin-key show \
  --service-name your-search-service \
  --resource-group your-rg

# Get Document Intelligence Key
az cognitiveservices account keys list \
  --name your-doc-intelligence \
  --resource-group your-rg
```

### 4. Install Required Packages

```bash
uv pip install azure-search-documents azure-ai-documentintelligence PyPDF2 python-dotenv
```

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

The search index must be created before uploading documents:

```bash
# The index configuration is in config/search_index.json
# Create index using Azure CLI or Portal

az search index create \
  --service-name your-search-service \
  --name grant-compliance-index \
  --fields @config/search_index.json
```

Or use the Azure Portal:
1. Navigate to your Search Service
2. Click "Indexes" → "+ Add index"
3. Import schema from `config/search_index.json`

### Step 4: Run the Indexing Script

#### Basic Indexing (Executive Orders)

```bash
python scripts/index_knowledge_base.py \
  --input knowledge_base/executive_orders \
  --type executive_order
```

#### Index Grant Guidelines

```bash
python scripts/index_knowledge_base.py \
  --input knowledge_base/grant_guidelines \
  --type grant_guideline
```

#### Index Multiple Directories

```bash
# Index executive orders
python scripts/index_knowledge_base.py --input knowledge_base/executive_orders

# Index guidelines
python scripts/index_knowledge_base.py --input knowledge_base/grant_guidelines
```

#### Dry Run (Test Without Uploading)

```bash
python scripts/index_knowledge_base.py \
  --input knowledge_base/executive_orders \
  --dry-run
```

### Step 5: Verify Upload Success

**Expected Output**:

```
======================================================================
📚 Knowledge Base PDF Indexer
======================================================================

📄 Found 3 PDF files to index
📁 Directory: knowledge_base/executive_orders
🏷️  Document type: executive_order

[1/3] Processing: EO_14008_Climate_Crisis.pdf
  └─ Extracting text with Azure Document Intelligence...
  └─ Creating search document...
  └─ ✅ Successfully processed (25,847 characters)

[2/3] Processing: EO_14028_Cybersecurity.pdf
  └─ Extracting text with Azure Document Intelligence...
  └─ Creating search document...
  └─ ✅ Successfully processed (18,234 characters)

[3/3] Processing: EO_13985_Racial_Equity.pdf
  └─ Extracting text with Azure Document Intelligence...
  └─ Creating search document...
  └─ ✅ Successfully processed (22,156 characters)

⬆️  Uploading 3 documents to Azure AI Search...
✅ Successfully indexed 3/3 documents

======================================================================
✅ Indexing complete: 3 documents indexed
======================================================================
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

## What the Indexing Script Does

The `index_knowledge_base.py` script performs the following:

1. **Reads PDFs** from the specified directory
2. **Extracts text** using Azure Document Intelligence (with OCR for scanned docs)
3. **Extracts metadata** from filenames (EO numbers, keywords)
4. **Identifies compliance areas** using keyword matching (climate, cybersecurity, equity, etc.)
5. **Creates search documents** with structured fields:
   - `id`: Unique document identifier
   - `title`: Human-readable title
   - `content`: Full text content
   - `document_type`: executive_order, grant_guideline, etc.
   - `executive_order_number`: Extracted EO number
   - `category`: Document categories
   - `keywords`: Extracted keywords
   - `compliance_areas`: Identified compliance topics
   - `summary`: First 500 characters
6. **Uploads to Azure AI Search** in batch

---

## Using the Knowledge Base in Demo App

Once documents are indexed, they're automatically available in the demo:

### Step 1: Start the Demo App

```bash
streamlit run app/streamlit_app.py
```

### Step 2: Upload a Grant Proposal

1. Navigate to **"📝 Document Upload"** page
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

### Error: "Azure AI Search not configured"

**Solution**: Check your `.env` file has required variables:
```env
AZURE_SEARCH_ENDPOINT=https://your-service.search.windows.net
AZURE_SEARCH_INDEX_NAME=grant-compliance-index
AZURE_SEARCH_API_KEY=your_key
```

### Error: "Index does not exist"

**Solution**: Create the search index first:
```bash
az search index create \
  --service-name your-search-service \
  --name grant-compliance-index
```

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

python scripts/index_knowledge_base.py --input knowledge_base/executive_orders --type executive_order
python scripts/index_knowledge_base.py --input knowledge_base/grant_guidelines --type grant_guideline
python scripts/index_knowledge_base.py --input knowledge_base/policies --type policy
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

# Delete document by ID
client.delete_documents(documents=[{'id': 'EO_14008_Climate_Crisis'}])
"
```

2. Re-run indexing script with updated PDF

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

1. **Test the Demo App**:
   ```bash
   streamlit run app/streamlit_app.py
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

**Last Updated**: November 2025
