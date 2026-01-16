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

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.orchestrator import AgentOrchestrator
from agents.sequential_workflow_orchestrator import SequentialWorkflowOrchestrator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agent Service configuration
# AGENT_SERVICE: 'agent-framework' uses agent_framework SDK, 'foundry' uses azure-ai-projects SDK
AGENT_SERVICE = os.getenv('AGENT_SERVICE', 'agent-framework').lower()

# Orchestrator configuration - defaults to 'sequential' for the new Agent Framework workflow
# Options: 'sequential' (Agent Framework workflows) or 'legacy' (original orchestrator)
ORCHESTRATOR_TYPE = os.getenv('ORCHESTRATOR_TYPE', 'sequential').lower()

# Import the appropriate Foundry orchestrator if needed
SequentialWorkflowOrchestratorFoundry = None  # type: ignore
if AGENT_SERVICE == 'foundry':
    try:
        from agents.sequential_workflow_orchestrator_foundry import SequentialWorkflowOrchestratorFoundry
        logger.info("Foundry Agent Service SDK loaded successfully")
    except ImportError as e:
        logger.warning(f"Failed to import Foundry orchestrator: {e}. Falling back to agent-framework.")
        AGENT_SERVICE = 'agent-framework'

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


@app.get("/api/config/orchestrator")
async def get_orchestrator_config():
    """Get the current orchestrator configuration."""
    is_foundry = AGENT_SERVICE == 'foundry'
    is_sequential = ORCHESTRATOR_TYPE == 'sequential'
    
    return {
        "orchestrator_type": ORCHESTRATOR_TYPE,
        "agent_service": AGENT_SERVICE,
        "description": _get_orchestrator_description(is_sequential, is_foundry),
        "features": {
            "agent_framework_workflows": is_sequential and not is_foundry,
            "foundry_agent_service": is_sequential and is_foundry,
            "azure_ai_search_hosted_tool": is_sequential,
            "streaming_support": is_sequential,
        }
    }


