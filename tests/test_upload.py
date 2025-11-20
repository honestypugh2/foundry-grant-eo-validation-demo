#!/usr/bin/env python3
"""Test uploading documents to Azure Search"""
import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

load_dotenv()

endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
api_key = os.getenv('AZURE_SEARCH_API_KEY')
index_name = 'grant-compliance-index'

print(f"Endpoint: {endpoint}")
print(f"Index: {index_name}")
print(f"API Key: {api_key[:10] if api_key else 'Not set'}...")

if not endpoint or not api_key:
    raise ValueError("AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_API_KEY must be set in environment variables")

client = SearchClient(
    endpoint=endpoint,
    index_name=index_name,
    credential=AzureKeyCredential(api_key)
)

# Create sample documents in same format as the indexing script
documents = [
    {
        "id": "test-eo-001",
        "title": "Test Executive Order 001",
        "content": "This is a test executive order about environmental protection.",
        "document_type": "executive_order",
        "executive_order_number": "EO-14001",
        "effective_date": "2025-01-15T00:00:00",
        "category": None,
        "keywords": None,
        "compliance_areas": None,
        "agency": "Federal",
        "status": "Active",
        "summary": "Test executive order summary"
    },
    {
        "id": "test-eo-002",
        "title": "Test Executive Order 002",
        "content": "This is a test executive order about cybersecurity.",
        "document_type": "executive_order",
        "executive_order_number": "EO-14002",
        "effective_date": "2025-02-01T00:00:00",
        "category": None,
        "keywords": None,
        "compliance_areas": None,
        "agency": "Federal",
        "status": "Active",
        "summary": "Test executive order summary"
    }
]

print(f"\nUploading {len(documents)} test documents...")
try:
    result = client.upload_documents(documents=documents)
    succeeded = sum(1 for r in result if r.succeeded)
    print(f"✅ Successfully uploaded {succeeded}/{len(documents)} documents")
    
    for r in result:
        if not r.succeeded:
            print(f"   ❌ {r.key}: {r.error_message if hasattr(r, 'error_message') else 'Unknown'}")
        else:
            print(f"   ✅ {r.key}")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
