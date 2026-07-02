# Document Ingestion Guide

> How to add, process, and index documents in the Grant Compliance system.

---

## Quick Reference

```bash
# Add executive orders to knowledge base
cp your_executive_order.pdf knowledge_base/executive_orders/

# Add grant proposals for review
cp your_grant_proposal.pdf knowledge_base/sample_proposals/

# Index to Azure AI Search (production)
python scripts/index_knowledge_base.py --input knowledge_base/executive_orders

# Or just upload via UI (demo or production)
./start.sh   # then go to http://localhost:3000 → Document Upload
```

---

## Document Types

The system handles two types of documents:

| Type | Purpose | Directory | Indexed to Search? |
|------|---------|-----------|-------------------|
| **Knowledge Base** (Executive Orders, Guidelines) | Reference documents for compliance checking | `knowledge_base/executive_orders/` or `knowledge_base/grant_guidelines/` | Yes — must be indexed |
| **Grant Proposals** | Documents to analyze for compliance | `knowledge_base/sample_proposals/` or uploaded via UI | No — processed on-the-fly |

### Directory Structure

```
knowledge_base/
├── executive_orders/          ← Executive order PDFs (indexed to Azure AI Search)
├── grant_guidelines/          ← Policy/guideline PDFs (indexed to Azure AI Search)
├── sample_executive_orders/   ← Pre-loaded samples for demo
└── sample_proposals/          ← Grant proposals for review
```

### File Naming Convention

```
EO_[NUMBER]_[Short_Description].pdf

Examples:
- EO_14008_Climate_Crisis.pdf
- EO_14028_Cybersecurity.pdf
- EO_13985_Racial_Equity.pdf
```

---

## Processing Modes

### Demo Mode (No Azure Required)

```bash
./start.sh
# Upload via React UI → Document Upload → Choose file → Analyze
```

- Uses PyPDF2 for text extraction (basic)
- No OCR for scanned documents
- No layout/table analysis
- Works with text-based PDFs only

### Production Mode (Azure Services)

Full capabilities with Azure Document Intelligence:

| PDF Type | Demo Mode | Production Mode |
|----------|-----------|-----------------|
| Text-based PDF | ✅ Basic | ✅ Full |
| Scanned PDF | ❌ No OCR | ✅ OCR applied |
| Forms | ⚠️ Text only | ✅ Field extraction |
| Tables | ❌ No | ✅ Structured extraction |
| Multi-column | ⚠️ Basic | ✅ Layout preserved |
| Handwritten | ❌ No | ✅ Recognized |

**File size limits**: Up to 500MB per file (Azure Document Intelligence), 10MB in demo mode.

---

## Indexing Knowledge Base to Azure AI Search

### Prerequisites

```bash
# Required Azure resources
az search service create --name your-search-service --resource-group your-rg --sku basic --location eastus
az cognitiveservices account create --name your-doc-intelligence --resource-group your-rg --kind FormRecognizer --sku S0 --location eastus
```

### Environment Configuration

**Option A: Managed Identity (Recommended)**

```env
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_INDEX_NAME=grant-compliance-index
USE_MANAGED_IDENTITY=true
AZURE_TENANT_ID=your-tenant-id
```

**Option B: API Keys (Development)**

```env
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_INDEX_NAME=grant-compliance-index
AZURE_SEARCH_API_KEY=your_admin_key
USE_MANAGED_IDENTITY=false
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-region.api.cognitive.microsoft.com
AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your_key
```

### Run the Indexing Script

```bash
# Index executive orders
python scripts/index_knowledge_base.py --input knowledge_base/executive_orders --type executive_order

# Index grant guidelines
python scripts/index_knowledge_base.py --input knowledge_base/grant_guidelines --type grant_guideline

# Index sample executive orders (default)
python scripts/index_knowledge_base.py

# Skip index check (if index already verified)
python scripts/index_knowledge_base.py --input knowledge_base/executive_orders --skip-index-check
```

**Available arguments:**
- `--input`: Directory containing PDF files (default: `knowledge_base/sample_executive_orders`)
- `--type`: Document type — `executive_order`, `grant_guideline`, `policy`, `regulation`
- `--skip-index-check`: Skip index existence check

### What the Script Does

1. Reads all PDFs from the specified directory
2. Extracts text using Azure Document Intelligence (or PyPDF2 fallback)
3. Extracts metadata from filenames (EO numbers, keywords)
4. Identifies compliance areas via keyword matching
5. Chunks text into ~2000-character segments with 200-character overlap at sentence boundaries
6. Uploads chunks to Azure AI Search in batch
7. The integrated vectorizer (`text-embedding-3-small`) generates embeddings automatically