def _get_orchestrator_description(is_sequential: bool, is_foundry: bool) -> str:
    """Get a description of the current orchestrator configuration."""
    if not is_sequential:
        return "Legacy Orchestrator"
    elif is_foundry:
        return "Sequential Workflow (Foundry Agent Service - azure-ai-projects SDK)"
    else:
        return "Sequential Workflow (Agent Framework SDK)"


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
        
        # Initialize orchestrator based on configuration
        # AGENT_SERVICE: 'foundry' uses Foundry Agent Service, 'agent-framework' uses Agent Framework SDK
        # ORCHESTRATOR_TYPE: 'sequential' uses workflow, 'legacy' uses original orchestrator
        if ORCHESTRATOR_TYPE == 'sequential':
            if AGENT_SERVICE == 'foundry' and SequentialWorkflowOrchestratorFoundry is not None:
                logger.info("Using Sequential Workflow Orchestrator (Foundry Agent Service)")
                orchestrator = SequentialWorkflowOrchestratorFoundry(use_azure=use_azure, send_email=send_email)
            else:
                logger.info("Using Sequential Workflow Orchestrator (Agent Framework)")
                orchestrator = SequentialWorkflowOrchestrator(use_azure=use_azure, send_email=send_email)
            results = await orchestrator.process_grant_proposal_async(tmp_file_path)
        else:
            logger.info("Using Legacy Orchestrator")
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
        # Find sample file (knowledge_base is at project root, not under src/)
        sample_dir = Path(__file__).parent.parent.parent / 'knowledge_base' / 'sample_proposals'
        sample_files = list(sample_dir.glob(f"{request.sample_name}*"))
        
        if not sample_files:
            raise HTTPException(
                status_code=404,
                detail=f"Sample '{request.sample_name}' not found"
            )
        
        sample_path = sample_files[0]
        logger.info(f"Processing sample: {sample_path.name}")
        
        # Initialize orchestrator based on configuration
        # AGENT_SERVICE: 'foundry' uses Foundry Agent Service, 'agent-framework' uses Agent Framework SDK
        # ORCHESTRATOR_TYPE: 'sequential' uses workflow, 'legacy' uses original orchestrator
        if ORCHESTRATOR_TYPE == 'sequential':
            if AGENT_SERVICE == 'foundry' and SequentialWorkflowOrchestratorFoundry is not None:
                logger.info("Using Sequential Workflow Orchestrator (Foundry Agent Service)")
                orchestrator = SequentialWorkflowOrchestratorFoundry(
                    use_azure=request.use_azure, 
                    send_email=request.send_email
                )
            else:
                logger.info("Using Sequential Workflow Orchestrator (Agent Framework)")
                orchestrator = SequentialWorkflowOrchestrator(
                    use_azure=request.use_azure, 
                    send_email=request.send_email
                )
            results = await orchestrator.process_grant_proposal_async(str(sample_path))
        else:
            logger.info("Using Legacy Orchestrator")
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
    # knowledge_base is at project root, not under src/
    kb_path = Path(__file__).parent.parent.parent / 'knowledge_base' if not KNOWLEDGE_BASE_PATH.is_absolute() else KNOWLEDGE_BASE_PATH
    
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
        from azure.identity.aio import ChainedTokenCredential, ManagedIdentityCredential, AzureCliCredential
        
        search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        search_index = os.getenv('AZURE_SEARCH_INDEX_NAME', 'grant-compliance-index')
        use_managed_identity = os.getenv('USE_MANAGED_IDENTITY', 'true').lower() == 'true'
        
        if not search_endpoint:
            raise HTTPException(
                status_code=503,
                detail="Azure AI Search not configured. Set AZURE_SEARCH_ENDPOINT in .env"
            )
        
        # Set up credentials - use ChainedTokenCredential for flexibility
        # This tries ManagedIdentity first (for Azure deployment), then falls back to AzureCli (for local dev)
        if use_managed_identity:
            credential = ChainedTokenCredential(
                ManagedIdentityCredential(),
                AzureCliCredential()
            )
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
            
            # First try with document_type filter, then fallback to all documents
            try:
                search_results = await search_client.search(
                    search_text="*",
                    filter="document_type eq 'executive_order'",
                    select=["title", "executive_order_number", "category", "id"],
                    top=1000
                )
                async for doc in search_results:
                    eo_results.append(doc)
            except Exception as filter_error:
                logger.warning(f"Filtered search failed, trying without filter: {filter_error}")
                # Fallback: search without filter
                search_results = await search_client.search(
                    search_text="*",
                    select=["title", "executive_order_number", "category", "id"],
                    top=100
                )
                async for doc in search_results:
                    eo_results.append(doc)
            
            executive_orders = [
                {
                    'name': doc.get('title', doc.get('id', 'Unknown')),
                    'type': 'indexed',
                    'eo_number': doc.get('executive_order_number'),
                    'category': doc.get('category')
                }
                for doc in eo_results
            ]
            
            # Also include local sample proposals (knowledge_base is at project root)
            kb_path = Path(__file__).parent.parent.parent / 'knowledge_base'
            sample_dir = kb_path / 'sample_proposals'
            sample_files = list(sample_dir.glob('*.pdf')) + list(sample_dir.glob('*.txt')) if sample_dir.exists() else []
            
            return {
                'source': 'azure',
                'index_name': search_index,
                'executive_orders_count': len(eo_results),
                'sample_proposals_count': len(sample_files),
                'executive_orders': executive_orders,
                'sample_proposals': [f.name for f in sample_files]
            }
        except Exception as search_error:
            # If token auth failed with 403, try with API key as fallback
            search_key = os.getenv('AZURE_SEARCH_API_KEY')
            if search_key and "Forbidden" in str(search_error):
                logger.warning(f"Token auth failed ({search_error}), falling back to API key")
                await search_client.close()
                if hasattr(credential, 'close'):
                    await credential.close()  # type: ignore
                
                # Retry with API key
                search_client = SearchClient(
                    endpoint=search_endpoint,
                    index_name=search_index,
                    credential=AzureKeyCredential(search_key)
                )
                
                eo_results = []
                search_results = await search_client.search(
                    search_text="*",
                    select=["title", "executive_order_number", "category", "id"],
                    top=100
                )
                async for doc in search_results:
                    eo_results.append(doc)
                
                await search_client.close()
                
                executive_orders = [
                    {
                        'name': doc.get('title', doc.get('id', 'Unknown')),
                        'type': 'indexed',
                        'eo_number': doc.get('executive_order_number'),
                        'category': doc.get('category')
                    }
                    for doc in eo_results
                ]
                
                # Also include local sample proposals (knowledge_base is at project root)
                kb_path = Path(__file__).parent.parent.parent / 'knowledge_base'
                sample_dir = kb_path / 'sample_proposals'
                sample_files = list(sample_dir.glob('*.pdf')) + list(sample_dir.glob('*.txt')) if sample_dir.exists() else []
                
                return {
                    'source': 'azure',
                    'index_name': search_index,
                    'executive_orders_count': len(eo_results),
                    'sample_proposals_count': len(sample_files),
                    'executive_orders': executive_orders,
                    'sample_proposals': [f.name for f in sample_files]
                }
            else:
                raise
        finally:
            # Clean up async client
            try:
                await search_client.close()
            except Exception:
                pass
            if use_managed_identity and hasattr(credential, 'close'):
                try:
                    await credential.close()  # type: ignore
                except Exception:
                    pass
        
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


