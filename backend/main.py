"""
FastAPI Backend for Grant Compliance Demo

Provides REST API endpoints for document processing and Azure service integration.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import os
import sys
from pathlib import Path
import tempfile
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.orchestrator import AgentOrchestrator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Knowledge base configuration
KNOWLEDGE_BASE_SOURCE = os.getenv('KNOWLEDGE_BASE_SOURCE', 'local').lower()
KNOWLEDGE_BASE_PATH = Path(os.getenv('KNOWLEDGE_BASE_PATH', './knowledge_base'))
EXECUTIVE_ORDERS_PATH = Path(os.getenv('KNOWLEDGE_BASE_EXECUTIVE_ORDERS_PATH', './knowledge_base/sample_executive_orders'))

# Create FastAPI app
app = FastAPI(
    title="Grant Compliance API",
    description="REST API for automated grant proposal compliance checking",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ProcessSampleRequest(BaseModel):
    sample_name: str
    send_email: bool = False
    use_azure: bool = True


class AzureServiceStatus(BaseModel):
    azure_openai: bool
    document_intelligence: bool
    ai_search: bool
    ai_foundry: bool


class HealthResponse(BaseModel):
    status: str
    message: str
    version: str


# Helper functions
def check_azure_service_status() -> AzureServiceStatus:
    """Check if Azure services are configured."""
    return AzureServiceStatus(
        azure_openai=bool(
            os.getenv('AZURE_OPENAI_ENDPOINT') and 
            os.getenv('AZURE_OPENAI_API_KEY')
        ),
        document_intelligence=bool(
            os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT') and 
            os.getenv('AZURE_DOCUMENT_INTELLIGENCE_API_KEY')
        ),
        ai_search=bool(
            os.getenv('AZURE_SEARCH_ENDPOINT') and 
            os.getenv('AZURE_SEARCH_API_KEY')
        ),
        ai_foundry=bool(
            os.getenv('AZURE_AI_FOUNDRY_ENDPOINT') and 
            os.getenv('AZURE_AI_FOUNDRY_API_KEY')
        )
    )


# API Routes

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="Grant Compliance API is running",
        version="1.0.0"
    )


@app.get("/api/azure/status", response_model=AzureServiceStatus)
async def get_azure_status():
    """Get Azure services configuration status."""
    return check_azure_service_status()


@app.post("/api/process/upload")
async def process_uploaded_document(
    file: UploadFile = File(...),
    send_email: bool = Form(False),
    use_azure: bool = Form(True)
):
    """
    Upload and process a grant proposal document.
    
    Args:
        file: Document file (PDF, DOCX, or TXT)
        send_email: Whether to send email notifications
        use_azure: Whether to use Azure services
        
    Returns:
        Complete workflow results including compliance and risk reports
    """
    try:
        # Validate file type
        allowed_extensions = ['.pdf', '.docx', '.txt']
        file_ext = Path(file.filename or '').suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        logger.info(f"Processing uploaded file: {file.filename}")
        
        # Initialize orchestrator and process
        orchestrator = AgentOrchestrator(use_azure=use_azure)
        results = await orchestrator.process_grant_proposal_async(
            tmp_file_path,
            send_email=send_email
        )
        
        # Clean up temp file
        try:
            os.unlink(tmp_file_path)
        except Exception as e:
            logger.warning(f"Failed to delete temp file: {e}")
        
        logger.info(f"Successfully processed {file.filename}")
        return JSONResponse(content=results)
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process/sample")
async def process_sample_document(request: ProcessSampleRequest):
    """
    Process a sample grant proposal from the knowledge base.
    
    Args:
        request: Sample processing request with sample name and options
        
    Returns:
        Complete workflow results including compliance and risk reports
    """
    try:
        # Find sample file
        sample_dir = Path(__file__).parent.parent / 'knowledge_base' / 'sample_proposals'
        sample_files = list(sample_dir.glob(f"{request.sample_name}*"))
        
        if not sample_files:
            raise HTTPException(
                status_code=404,
                detail=f"Sample '{request.sample_name}' not found"
            )
        
        sample_path = sample_files[0]
        logger.info(f"Processing sample: {sample_path.name}")
        
        # Initialize orchestrator and process
        orchestrator = AgentOrchestrator(use_azure=request.use_azure)
        results = await orchestrator.process_grant_proposal_async(
            str(sample_path),
            send_email=request.send_email
        )
        
        logger.info(f"Successfully processed sample {request.sample_name}")
        return JSONResponse(content=results)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing sample: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge-base")
async def get_knowledge_base_info():
    """Get information about the knowledge base (Azure AI Search or Local)."""
    try:
        if KNOWLEDGE_BASE_SOURCE == 'azure':
            return await _get_knowledge_base_from_azure()
        else:
            return await _get_knowledge_base_from_local()
        
    except Exception as e:
        logger.error(f"Error getting knowledge base info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_knowledge_base_from_local() -> Dict[str, Any]:
    """Get knowledge base information from local file system."""
    kb_path = Path(__file__).parent.parent / 'knowledge_base' if not KNOWLEDGE_BASE_PATH.is_absolute() else KNOWLEDGE_BASE_PATH
    
    # Count executive orders
    eo_dir = kb_path / 'sample_executive_orders' if not EXECUTIVE_ORDERS_PATH.is_absolute() else EXECUTIVE_ORDERS_PATH
    eo_files = list(eo_dir.glob('*.txt')) + list(eo_dir.glob('*.pdf'))
    
    # Count sample proposals
    sample_dir = kb_path / 'sample_proposals'
    sample_files = list(sample_dir.glob('*.pdf')) + list(sample_dir.glob('*.txt'))
    
    return {
        'source': 'local',
        'executive_orders_count': len(eo_files),
        'sample_proposals_count': len(sample_files),
        'executive_orders': [{'name': f.stem, 'type': f.suffix[1:]} for f in eo_files],
        'sample_proposals': [f.name for f in sample_files]
    }


async def _get_knowledge_base_from_azure() -> Dict[str, Any]:
    """Get knowledge base information from Azure AI Search."""
    try:
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents.aio import SearchClient
        from azure.identity.aio import DefaultAzureCredential
        
        search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        search_index = os.getenv('AZURE_SEARCH_INDEX_NAME', 'grant-compliance-index')
        use_managed_identity = os.getenv('USE_MANAGED_IDENTITY', 'true').lower() == 'true'
        
        if not search_endpoint:
            raise HTTPException(
                status_code=503,
                detail="Azure AI Search not configured. Set AZURE_SEARCH_ENDPOINT in .env"
            )
        
        # Set up credentials
        if use_managed_identity:
            # Exclude EnvironmentCredential to avoid Conditional Access blocking
            # Service principal credentials in .env may be blocked by CA policies or have invalid values
            credential = DefaultAzureCredential(exclude_environment_credential=True)
        else:
            search_key = os.getenv('AZURE_SEARCH_API_KEY')
            if not search_key:
                raise HTTPException(
                    status_code=503,
                    detail="Azure AI Search API key not configured"
                )
            credential = AzureKeyCredential(search_key)
        
        # Initialize async search client
        search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=search_index,
            credential=credential
        )
        
        try:
            # Query for executive orders (async)
            eo_results = []
            search_results = await search_client.search(
                search_text="*",
                filter="document_type eq 'executive_order'",
                select=["title", "executive_order_number", "category"],
                top=1000
            )
            
            async for doc in search_results:
                eo_results.append(doc)
            
            executive_orders = [
                {
                    'name': doc.get('title', 'Unknown'),
                    'type': 'indexed',
                    'eo_number': doc.get('executive_order_number'),
                    'category': doc.get('category')
                }
                for doc in eo_results
            ]
            
            return {
                'source': 'azure',
                'index_name': search_index,
                'executive_orders_count': len(eo_results),
                'sample_proposals_count': 0,  # Proposals are processed on-demand, not indexed
                'executive_orders': executive_orders,
                'sample_proposals': []
            }
        finally:
            # Clean up async client
            await search_client.close()
            if use_managed_identity and hasattr(credential, 'close'):
                await credential.close() # type: ignore
        
    except ImportError:
        logger.error("Azure Search packages not installed. Run: pip install azure-search-documents azure-identity")
        raise HTTPException(
            status_code=503,
            detail="Azure Search packages not installed"
        )
    except Exception as e:
        logger.error(f"Error connecting to Azure AI Search: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to Azure AI Search: {str(e)}"
        )


@app.get("/api/knowledge-base/executive-order/{name}")
async def get_executive_order(name: str):
    """Get content of a specific executive order (Local file system only)."""
    try:
        kb_path = Path(__file__).parent.parent / 'knowledge_base' if not KNOWLEDGE_BASE_PATH.is_absolute() else KNOWLEDGE_BASE_PATH
        eo_dir = kb_path / 'sample_executive_orders' if not EXECUTIVE_ORDERS_PATH.is_absolute() else EXECUTIVE_ORDERS_PATH
        
        # Find the file (could be .txt or .pdf)
        eo_files = list(eo_dir.glob(f"{name}.*"))
        
        if not eo_files:
            raise HTTPException(
                status_code=404,
                detail=f"Executive order '{name}' not found"
            )
        
        eo_file = eo_files[0]
        
        # Only return content for text files
        if eo_file.suffix == '.txt':
            with open(eo_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                'name': name,
                'type': 'text',
                'content': content,
                'word_count': len(content.split())
            }
        else:
            return {
                'name': name,
                'type': 'pdf',
                'content': None,
                'message': 'PDF content not available via API'
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting executive order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge-base/samples")
async def get_sample_proposals():
    """Get list of sample proposals."""
    try:
        kb_path = Path(__file__).parent.parent / 'knowledge_base'
        sample_dir = kb_path / 'sample_proposals'
        
        sample_files = list(sample_dir.glob('*.pdf')) + list(sample_dir.glob('*.txt'))
        
        samples = [
            {
                'name': f.name,
                'stem': f.stem,
                'type': f.suffix[1:],
                'size': f.stat().st_size
            }
            for f in sample_files
        ]
        
        return {'samples': samples}
        
    except Exception as e:
        logger.error(f"Error getting sample proposals: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge-base/download/{name}")
async def download_executive_order(name: str):
    """Download a PDF executive order (Local file system only)."""
    try:
        kb_path = Path(__file__).parent.parent / 'knowledge_base' if not KNOWLEDGE_BASE_PATH.is_absolute() else KNOWLEDGE_BASE_PATH
        eo_dir = kb_path / 'sample_executive_orders' if not EXECUTIVE_ORDERS_PATH.is_absolute() else EXECUTIVE_ORDERS_PATH
        
        # Find the PDF file
        pdf_file = eo_dir / f"{name}.pdf"
        
        if not pdf_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"PDF file for '{name}' not found"
            )
        
        return FileResponse(
            path=str(pdf_file),
            media_type='application/pdf',
            filename=f"{name}.pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading executive order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