### Expected Output

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

...

⬆️  Uploading 109 chunks to Azure AI Search...
✅ Successfully indexed 109/109 chunks from 22 documents

======================================================================
✅ Indexing complete: 22 PDFs → 109 chunks indexed
======================================================================
```

### Verify Index

```bash
python scripts/verify_azure_search.py
```

Or via Azure Portal: Search Service → Search Explorer → test a query.

---

## Search Index Schema

The index (`config/search_index.json`) includes:

| Field | Type | Purpose |
|-------|------|---------|
| `id` | String (key) | Unique chunk identifier `{doc_id}_chunk_{n}` |
| `title` | String | Human-readable document title |
| `content` | String | Chunk text content |
| `content_vector` | Collection(Single) | 1536-dim embedding (auto-generated by integrated vectorizer) |
| `chunk_number` | Int32 | Zero-based chunk index |
| `total_chunks` | Int32 | Total chunks for the source document |
| `document_type` | String | executive_order, grant_guideline, etc. |
| `executive_order_number` | String | Extracted EO number |
| `compliance_areas` | Collection(String) | Identified compliance topics |
| `category` | Collection(String) | Document categories |
| `keywords` | Collection(String) | Extracted keywords |

**Semantic config**: `default-semantic-config` with title + content prioritized.

### Create Index Manually (if needed)

The indexing script creates the index automatically. If you need to create it manually:

```bash
SEARCH_SERVICE_NAME="your-search-service"
SEARCH_ADMIN_KEY="your-admin-key"
INDEX_NAME="grant-compliance-index"

curl -X PUT \
  "https://${SEARCH_SERVICE_NAME}.search.windows.net/indexes/${INDEX_NAME}?api-version=2024-07-01" \
  -H "Content-Type: application/json" \
  -H "api-key: ${SEARCH_ADMIN_KEY}" \
  -d @config/search_index.json
```

---

## RBAC for Managed Identity

If using Managed Identity (key-based auth disabled), assign these roles:

```bash
USER_ID=$(az ad signed-in-user show --query id -o tsv)

# Read/write documents to the index
az role assignment create \
  --assignee $USER_ID \
  --role "Search Index Data Contributor" \
  --scope /subscriptions/SUB_ID/resourceGroups/RG/providers/Microsoft.Search/searchServices/YOUR_SEARCH

# Create/manage indexes
az role assignment create \
  --assignee $USER_ID \
  --role "Search Service Contributor" \
  --scope /subscriptions/SUB_ID/resourceGroups/RG/providers/Microsoft.Search/searchServices/YOUR_SEARCH
```

---

## Troubleshooting

### "No text extracted from PDF"
- **Cause**: Scanned PDF without OCR
- **Fix**: Configure Azure Document Intelligence, or convert to text-based PDF

### "Azure AI Search not configured"
- **Fix**: Check `.env` has `AZURE_SEARCH_ENDPOINT` and either `AZURE_SEARCH_API_KEY` or `USE_MANAGED_IDENTITY=true`

### "Invalid tenant ID"
- **Fix**: Run `az account show --query tenantId -o tsv` and add to `.env` as `AZURE_TENANT_ID`

### "AuthenticationTypeDisabled" / "Key based authentication is disabled"
- **Fix**: Use Managed Identity (set `USE_MANAGED_IDENTITY=true`, remove API key) and assign RBAC roles above

### "Index does not exist"
- **Fix**: Run the indexing script — it creates the index automatically on first run

### "403 Forbidden" when creating index
- **Fix**: Use an **Admin key** (not Query key): `az search admin-key show --service-name NAME --resource-group RG`

### Documents not appearing in search
1. Check script output for upload errors
2. Wait 1-2 minutes for Azure Search indexing
3. Verify fields are marked `searchable` in index schema
4. Test in Azure Portal → Search Explorer

### Fallback to PyPDF2

If Document Intelligence is not configured, the script falls back to PyPDF2 automatically:
```
⚠️  Azure Document Intelligence not configured. Will extract text using PyPDF2.
```
Limitations: No OCR, no layout/form recognition, basic text extraction only.

---

## Batch Processing

```bash
#!/bin/bash
# Index all knowledge base directories
python scripts/index_knowledge_base.py --input knowledge_base/sample_executive_orders --type executive_order
python scripts/index_knowledge_base.py --input knowledge_base/executive_orders --type executive_order
python scripts/index_knowledge_base.py --input knowledge_base/grant_guidelines --type grant_guideline
```

## Update Existing Documents

To re-index updated documents, simply re-run the indexing script — it uses merge-or-upload semantics, so existing documents with the same ID will be updated.