async def _get_executive_order_from_azure(name: str) -> Dict[str, Any] | None:
    """Get executive order content from Azure AI Search."""
    from azure.core.credentials import AzureKeyCredential
    from azure.search.documents.aio import SearchClient
    
    search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    search_index = os.getenv('AZURE_SEARCH_INDEX_NAME', 'grant-compliance-index')
    search_key = os.getenv('AZURE_SEARCH_API_KEY')
    
    if not search_endpoint or not search_key:
        return None
    
    search_client = SearchClient(
        endpoint=search_endpoint,
        index_name=search_index,
        credential=AzureKeyCredential(search_key)
    )
    
    try:
        # Search by title or EO number
        # The name might be like "EO-14102. 11.20.25 Infrastructure Sustainability"
        search_results = await search_client.search(
            search_text=name,
            select=["title", "content", "executive_order_number", "effective_date", "category"],
            top=1
        )
        
        async for doc in search_results:
            content = doc.get('content', '')
            return {
                'name': doc.get('title', name),
                'type': 'indexed',
                'content': content,
                'word_count': len(content.split()) if content else 0,
                'eo_number': doc.get('executive_order_number'),
                'effective_date': str(doc.get('effective_date', '')),
                'category': doc.get('category'),
                'source': 'azure'
            }
        
        return None
    finally:
        await search_client.close()


@app.get("/api/knowledge-base/executive-order/{name}")
async def get_executive_order(name: str):
    """Get content of a specific executive order (from Azure AI Search or local files)."""
    try:
        # First try Azure AI Search if configured
        if KNOWLEDGE_BASE_SOURCE == 'azure':
            try:
                content = await _get_executive_order_from_azure(name)
                if content:
                    return content
            except Exception as azure_error:
                logger.warning(f"Azure search failed for {name}, trying local: {azure_error}")
        
        # Fallback to local files (knowledge_base is at project root)
        kb_path = Path(__file__).parent.parent.parent / 'knowledge_base' if not KNOWLEDGE_BASE_PATH.is_absolute() else KNOWLEDGE_BASE_PATH
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
        # knowledge_base is at project root, not under src/
        kb_path = Path(__file__).parent.parent.parent / 'knowledge_base'
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
        # knowledge_base is at project root, not under src/
        kb_path = Path(__file__).parent.parent.parent / 'knowledge_base' if not KNOWLEDGE_BASE_PATH.is_absolute() else KNOWLEDGE_BASE_PATH
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
