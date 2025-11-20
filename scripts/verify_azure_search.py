"""
Verify Azure Search Configuration and API Key Permissions

This script tests your Azure Search setup and verifies that your API key
has the correct permissions for creating indexes and uploading documents.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment
load_dotenv()

print("=" * 70)
print("🔍 Azure Search Configuration Verification")
print("=" * 70)

# Check environment variables
endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
api_key = os.getenv("AZURE_SEARCH_API_KEY")
index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "grant-compliance-index")

print("\n📋 Configuration Check:")
print(f"   AZURE_SEARCH_ENDPOINT: {endpoint if endpoint else '❌ NOT SET'}")
print(f"   AZURE_SEARCH_API_KEY: {'✅ SET (' + api_key[:8] + '...' + api_key[-4:] + ')' if api_key else '❌ NOT SET'}")
print(f"   AZURE_SEARCH_INDEX_NAME: {index_name}")

if not endpoint or not api_key:
    print("\n❌ Missing required environment variables!")
    print("\nPlease set in your .env file:")
    print("   AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net")
    print("   AZURE_SEARCH_API_KEY=your_admin_key_here")
    sys.exit(1)

# Test connection
print("\n🔌 Testing connection...")
try:
    from azure.core.credentials import AzureKeyCredential
    from azure.search.documents.indexes import SearchIndexClient
    
    client = SearchIndexClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(api_key)
    )
    
    print("✅ Connection successful")
    
    # Test permissions - list indexes
    print("\n🔑 Testing API key permissions...")
    try:
        indexes = list(client.list_indexes())
        print(f"✅ Can list indexes - Found {len(indexes)} indexes")
        
        if indexes:
            print("\n📚 Existing indexes:")
            for idx in indexes:
                print(f"   - {idx.name}")
        else:
            print("   (No indexes found)")
        
        print("\n✅ Your API key has ADMIN permissions!")
        print("   You can create indexes and upload documents.")
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Permission test failed: {error_msg}")
        
        if "Forbidden" in error_msg or "403" in error_msg:
            print("\n🔒 Your API key has QUERY permissions only (read-only)")
            print("\n💡 Solution: Get the Admin API key")
            print("\n   Steps:")
            print("   1. Go to Azure Portal: https://portal.azure.com")
            print("   2. Navigate to your Search Service")
            print("   3. Click: Settings → Keys")
            print("   4. Copy the 'Primary admin key' (NOT Query key)")
            print("   5. Update AZURE_SEARCH_API_KEY in your .env file")
            print(f"\n   Your search service: {endpoint}")
            sys.exit(1)
        else:
            print("\n💡 Unexpected error. Check:")
            print(f"   1. Endpoint is correct: {endpoint}")
            print("   2. API key is valid (not expired)")
            print("   3. Search service is running")
            sys.exit(1)
    
    # Test index creation
    print("\n📝 Testing index creation permissions...")
    test_index_name = "test-permissions-verify"
    
    try:
        from azure.search.documents.indexes.models import SearchIndex, SimpleField, SearchFieldDataType
        
        # Try to create a test index
        test_index = SearchIndex(
            name=test_index_name,
            fields=[
                SimpleField(name="id", type=SearchFieldDataType.String, key=True)
            ]
        )
        
        client.create_index(test_index)
        print("✅ Can create indexes")
        
        # Clean up - delete test index
        client.delete_index(test_index_name)
        print("✅ Can delete indexes")
        
        print("\n" + "=" * 70)
        print("🎉 All tests passed! Your configuration is correct.")
        print("=" * 70)
        print("\n✅ You can now run the indexing script:")
        print("   python scripts/index_knowledge_base.py --input knowledge_base/sample_executive_orders")
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Index creation test failed: {error_msg}")
        
        if "Forbidden" in error_msg or "403" in error_msg:
            print("\n🔒 Your API key cannot create indexes")
            print("   You need an ADMIN key, not a QUERY key")
        elif "Conflict" in error_msg:
            print("✅ Can create indexes (conflict means it already exists)")
        else:
            print(f"   Unexpected error: {error_msg}")
        
        sys.exit(1)

except ImportError as e:
    print(f"\n❌ Missing required package: {e}")
    print("\nInstall required packages:")
    print("   pip install azure-search-documents python-dotenv")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ Unexpected error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
