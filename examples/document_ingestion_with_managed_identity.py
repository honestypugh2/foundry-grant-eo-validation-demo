"""
Example: Using Document Ingestion Agent with Managed Identity

This example demonstrates how to use Azure Document Intelligence
with managed identity authentication instead of API keys.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.document_ingestion_agent import DocumentIngestionAgent


def example_with_managed_identity():
    """Example using managed identity authentication."""
    
    print("=" * 80)
    print("Document Ingestion with Managed Identity")
    print("=" * 80)
    
    # Configure endpoint (required)
    # In production, this would be set as an environment variable
    endpoint = os.getenv(
        'AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT',
        'https://your-resource.cognitiveservices.azure.com/'
    )
    
    # Initialize agent with managed identity
    agent = DocumentIngestionAgent(
        use_azure=True,
        use_managed_identity=True  # Enable managed identity
    )
    
    print(f"Endpoint: {endpoint}")
    print(f"Using Managed Identity: {agent.use_managed_identity}")
    print(f"Using Azure: {agent.use_azure}")
    print()
    
    # Process a document
    test_file = "../knowledge_base/sample_executive_orders/EO-14087. 11.20.25_Community_Health_Centers.pdf"  # Update with a valid test file path
    
    if not os.path.exists(test_file):
        print(f"Test file not found: {test_file}")
        print("Please update the test_file path to a valid document")
        return
    
    print(f"Processing: {test_file}")
    print("-" * 80)
    
    try:
        result = agent.process_document(test_file)
        
        print("Processing complete!")
        print(f"Text length: {len(result['text'])} characters")
        print(f"Word count: {result.get('word_count', 0)}")
        print(f"Page count: {result.get('page_count', 0)}")
        print()
        
        print("Text preview:")
        print(result['text'][:500])
        print()
        
        # Extract metadata
        metadata = agent.extract_metadata(result)
        print("Extracted Metadata:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"Error: {e}")
        raise


def example_with_api_key():
    """Example using API key authentication (legacy)."""
    
    print("=" * 80)
    print("Document Ingestion with API Key (Legacy)")
    print("=" * 80)
    
    # This is the old method - less secure
    agent = DocumentIngestionAgent(
        use_azure=True,
        use_managed_identity=False  # Use API key instead
    )
    
    print(f"Using API Key: {bool(agent.azure_key)}")
    print(f"Using Managed Identity: {agent.use_managed_identity}")
    print()


def example_local_processing():
    """Example using local processing (no Azure)."""
    
    print("=" * 80)
    print("Document Ingestion with Local Processing")
    print("=" * 80)
    
    # For development/testing without Azure
    agent = DocumentIngestionAgent(
        use_azure=False
    )
    
    print(f"Using Azure: {agent.use_azure}")
    print("Will use local PDF/DOCX parsing")
    print()


if __name__ == "__main__":
    # Example 1: Managed Identity (Recommended for Production)
    print("\n\nExample 1: Managed Identity Authentication")
    print("This is the RECOMMENDED approach for production deployments")
    print()
    example_with_managed_identity()
    
    print("\n\n")
    
    # Example 2: API Key (Legacy)
    print("Example 2: API Key Authentication (Legacy)")
    print("Only use this for local development or legacy systems")
    print()
    example_with_api_key()
    
    print("\n\n")
    
    # Example 3: Local Processing
    print("Example 3: Local Processing (No Azure)")
    print("Use this for development without Azure dependencies")
    print()
    example_local_processing()
