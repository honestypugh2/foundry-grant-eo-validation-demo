# Streamlit Application

This directory contains the Streamlit-based user interface for the Grant Compliance Automation Demo.

## 🚀 Application

### `streamlit_app.py` ✅ **PRODUCTION VERSION**

The **current, production-ready** Streamlit application with real Azure AI agent integration.

**Features:**
- ✅ Real Azure AI agent integration via `AgentOrchestrator`
- ✅ Async processing using `asyncio.run()` with `process_grant_proposal_async()`
- ✅ Managed identity authentication by default (`USE_MANAGED_IDENTITY=true`)
- ✅ Document Intelligence SDK (`azure-ai-documentintelligence`)
- ✅ All latest agent code improvements (Dec 2025)
- ✅ Azure AI Search integration for knowledge base
- ✅ Layout matching React frontend (4-page structure)
- ✅ Production-ready error handling and logging

**Run:**
```bash
streamlit run src/app/streamlit_app.py
```

**Navigation:**
- Upload & Analyze - Submit grant proposals for review
- Results Dashboard - View compliance analysis with tabs for Overview, Summary, Compliance, Risk, Email
- Knowledge Base - Browse executive orders and compliance documents
- About - System information and architecture

---

## 📦 Backup Files

### `streamlit_app_legacy_backup.py`

Legacy demo application kept as backup (uses mock data). Not for production use.

---

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables** (`.env` file):
   ```bash
   # Azure AI Services
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_API_KEY=your_api_key
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
   
   # Document Intelligence
   AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
   AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your_api_key
   
   # AI Search
   AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
   AZURE_SEARCH_API_KEY=your_api_key
   AZURE_SEARCH_INDEX_NAME=grant-compliance-index
   
   # Managed Identity (default: true)
   USE_MANAGED_IDENTITY=true
   ```

3. **Run the application:**
   ```bash
   streamlit run src/app/streamlit_app.py
   ```

4. **Access the UI:**
   - Open browser to `http://localhost:8501`

---

## Architecture

```
streamlit_app.py
    ├── AgentOrchestrator (src/agents/orchestrator.py)
    │   ├── DocumentIngestionAgent (azure-ai-documentintelligence)
    │   ├── SummarizationAgent (Azure AI Foundry)
    │   ├── ComplianceAgent (Azure AI Search + OpenAI)
    │   ├── RiskScoringAgent
    │   └── EmailTriggerAgent
    └── Async processing with asyncio.run()
```

---

## Comparison with React Frontend

| Feature | Streamlit | React (Frontend + Backend) |
|---------|-----------|----------------------------|
| Upload Page | ✅ | ✅ |
| Results Dashboard | ✅ | ✅ |
| Knowledge Base | ✅ | ✅ |
| About Page | ✅ | ✅ |
| Agent Integration | Direct | Via FastAPI REST API |
| Async Processing | `asyncio.run()` | `async/await` in FastAPI |
| Deployment | Single app | Frontend + Backend |

Both UIs provide the same functionality but with different architectures:
- **Streamlit**: Single-file app, direct agent calls, simpler deployment
- **React**: Separated frontend/backend, REST API, better for production scalability

---

## Development

### Adding New Features

Edit `streamlit_app.py` and follow these patterns:

1. **Import agents:**
   ```python
   from src.agents.orchestrator import AgentOrchestrator
   ```

2. **Use async processing:**
   ```python
   results = asyncio.run(
       orchestrator.process_grant_proposal_async(file_path, send_email)
   )
   ```

3. **Handle results:**
   ```python
   st.session_state.workflow_results = results
   ```

### Testing

Test the Streamlit app:
```bash
# Run in demo mode (no Azure services required)
USE_MANAGED_IDENTITY=false streamlit run src/app/streamlit_app.py

# Run with Azure services
streamlit run src/app/streamlit_app.py
```

---

**Last Updated:** December 18, 2025  
**Version:** 2.0 (Async with Real Agents)
