# React App Quick Start

> **Get the React frontend running in 60 seconds**

---

## Prerequisites Check

Before starting, verify you have:

```bash
# Check Node.js (requires v16 or higher)
node --version

# Check npm (requires v8 or higher)
npm --version

# Check Python (requires 3.10 or higher)
python --version
```

If any are missing, install them first:
- **Node.js & npm**: [Download from nodejs.org](https://nodejs.org/)
- **Python**: [Download from python.org](https://www.python.org/downloads/)

---

## Quick Start (One Command)

### Option 1: Automatic Setup Script

The fastest way to get running:

```bash
# From project root
./start.sh
```

This script will:
- ✅ Check all prerequisites
- ✅ Install Python dependencies
- ✅ Install Node.js dependencies
- ✅ Start FastAPI backend (port 8000)
- ✅ Start React frontend (port 3000)
- ✅ Open browser automatically

**To stop services:**
```bash
./stop.sh
```

---

## Manual Setup

If you prefer step-by-step control:

### Step 1: Backend Setup (Terminal 1)

```bash
# From project root
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
python main.py
```

✅ Backend running at `http://localhost:8000`

### Step 2: Frontend Setup (Terminal 2)

```bash
# From project root
cd frontend

# Install Node.js dependencies
npm install

# Start development server
npm run dev
```

✅ Frontend running at `http://localhost:3000`

### Step 3: Open Browser

Navigate to `http://localhost:3000` - the app should load automatically!

---

## Verify Installation

### Test Backend API

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Test Frontend

Open browser to `http://localhost:3000` and verify:
- ✅ Home page loads
- ✅ Navigation menu visible
- ✅ Can navigate to About, Upload, Knowledge Base pages

---

## Project Structure

```
foundry-grant-eo-validation-demo/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── requirements.txt     # Python dependencies
│   └── .venv/               # Python virtual environment
├── frontend/
│   ├── src/
│   │   ├── pages/           # React pages
│   │   │   ├── AboutPage.tsx
│   │   │   ├── UploadPage.tsx
│   │   │   ├── ResultsPage.tsx
│   │   │   └── KnowledgeBasePage.tsx
│   │   ├── components/      # Reusable components
│   │   └── App.tsx          # Main React component
│   ├── package.json         # Node.js dependencies
│   └── node_modules/        # Node.js packages
└── start.sh                 # Quick start script
```

---

## Common Issues

### Port Already in Use

**Problem**: `Error: Port 3000 is already in use`

**Solution**:
```bash
# Find process using port 3000
lsof -i :3000          # Linux/Mac
netstat -ano | findstr :3000  # Windows

# Kill the process
kill -9 <PID>          # Linux/Mac
taskkill /PID <PID> /F # Windows

# Or use a different port
npm run dev -- --port 3001
```

### Backend Connection Failed

**Problem**: Frontend shows "Failed to connect to backend"

**Solution**:
1. Verify backend is running: `curl http://localhost:8000/api/health`
2. Check backend terminal for errors
3. Ensure `.env` file exists with correct configuration
4. Restart backend: `cd backend && python main.py`

### Node Modules Missing

**Problem**: `Error: Cannot find module 'react'`

**Solution**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Python Dependencies Missing

**Problem**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
cd backend
source .venv/bin/activate  # Activate venv first!
pip install -r requirements.txt
```

---

## Development Workflow

### Hot Reload

Both frontend and backend support hot reload:

- **Frontend**: Edit files in `frontend/src/` - changes appear instantly
- **Backend**: Edit files in `backend/` - FastAPI auto-reloads

### Code Formatting

```bash
# Frontend (Prettier)
cd frontend
npm run format

# Backend (Black)
cd backend
pip install black
black .
```

### Build for Production

```bash
# Frontend build
cd frontend
npm run build
# Output in frontend/dist/

# Backend (no build needed - Python runs directly)
```

---

## Available Scripts

### Frontend (`frontend/` directory)

```bash
npm run dev        # Start development server (port 3000)
npm run build      # Build for production
npm run preview    # Preview production build
npm run format     # Format code with Prettier
npm run lint       # Lint code with ESLint
```

### Backend (`backend/` directory)

```bash
python main.py     # Start FastAPI server (port 8000)
pytest             # Run backend tests
uvicorn main:app --reload  # Alternative start with uvicorn
```

---

## Environment Configuration

### Required Environment Variables

Create `.env` file in project root:

```env
# Azure AI Foundry
AZURE_AI_PROJECT_CONNECTION_STRING=your_connection_string
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-10-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_INDEX_NAME=grant-compliance-index

# Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-region.api.cognitive.microsoft.com

# Authentication (Production)
USE_MANAGED_IDENTITY=true
```

### Development vs Production

**Development** (local):
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- No authentication required

**Production** (Azure):
- Frontend: `https://your-app.azurewebsites.net`
- Backend: `https://your-api.azurewebsites.net`
- Azure AD authentication required
- HTTPS enforced

---

## Next Steps

### 1. Upload a Document

1. Navigate to **📝 Document Upload**
2. Drag and drop a PDF grant proposal
3. Click **🚀 Analyze for Compliance**
4. View results in the dashboard

### 2. Explore Knowledge Base

1. Navigate to **📚 Knowledge Base**
2. Browse executive orders
3. Download PDFs for reference
4. View sample proposals

### 3. Understand Scoring

1. Navigate to **ℹ️ About**
2. Read about the three-score system:
   - Confidence Score (AI certainty)
   - Compliance Score (regulatory alignment)
   - Risk Score (overall assessment)

### 4. Review Documentation

- [Architecture.md](Architecture.md) - System design
- [Deployment.md](Deployment.md) - Azure deployment
- [UserGuide.md](UserGuide.md) - End-user guide

---

## Technology Stack

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Lucide React** - Icons

### Backend
- **FastAPI** - Python web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **Azure SDK** - Azure service integration

### AI Services
- **Azure AI Foundry** - Agent orchestration
- **Azure OpenAI** - GPT-4 analysis
- **Azure AI Search** - Semantic search
- **Azure Document Intelligence** - OCR

---

## Getting Help

### Documentation
- [Main README](../README.md) - Project overview
- [FastAPI Guide](../FASTAPI_GUIDE.md) - Backend API reference
- [Contributing Guide](../CONTRIBUTING.md) - Contribution guidelines

### Support
- **Issues**: [GitHub Issues](https://github.com/your-org/foundry-grant-eo-validation-demo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/foundry-grant-eo-validation-demo/discussions)

---

## Quick Reference Card

```bash
# Start everything (one command)
./start.sh

# Or manually:
# Terminal 1 - Backend
cd backend && python main.py

# Terminal 2 - Frontend
cd frontend && npm run dev

# Stop everything
./stop.sh

# Check health
curl http://localhost:8000/api/health

# View logs
# Backend: Check Terminal 1
# Frontend: Check Terminal 2
```

---

**Last Updated**: November 2025  
**Version**: 1.0
