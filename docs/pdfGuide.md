# PDF Document Processing Guide

## Overview

This comprehensive guide explains how to add and process PDF documents in the Grant Compliance Automation system. The system handles two types of PDFs:

1. **Knowledge Base PDFs**: Executive orders and compliance documents used as reference
2. **Grant Proposal PDFs**: Documents that need compliance review

**Related Documentation:**
- [Quick Reference Card](pdfQuickReference.md) - One-page command reference
- [Azure Search Upload Guide](uploadPdfsToAzureSearch.md) - Detailed Azure indexing steps

## Adding PDF Documents

### Knowledge Base Documents (Executive Orders)

Place your executive order PDFs in the knowledge base directory:

```bash
# Navigate to project root
cd foundry-grant-eo-validation-demo

# Copy your PDF executive orders
cp /path/to/your/executive_order.pdf knowledge_base/sample_executive_orders/

# Example:
cp ~/Downloads/EO_14057_Federal_Sustainability.pdf knowledge_base/sample_executive_orders/
```

**File Naming Convention** (recommended):
```
EO_[NUMBER]_[Short_Description].pdf

Examples:
- EO_14008_Climate_Crisis.pdf
- EO_14028_Cybersecurity.pdf
- EO_13985_Racial_Equity.pdf
```

### Grant Proposal PDFs for Review

Place grant proposals in the sample proposals directory:

```bash
# Copy grant proposal PDFs
cp /path/to/your/grant_proposal.pdf knowledge_base/sample_proposals/

# Example:
cp ~/Downloads/Housing_Grant_Application.pdf knowledge_base/sample_proposals/
```

**Current Directory Structure**:
```
knowledge_base/
├── executive_orders/
│   ├── EO_14008_Climate_Crisis.txt     # Sample text version
│   ├── EO_14028_Cybersecurity.txt      # Sample text version
│   ├── EO_13985_Racial_Equity.txt      # Sample text version
│   └── [Your PDF files go here]        # Add your PDFs
├── grant_guidelines/
│   ├── County_Grant_Compliance_Guidelines.txt
│   └── [Your policy PDFs go here]
└── sample_proposals/
    └── [Your grant proposal PDFs go here]
```

## Processing PDF Documents

### Demo Mode (No Azure Required)

In demo mode, the system works with sample data embedded in the Streamlit app:

```bash
# Just run the demo
streamlit run app/streamlit_app.py
```

For PDFs in demo mode:
1. Go to "📝 Document Upload" page
2. Use file uploader to select your PDF
3. System will extract text using PyPDF2 (basic extraction)
4. Analysis proceeds with extracted text

**Limitations in Demo Mode**:
- Basic text extraction only (no OCR for scanned documents)
- No layout analysis or form recognition
- Limited to text-based PDFs

### Production Mode (With Azure Services)

#### Step 1: Set Up Azure Document Intelligence

1. Create Azure Document Intelligence resource:
```bash
az cognitiveservices account create \
  --name your-doc-intelligence \
  --resource-group your-rg \
  --kind FormRecognizer \
  --sku S0 \
  --location eastus
```

2. Get credentials:
```bash
az cognitiveservices account keys list \
  --name your-doc-intelligence \
  --resource-group your-rg
```

3. Update `.env`:
```env
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-region.api.cognitive.microsoft.com
AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your_key_here
```

#### Step 2: Index Knowledge Base PDFs

Index your executive order PDFs to Azure AI Search:

```bash
# Basic indexing
python scripts/index_knowledge_base.py \
  --input knowledge_base/executive_orders

# With custom document type
python scripts/index_knowledge_base.py \
  --input knowledge_base/grant_guidelines \
  --type grant_guideline

# Dry run (test without uploading)
python scripts/index_knowledge_base.py \
  --input knowledge_base/executive_orders \
  --dry-run
```

**What the script does**:
1. Reads all PDFs from the specified directory
2. Extracts text using Azure Document Intelligence (or PyPDF2 as fallback)
3. Extracts metadata from filenames
4. Identifies compliance areas using keyword matching
5. Uploads documents to Azure AI Search index

**Expected Output**:
```
======================================================================
📚 Knowledge Base PDF Indexer
======================================================================

📄 Found 5 PDF files to index
📁 Directory: knowledge_base/executive_orders
🏷️  Document type: executive_order

[1/5] Processing: EO_14008_Climate_Crisis.pdf
  └─ Extracting text...
  └─ Creating search document...
  └─ ✅ Successfully processed (25847 characters)

[2/5] Processing: EO_14028_Cybersecurity.pdf
  └─ Extracting text...
  └─ Creating search document...
  └─ ✅ Successfully processed (18234 characters)

...

⬆️  Uploading 5 documents to Azure AI Search...
✅ Successfully indexed 5/5 documents

======================================================================
✅ Indexing complete: 5 documents indexed
======================================================================
```

#### Step 3: Process Grant Proposal PDFs

For analyzing grant proposals:

1. **Via Streamlit Upload**:
   - Run app: `streamlit run app/streamlit_app.py`
   - Navigate to "📝 Document Upload"
   - Upload PDF directly
   - System automatically extracts text with Azure Document Intelligence

