"""Test Azure Search connectivity and check if index has documents"""
import os
import asyncio
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

async def test_search():
    endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    api_key = os.getenv('AZURE_SEARCH_API_KEY')
    index_name = os.getenv('AZURE_SEARCH_INDEX_NAME')
    
    if not endpoint or not api_key or not index_name:
        print("❌ Error: Missing required environment variables")
        print("Please ensure AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY, and AZURE_SEARCH_INDEX_NAME are set")
        return
    
    print("=== Testing Azure Search ===")
    print(f"Endpoint: {endpoint}")
    print(f"Index: {index_name}")
    print()
    
    search_client = SearchClient(
        endpoint=endpoint,
        index_name=index_name,
        credential=AzureKeyCredential(api_key)
    )
    
    try:
        # Test search
        print("Searching for 'executive order'...")
        results = await search_client.search(search_text='executive order', top=3)
        doc_count = 0
        async for result in results:
            doc_count += 1
            print(f"Document {doc_count}: {result.get('title', 'No title')[:80]}")
        
        print(f"\nTotal documents found: {doc_count}")
        
        if doc_count == 0:
            print("\n⚠️  Index exists but is empty. Run: python scripts/index_knowledge_base.py")
        else:
            print("\n✅ Azure Search is working correctly!")
            
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        if 'ResourceNotFoundError' in str(type(e)):
            print("\nIndex does not exist. Run: python scripts/index_knowledge_base.py")
    finally:
        await search_client.close()

if __name__ == "__main__":
    asyncio.run(test_search())
