# Grant Compliance Backend API

FastAPI backend for the Grant Proposal Compliance Automation system.

## Features

- 🚀 FastAPI REST API
- 📄 Document upload and processing
- 🤖 Azure AI integration
- 📚 Knowledge base access
- 🔄 Multi-agent orchestration

## Prerequisites

- Python 3.9+
- Azure AI services (optional - works in demo mode without)
- Virtual environment activated

## Quick Start

### 1. Set Up Environment

```bash
cd backend

# Create virtual environment (if not exists)
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate     # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

The backend uses the same `.env` file from the project root. Ensure you have:

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your_api_key

# AI Search (optional)
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=your_api_key
AZURE_SEARCH_INDEX_NAME=grant-compliance-index

# AI Foundry (optional)
AZURE_AI_FOUNDRY_ENDPOINT=https://your-foundry.services.ai.azure.com/api/projects/yourProject
AZURE_AI_FOUNDRY_API_KEY=your_api_key
```

### 4. Start the Server

```bash
# Development mode with auto-reload
uvicorn main:app --reload --port 8000

# OR use Python directly
python main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health & Status

- `GET /api/health` - Health check
- `GET /api/azure/status` - Check Azure services configuration

### Document Processing

- `POST /api/process/upload` - Upload and process a document
  - Form data: `file`, `send_email`, `use_azure`
  - Returns: Complete workflow results

- `POST /api/process/sample` - Process a sample document
  - JSON body: `{ "sample_name": "...", "send_email": bool, "use_azure": bool }`
  - Returns: Complete workflow results

### Knowledge Base

- `GET /api/knowledge-base` - Get knowledge base info
  - Returns: Counts and lists of EOs and samples

- `GET /api/knowledge-base/executive-order/{name}` - Get EO content
  - Returns: EO details and content (text only)

- `GET /api/knowledge-base/samples` - Get sample proposals list
  - Returns: List of sample proposal files

## Project Structure

```
backend/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Dependencies

- **FastAPI** - Modern web framework
- **Uvicorn** - ASGI server
- **python-multipart** - File upload support
- **python-dotenv** - Environment variables
- **Pydantic** - Data validation

The backend also uses the agent orchestrator from the parent project:
- `agents/orchestrator.py` - Multi-agent workflow

## Development

### Running Tests

```bash
# From project root
pytest tests/test_orchestrator.py
```

### CORS Configuration

CORS is configured to allow requests from:
- `http://localhost:3000` (Vite dev server)
- `http://localhost:5173` (Alternative Vite port)

Update `CORSMiddleware` in `main.py` if you need different origins.

### Logging

Logs are written to console with INFO level. Configure logging in `main.py`:

```python
logging.basicConfig(level=logging.DEBUG)  # More verbose
```

## Azure Integration

The backend integrates with Azure services through the orchestrator:

1. **Document Processing**: Azure Document Intelligence extracts text
2. **Summarization**: Azure OpenAI generates summaries
3. **Compliance Check**: Azure AI Search finds relevant executive orders
4. **Risk Analysis**: Azure OpenAI assesses risk
5. **Email Notifications**: Microsoft Graph API (if configured)

### Demo Mode

If Azure services are not configured, the system falls back to:
- Local document parsing
- Simulated AI responses
- Local knowledge base search
- Simulated email sending

## Troubleshooting

### Port Already in Use

```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9  # Linux/Mac
# OR
netstat -ano | findstr :8000   # Windows
```

### Import Errors

Ensure you're running from the backend directory and the parent project agents are accessible:

```bash
cd backend
python -c "from agents.orchestrator import AgentOrchestrator"
```

### File Upload Issues

- Check file size limits (default: no limit in FastAPI)
- Verify file type is allowed: PDF, DOCX, TXT
- Ensure temp directory has write permissions

### Azure Connection Errors

- Verify environment variables are set correctly
- Check Azure service endpoints are accessible
- Ensure API keys are valid
- Try demo mode first: `use_azure=false`

## Production Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Environment Variables

Set production environment variables:
- Use secrets management (Azure Key Vault)
- Never commit `.env` files
- Use environment-specific configurations

### Security

- Enable HTTPS in production
- Configure proper CORS origins
- Add rate limiting
- Implement authentication/authorization
- Validate all inputs

## Learn More

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Azure AI Services](https://learn.microsoft.com/azure/ai-services/)