2. **Via SharePoint** (Production):
   - Upload to configured SharePoint library
   - Azure Function App triggers processing
   - Document Intelligence extracts text
   - Compliance agent analyzes automatically

3. **Via Email** (Production):
   - Email PDF to configured address
   - Azure Function App receives and processes
   - Stores in SharePoint
   - Triggers compliance analysis

## PDF Processing Capabilities

### Azure Document Intelligence Features

When connected to Azure services, PDFs are processed with:

**OCR (Optical Character Recognition)**:
- ✅ Scanned documents converted to searchable text
- ✅ Handwritten text recognition
- ✅ Multi-language support
- ✅ High accuracy even with poor image quality

**Layout Analysis**:
- ✅ Document structure identification (headings, sections, paragraphs)
- ✅ Table extraction with cell values
- ✅ Reading order detection
- ✅ Column and page layout preservation

**Form Recognition**:
- ✅ Key-value pair extraction (e.g., "Grant Amount: $500,000")
- ✅ Checkbox and selection field detection
- ✅ Signature region identification
- ✅ Custom form models (trainable)

**Content Extraction**:
- ✅ Text with position coordinates
- ✅ Metadata (page numbers, fonts, etc.)
- ✅ Embedded images and figures
- ✅ Document properties (author, date, etc.)

### Supported PDF Types

| PDF Type | Demo Mode | Production Mode |
|----------|-----------|-----------------|
| Text-based PDFs | ✅ Basic extraction | ✅ Full extraction |
| Scanned PDFs | ❌ Limited | ✅ OCR applied |
| Form-based PDFs | ⚠️ Text only | ✅ Form recognition |
| Mixed content | ⚠️ Text only | ✅ Full analysis |
| Multi-column | ⚠️ Basic | ✅ Layout preserved |
| Tables | ❌ No | ✅ Table extraction |
| Handwritten | ❌ No | ✅ Recognized |

### File Size Limits

- **Demo Mode**: Up to 10MB per file
- **Azure Document Intelligence**: Up to 500MB per file
- **Batch Processing**: Multiple documents can be queued

## Batch Processing

To process multiple PDFs at once:

```bash
# Process all executive orders
python scripts/index_knowledge_base.py \
  --input knowledge_base/executive_orders

# Process all grant guidelines
python scripts/index_knowledge_base.py \
  --input knowledge_base/grant_guidelines \
  --type grant_guideline

# Process custom directory
python scripts/index_knowledge_base.py \
  --input /path/to/your/pdfs \
  --type policy
```

## Troubleshooting

### PDF Text Extraction Issues

**Problem**: Extracted text is garbled or empty
- **Solution**: Ensure PDF is not password-protected or corrupted
- **Check**: Try opening PDF in a viewer first
- **Alternative**: Use Azure Document Intelligence for better OCR

**Problem**: Scanned PDF shows no text
- **Solution**: Demo mode doesn't support OCR; use Azure Document Intelligence
- **Workaround**: Convert scanned PDF to text-based using online tools

**Problem**: Tables are not extracted correctly
- **Solution**: Azure Document Intelligence required for table extraction
- **Note**: Demo mode only extracts raw text

### Indexing Errors

**Problem**: "Azure AI Search not configured"
- **Solution**: Check `.env` file has `AZURE_SEARCH_ENDPOINT` and credentials
- **Verify**: Run `python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('AZURE_SEARCH_ENDPOINT'))"`

**Problem**: "Document Intelligence endpoint not found"
- **Solution**: Set `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` in `.env`
- **Note**: Script will fallback to PyPDF2 but with limited capabilities

**Problem**: Upload fails with "Index not found"
- **Solution**: Create index first using Azure portal or provided schema
- **Schema**: Use `config/search_index.json` as template

## Best Practices

### File Organization

1. **Use descriptive filenames**:
   - Good: `EO_14008_Climate_Action_Jan2021.pdf`
   - Bad: `document1.pdf`

2. **Organize by type**:
   ```
   knowledge_base/
   ├── executive_orders/     # Federal executive orders
   ├── grant_guidelines/     # Agency-specific policies
   └── sample_proposals/     # Grant applications
   ```

3. **Keep originals**:
   - Store original PDFs separately
   - Never modify source documents
   - Maintain version history if documents are updated

### Quality Checks

Before indexing PDFs:
- ✅ Verify PDF opens correctly
- ✅ Check for password protection (remove if present)
- ✅ Ensure text is selectable (for text-based PDFs)
- ✅ Review file size (compress if over 50MB)
- ✅ Confirm document is complete (all pages present)

### Security Considerations

- 🔒 Never commit PDFs with sensitive information to Git
- 🔒 Use `.gitignore` to exclude PDF directories
- 🔒 Store credentials in `.env`, never in code
- 🔒 Use Managed Identity in production (no keys in config)

## Additional Resources

- [Azure Document Intelligence Documentation](https://learn.microsoft.com/azure/ai-services/document-intelligence/)
- [Azure AI Search PDF Indexing](https://learn.microsoft.com/azure/search/)
- [PyPDF2 Documentation](https://pypdf2.readthedocs.io/) (for demo mode)

## Questions?

- Check [README.md](../README.md) for general setup
- Review [PROJECT_STATUS.md](../PROJECT_STATUS.md) for feature status
- Open an issue for bugs or feature requests
