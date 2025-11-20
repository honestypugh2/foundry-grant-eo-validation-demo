"""
Simple FastAPI Backend for Testing React App Connection
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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

class HealthResponse(BaseModel):
    status: str
    message: str
    version: str

class AzureServiceStatus(BaseModel):
    azure_openai: bool
    document_intelligence: bool
    ai_search: bool
    ai_foundry: bool

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
    return AzureServiceStatus(
        azure_openai=False,
        document_intelligence=False,
        ai_search=False,
        ai_foundry=False
    )

@app.get("/api/knowledge-base")
async def get_knowledge_base_info():
    """Get information about the knowledge base."""
    return {
        'executive_orders_count': 3,
        'sample_proposals_count': 2,
        'executive_orders': ['EO_12345', 'EO_67890'],
        'sample_proposals': ['sample1.pdf', 'sample2.pdf']
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
