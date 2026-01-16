"""
Test script for Azure Document Intelligence with Managed Identity
Tests document processing using ONLY managed identity authentication (no API key).
"""

import os
import sys
import logging
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from agents.document_ingestion_agent import DocumentIngestionAgent

# Configure logging to force output to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger(__name__)

# Also use print for immediate output
def log_and_print(message):
    """Print message and log it."""
    print(message)
    logger.info(message)


def test_managed_identity_authentication():
    """
    Test Azure Document Intelligence with managed identity authentication only.
    This test explicitly DOES NOT use API keys.
    """
    print("=" * 80)
    print("Testing Azure Document Intelligence with Managed Identity")
    print("=" * 80)
    
    # Get endpoint from environment (required)
    endpoint = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
    
    if not endpoint:
        print("\n❌ ERROR: AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT environment variable is required")
        print("Set it to your Document Intelligence endpoint, e.g.:")
        print("export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT='https://your-resource.cognitiveservices.azure.com/'")
        return False
    
    # Ensure API key is NOT being used
    if os.getenv('AZURE_DOCUMENT_INTELLIGENCE_API_KEY'):
        print("\n⚠️  WARNING: AZURE_DOCUMENT_INTELLIGENCE_API_KEY is set but will be ignored")
        print("Unsetting it for this test to ensure managed identity is used")
        # Temporarily remove API key from environment
        api_key_backup = os.environ.pop('AZURE_DOCUMENT_INTELLIGENCE_API_KEY', None)
    else:
        api_key_backup = None
    
    try:
        # Initialize agent with managed identity
        print("\n📋 Configuration:")
        print(f"  Endpoint: {endpoint}")
        print("  Authentication: Managed Identity (DefaultAzureCredential)")
        
        print("\n🔧 Initializing DocumentIngestionAgent...")
        agent = DocumentIngestionAgent(
            use_azure=True,
            use_managed_identity=True
        )
        
        # Verify configuration
        assert agent.use_azure, "Azure processing should be enabled"
        assert agent.use_managed_identity, "Managed identity should be enabled"
        assert agent.azure_endpoint == endpoint, "Endpoint should be set"
        assert agent.azure_key is None or agent.azure_key == '', "API key should not be used"
        
        print("✅ Agent initialized successfully with managed identity")
        
        # Find a test document
        test_files = [
            "knowledge_base/sample_executive_orders/EO-14087. 11.20.25_Community_Health_Centers.pdf",
            "knowledge_base/sample_proposals/sample_grant_proposal.pdf",
            "README.md"  # Fallback to any text file
        ]
        
        test_file = None
        for file_path in test_files:
            full_path = Path(__file__).parent.parent / file_path
            if full_path.exists():
                test_file = str(full_path)
                print(f"📄 Found test file: {test_file}")
                break
        
        if not test_file:
            print("\n⚠️  No test files found. Creating a temporary test file.")
            test_file = "/tmp/test_document.txt"
            with open(test_file, 'w') as f:
                f.write("This is a test document for Azure Document Intelligence.\n")
                f.write("Testing managed identity authentication.\n")
                f.write("Grant Proposal: Community Development Initiative\n")
                f.write("Budget: $50,000\n")
                f.write("Deadline: December 31, 2025\n")
            print(f"Created temporary test file: {test_file}")
        
        # Process the document
        print("\n" + "-" * 80)
        print("🔄 Processing document with Azure Document Intelligence...")
        print("-" * 80)
        
        result = agent.process_document(test_file)
        
        # Verify results
        assert 'text' in result, "Result should contain extracted text"
        assert 'metadata' in result, "Result should contain metadata"
        assert result['metadata']['processing_method'] == 'azure', "Should use Azure processing"
        
        print("✅ Document processed successfully")
        print("-" * 80)
        print("📊 Results:")
        print(f"  Text length: {len(result['text'])} characters")
        print(f"  Word count: {result.get('word_count', 0)}")
        print(f"  Page count: {result.get('page_count', 0)}")
        print(f"  Processing method: {result['metadata']['processing_method']}")
        
        if result.get('tables'):
            print(f"  Tables found: {len(result['tables'])}")
        
        if result.get('key_value_pairs'):
            print(f"  Key-value pairs found: {len(result['key_value_pairs'])}")
            for kv in result['key_value_pairs'][:5]:  # Show first 5
                print(f"    - {kv['key']}: {kv['value']}")
        
        print("-" * 80)
        print("📝 Text preview (first 300 chars):")
        print(result['text'][:300])
        print("-" * 80)
        
        # Test metadata extraction
        metadata = agent.extract_metadata(result)
        print("\n📋 Extracted Metadata:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Managed Identity Authentication Working!")
        print("=" * 80)
        
        return True
        
    except ImportError as e:
        print(f"\n❌ Missing required package: {e}")
        print("Install required packages:")
        print("  pip install azure-ai-documentintelligence azure-identity")
        return False
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        print("\nFull error details:")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Restore API key if it was set
        if api_key_backup:
            os.environ['AZURE_DOCUMENT_INTELLIGENCE_API_KEY'] = api_key_backup


