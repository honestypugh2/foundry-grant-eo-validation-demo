# PDF Quick Reference Card

## 📄 Adding PDFs to Your Project

### Knowledge Base Documents (Executive Orders)
```bash
# Place your PDFs here:
cp your_executive_order.pdf knowledge_base/executive_orders/

# File naming (recommended):
EO_[NUMBER]_[Description].pdf
# Example: EO_14008_Climate_Crisis.pdf
```

### Grant Proposals for Review
```bash
# Place your PDFs here:
cp your_grant_proposal.pdf knowledge_base/sample_proposals/

# Any descriptive filename works:
# Example: Housing_Grant_2024.pdf
```

---

## 🚀 Quick Commands

### Demo Mode (No Azure Setup)
```bash
# Just run the app
streamlit run app/streamlit_app.py

# Upload PDFs through UI:
# Go to "Document Upload" → Upload your PDF → Analyze
```

### Production Mode (With Azure)

**Index Knowledge Base:**
```bash
# Index executive orders
python scripts/index_knowledge_base.py --input knowledge_base/executive_orders

# Index grant guidelines
python scripts/index_knowledge_base.py --input knowledge_base/grant_guidelines --type grant_guideline

# Dry run (test without uploading)
python scripts/index_knowledge_base.py --input knowledge_base/executive_orders --dry-run
```

**Process Grant Proposals:**
```bash
# Via Streamlit:
streamlit run app/streamlit_app.py
# Then upload through the web interface
```

---

## 📋 Supported PDF Types

| Type | Demo Mode | Azure Mode | Notes |
|------|-----------|------------|-------|
| Text-based PDF | ✅ Yes | ✅ Yes | Works everywhere |
| Scanned PDF | ⚠️ Limited | ✅ Yes | Needs Azure OCR |
| Forms | ⚠️ Text only | ✅ Full | Azure extracts fields |
| Tables | ❌ No | ✅ Yes | Azure extracts tables |
| Multi-column | ⚠️ Basic | ✅ Yes | Azure preserves layout |

---

## 🔧 Environment Setup

**Minimum (Demo Mode):**
```env
# No Azure credentials needed!
DEMO_MODE=true
```

**Production (Azure Mode):**
```env
# Required in .env file:
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=your_key
AZURE_SEARCH_INDEX_NAME=grant-compliance-index
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-region.api.cognitive.microsoft.com
AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your_key
```

---

## 📂 Directory Structure

```
knowledge_base/
├── executive_orders/          ← Add executive order PDFs here
│   ├── EO_14008_Climate.pdf
│   ├── EO_14028_Cyber.pdf
│   └── your_eo.pdf           ← Your PDFs
│
├── grant_guidelines/          ← Add policy PDFs here
│   └── your_policies.pdf     ← Your PDFs
│
└── sample_proposals/          ← Add grant proposal PDFs here
    └── your_grant.pdf        ← Your PDFs
```

---

## ⚡ Common Tasks

### 1. Add a New Executive Order
```bash
# Copy PDF to knowledge base
cp EO_14057_Sustainability.pdf knowledge_base/executive_orders/

# Index it (if using Azure)
python scripts/index_knowledge_base.py --input knowledge_base/executive_orders
```

### 2. Review a Grant Proposal
```bash
# Option A: Copy to sample directory
cp Grant_Application.pdf knowledge_base/sample_proposals/

# Option B: Upload through Streamlit UI
streamlit run app/streamlit_app.py
# Navigate to Document Upload → Choose file → Analyze
```

### 3. Batch Process Multiple PDFs
```bash
# Put all PDFs in directory
cp *.pdf knowledge_base/executive_orders/

# Index all at once
python scripts/index_knowledge_base.py --input knowledge_base/executive_orders
```

---

## 🐛 Troubleshooting

### "No text extracted from PDF"
- **Cause**: Scanned PDF without OCR
- **Fix**: Use Azure Document Intelligence or convert PDF to text-based

### "Azure Search not configured"
- **Cause**: Missing .env configuration
- **Fix**: Copy .env.example to .env and add your Azure credentials

### "PDF upload fails"
- **Cause**: File too large (>10MB in demo mode)
- **Fix**: Compress PDF or use Azure mode (supports up to 500MB)

### "Index not found"
- **Cause**: Azure AI Search index doesn't exist
- **Fix**: Create index using config/search_index.json schema

---

## 📚 More Help

- **Full Guide**: [docs/PDF_GUIDE.md](docs/PDF_GUIDE.md)
- **Setup Guide**: [QUICKSTART.md](QUICKSTART.md)
- **Main Docs**: [README.md](README.md)

---

## 💡 Tips

1. **File Naming**: Use descriptive names with underscores
   - Good: `EO_14008_Climate_Action.pdf`
   - Bad: `document1.pdf`

2. **Size**: Keep PDFs under 50MB for best performance
   - Compress large files before uploading
   - Split very large documents if needed

3. **Quality**: Ensure PDFs are readable
   - Test opening in a PDF viewer first
   - Check that text is selectable (for text-based PDFs)

4. **Organization**: Group similar documents
   - All executive orders in `executive_orders/`
   - All grant applications in `sample_proposals/`
   - All policies in `grant_guidelines/`

---

**Need More Help?** See [docs/PDF_GUIDE.md](docs/PDF_GUIDE.md) for comprehensive documentation.