def check_azure_credentials():
    """Check if Azure credentials are available for managed identity."""
    print("\n🔍 Checking Azure credential availability...")
    
    try:
        from azure.identity import DefaultAzureCredential
        
        credential = DefaultAzureCredential()
        print("✅ DefaultAzureCredential created successfully")
        
        # Try to get a token (this will verify credentials work)
        print("🔐 Attempting to acquire token...")
        try:
            token = credential.get_token("https://cognitiveservices.azure.com/.default")
            print("✅ Successfully acquired token with managed identity")
            print(f"   Token expires at: {token.expires_on}")
            return True
        except Exception as token_error:
            error_msg = str(token_error)
            print(f"\n❌ Failed to acquire token: {error_msg[:200]}")
            
            # Check for Conditional Access
            if "AADSTS53003" in error_msg or "Conditional Access" in error_msg:
                print("\n⚠️  CONDITIONAL ACCESS POLICY BLOCKING")
                print("Your organization's Conditional Access policies are blocking token issuance.")
                print("\n💡 SOLUTIONS:")
                print("   1. Contact your Azure admin to adjust CA policies")
                print("   2. Use API key authentication instead (not recommended for production)")
                print("   3. Request exception for this service principal/managed identity")
                return False
            
            print("\nThis could mean:")
            print("  1. Not running in Azure environment (VM, App Service, Function, etc.)")
            print("  2. Managed identity not enabled on the resource")
            print("  3. Not logged in with 'az login' for local development")
            print("")
            print("For local development, run: az login")
            print("For Azure resources, enable managed identity in the portal")
            return False
        
    except ImportError:
        print("❌ azure-identity package not installed")
        print("Install it with: pip install azure-identity")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n")
    print("=" * 80)
    print("Azure Document Intelligence - Managed Identity Test")
    print("=" * 80)
    
    # Check credentials first
    credentials_ok = check_azure_credentials()
    
    print("\n")
    
    if not credentials_ok:
        print("⚠️  Credential check failed!")
        print("The test will likely fail if credentials are not properly configured.")
        print("\nDo you want to continue anyway? This may help diagnose the issue.")
        print("Press Ctrl+C to abort, or Enter to continue...")
        try:
            input()
        except KeyboardInterrupt:
            print("\n\nTest aborted by user.")
            sys.exit(1)
        print("\nContinuing with test...\n")
    
    # Run the test
    success = test_managed_identity_authentication()
    
    print("\n")
    
    # Exit with appropriate code
    if success:
        print("✅ Test completed successfully!")
        sys.exit(0)
    else:
        print("❌ Test failed!")
        sys.exit(1)
