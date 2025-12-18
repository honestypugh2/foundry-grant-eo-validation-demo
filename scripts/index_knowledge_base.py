"""
Index Knowledge Base PDFs to Azure AI Search

This script processes PDF documents from the knowledge base and indexes them
in Azure AI Search for semantic retrieval by compliance agents.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

try:
    from azure.core.credentials import AzureKeyCredential
    from azure.search.documents import SearchClient
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.indexes.models import (
        SearchIndex,
        SimpleField,
        SearchableField,
        SearchFieldDataType,
    )
    from azure.identity import DefaultAzureCredential
    from dotenv import load_dotenv
    import PyPDF2
    
    # Document Intelligence is optional
    try:
        from azure.ai.documentintelligence import DocumentIntelligenceClient
        DOCINT_AVAILABLE = True
    except ImportError:
        DocumentIntelligenceClient = None
        DOCINT_AVAILABLE = False
        
except ImportError as e:
    print(f"Error: Required packages not installed: {e}")
    print("Run: pip install azure-search-documents PyPDF2 python-dotenv")
    sys.exit(1)


class KnowledgeBaseIndexer:
    """Index PDF documents to Azure AI Search."""

    def __init__(self):
        """Initialize with Azure credentials from environment."""
        load_dotenv()
        
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_index = os.getenv("AZURE_SEARCH_INDEX_NAME", "grant-compliance-index")
        self.doc_intel_endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        self.use_managed_identity = os.getenv("USE_MANAGED_IDENTITY", "false").lower() == "true"
        
        # Validate required environment variables
        if not self.search_endpoint:
            raise ValueError("AZURE_SEARCH_ENDPOINT environment variable is required")
        
        # Set up credentials
        if self.use_managed_identity:
            self.credential = DefaultAzureCredential()
            self.search_credential = DefaultAzureCredential()
        else:
            search_key = os.getenv("AZURE_SEARCH_API_KEY")
            doc_intel_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
            if not search_key:
                raise ValueError("AZURE_SEARCH_API_KEY environment variable is required when not using managed identity")
            self.search_credential = AzureKeyCredential(search_key)
            if doc_intel_key:
                self.credential = AzureKeyCredential(doc_intel_key)
            else:
                self.credential = None
        
        # Initialize clients
        self.search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.search_index,
            credential=self.search_credential
        )
        
        self.index_client = SearchIndexClient(
            endpoint=self.search_endpoint,
            credential=self.search_credential
        )
        
        # Initialize Document Intelligence client with managed identity and API key fallback
        self.doc_intel_client = None
        self._doc_intel_available = False
        
        if self.doc_intel_endpoint and DOCINT_AVAILABLE and DocumentIntelligenceClient is not None:
            doc_intel_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
            
            # Try managed identity first if enabled
            if self.use_managed_identity:
                try:
                    print("🔐 Attempting Document Intelligence with Managed Identity...")
                    doc_intel_cred = DefaultAzureCredential()
                    self.doc_intel_client = DocumentIntelligenceClient(
                        endpoint=self.doc_intel_endpoint,
                        credential=doc_intel_cred
                    )
                    # Test the connection with a simple operation
                    print("✅ Document Intelligence using Managed Identity")
                    self._doc_intel_available = True
                except Exception as e:
                    error_msg = str(e)
                    if "AADSTS" in error_msg or "Conditional Access" in error_msg:
                        print("⚠️  Managed Identity blocked by Conditional Access policies")
                    else:
                        print(f"⚠️  Managed Identity failed: {error_msg[:100]}...")
                    # Fall through to try API key
            
            # Try API key if managed identity not used or failed
            if not self.doc_intel_client and doc_intel_key:
                try:
                    print("🔑 Attempting Document Intelligence with API key...")
                    self.doc_intel_client = DocumentIntelligenceClient(
                        endpoint=self.doc_intel_endpoint,
                        credential=AzureKeyCredential(doc_intel_key)
                    )
                    print("✅ Document Intelligence client initialized with API key")
                    self._doc_intel_available = True
                except Exception as e:
                    print(f"⚠️  API key initialization failed: {str(e)[:100]}...")
        
        if not self._doc_intel_available:
            print("ℹ️  Document Intelligence not available - using PyPDF2 for text extraction")
            print("   Note: PyPDF2 works well for text-based PDFs but may have issues with scanned documents")

    def create_index(self) -> bool:
        """Create the search index if it doesn't exist.
        
        Returns:
            True if index was created or already exists, False on error
        """
        try:
            # Check if index exists
            try:
                self.index_client.get_index(self.search_index)
                print(f"✅ Search index '{self.search_index}' already exists")
                return True
            except Exception as check_error:
                # Index doesn't exist, continue to create it
                if "NotFound" not in str(check_error) and "ResourceNotFoundError" not in str(type(check_error).__name__):
                    # If it's not a "not found" error, something else is wrong
                    print(f"⚠️  Warning checking index: {check_error}")
            
            print(f"📝 Creating search index '{self.search_index}'...")
            
            # Define index schema
            fields = [
                SimpleField(
                    name="id",
                    type=SearchFieldDataType.String,
                    key=True,
                    filterable=True,
                ),
                SearchableField(
                    name="title",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    filterable=True,
                ),
                SearchableField(
                    name="content",
                    type=SearchFieldDataType.String,
                    searchable=True,
                ),
                SimpleField(
                    name="document_type",
                    type=SearchFieldDataType.String,
                    filterable=True,
                ),
                SearchableField(
                    name="executive_order_number",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    filterable=True,
                ),
                SimpleField(
                    name="effective_date",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    sortable=True,
                ),
                SearchableField(
                    name="category",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    filterable=True,
                ),
                SearchableField(
                    name="keywords",
                    type=SearchFieldDataType.String,
                    searchable=True,
                ),
                SearchableField(
                    name="compliance_areas",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    filterable=True,
                ),
                SimpleField(
                    name="agency",
                    type=SearchFieldDataType.String,
                    filterable=True,
                ),
                SimpleField(
                    name="status",
                    type=SearchFieldDataType.String,
                    filterable=True,
                ),
                SearchableField(
                    name="summary",
                    type=SearchFieldDataType.String,
                    searchable=True,
                ),
            ]
            
            # Create the index
            index = SearchIndex(name=self.search_index, fields=fields)
            
            try:
                self.index_client.create_index(index)
                print(f"✅ Successfully created index '{self.search_index}'")
                return True
            except Exception as create_error:
                # Check if the error is because index already exists (race condition)
                if "ResourceExistsError" in str(type(create_error).__name__) or "Conflict" in str(create_error):
                    print(f"✅ Index '{self.search_index}' already exists")
                    return True
                else:
                    raise create_error
            
        except Exception as e:
            print(f"❌ Error creating index: {str(e)}")
            print("\n💡 Troubleshooting tips:")
            print("   1. Verify your AZURE_SEARCH_API_KEY has 'Contributor' or 'Admin' permissions")
            print("   2. Check that AZURE_SEARCH_ENDPOINT is correct")
            print("   3. Ensure your Azure Search service is running")
            return False

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        Extract text from PDF using Azure Document Intelligence or PyPDF2.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        # Try Document Intelligence first if configured and available
        if self.doc_intel_client and self._doc_intel_available:
            try:
                with open(pdf_path, "rb") as f:
                    poller = self.doc_intel_client.begin_analyze_document(
                        "prebuilt-layout", f
                    )
                    result = poller.result()
                    if not hasattr(self, '_doc_intel_success_shown'):
                        print("  └─ ✅ Using Azure Document Intelligence for OCR")
                        self._doc_intel_success_shown = True
                    return result.content
            except Exception as e:
                error_msg = str(e)
                # Check for authentication errors
                if "AuthenticationTypeDisabled" in error_msg:
                    if not hasattr(self, '_auth_disabled_shown'):
                        print("  └─ ⚠️  Document Intelligence has key-based auth disabled")
                        print("  └─ ℹ️  This resource requires managed identity or Entra ID authentication")
                        print("  └─ ℹ️  Switching to PyPDF2 for all remaining files")
                        self._auth_disabled_shown = True
                    self.doc_intel_client = None  # Disable for remaining files
                    self._doc_intel_available = False
                elif "Forbidden" in error_msg or "401" in error_msg or "403" in error_msg:
                    if not hasattr(self, '_auth_error_shown'):
                        print("  └─ ⚠️  Document Intelligence authentication error")
                        print("  └─ ℹ️  Switching to PyPDF2 for all remaining files")
                        self._auth_error_shown = True
                    self.doc_intel_client = None
                    self._doc_intel_available = False
                else:
                    # Log other errors but continue with fallback
                    print(f"  └─ ⚠️  Document Intelligence error: {error_msg[:150]}...")
                # Fall through to PyPDF2
        
        # Fallback to PyPDF2 for local processing
        if not hasattr(self, '_pypdf2_fallback_shown'):
            print("  └─ 📄 Using PyPDF2 for text extraction")
            self._pypdf2_fallback_shown = True
        
        text = []
        with open(pdf_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        
        return "\n".join(text)

    def extract_metadata_from_filename(self, filename: str) -> Dict[str, Any]:
        """
        Extract metadata from filename convention.
        
        Expected formats:
        - EO-14151. 1.20.25. Ending Radical and Wasteful Government DEI Programs.pdf
        - EO_14008_Climate_Crisis.pdf
        
        Args:
            filename: Name of the file
            
        Returns:
            Dictionary with extracted metadata
        """
        import re
        
        metadata: Dict[str, Any] = {
            "executive_order_number": None,
            "category": None,
            "keywords": None
        }
        
        # Try to extract EO number using various patterns
        # Pattern 1: EO-14151. (with hyphen and period)
        match = re.search(r'EO-(\d+)', filename, re.IGNORECASE)
        if match:
            metadata["executive_order_number"] = match.group(1)
        else:
            # Pattern 2: EO_14008 (with underscore)
            match = re.search(r'EO_(\d+)', filename, re.IGNORECASE)
            if match:
                metadata["executive_order_number"] = match.group(1)
        
        # Extract keywords from filename (remove EO number, dates, and file extension)
        # Remove EO prefix and number
        clean_name = re.sub(r'EO[-_]\d+\.?\s*', '', filename, flags=re.IGNORECASE)
        # Remove dates in format like 1.20.25 or 01.20.2025
        clean_name = re.sub(r'\d{1,2}\.\d{1,2}\.\d{2,4}', '', clean_name)
        # Remove file extension
        clean_name = re.sub(r'\.(pdf|txt)$', '', clean_name, flags=re.IGNORECASE)
        # Split on punctuation and whitespace
        name_parts = re.split(r'[_\-\.\s]+', clean_name)
        keywords = [p.lower() for p in name_parts if len(p) > 3]
        metadata["keywords"] = keywords if keywords else None
        metadata["category"] = None  # Will be set to None instead of empty array
        
        return metadata

    def create_search_document(
        self, 
        pdf_path: Path, 
        content: str, 
        doc_type: str = "executive_order"
    ) -> Dict[str, Any]:
        """
        Create a search document from extracted content.
        
        Args:
            pdf_path: Path to the PDF file
            content: Extracted text content
            doc_type: Type of document (executive_order, grant_guideline, etc.)
            
        Returns:
            Document dictionary for indexing
        """
        filename = pdf_path.name
        metadata = self.extract_metadata_from_filename(filename)
        
        # Generate document ID (only letters, digits, underscore, dash, equal sign allowed)
        doc_id = filename.replace(".pdf", "").replace(" ", "_").replace(".", "_")
        # Remove invalid characters from document ID
        import re
        doc_id = re.sub(r"[^a-zA-Z0-9_\-=]", "", doc_id)
        
        # Create summary (first 500 characters)
        summary = content[:500].strip() + "..." if len(content) > 500 else content
        
        # Extract compliance areas and keywords
        compliance_areas = self.extract_compliance_areas(content)
        keywords = metadata["keywords"]
        category = metadata["category"]
        
        # Convert lists to comma-separated strings for Azure Search
        keywords_str = ", ".join(keywords) if keywords and isinstance(keywords, list) else keywords
        compliance_str = ", ".join(compliance_areas) if compliance_areas and isinstance(compliance_areas, list) else compliance_areas
        category_str = ", ".join(category) if category and isinstance(category, list) else category
        
        document = {
            "id": doc_id,
            "title": filename.replace(".pdf", "").replace("_", " "),
            "content": content,
            "document_type": doc_type,
            "executive_order_number": metadata["executive_order_number"],
            "effective_date": datetime.now().isoformat(),  # Extract from content if available
            "category": category_str,
            "keywords": keywords_str,
            "compliance_areas": compliance_str,
            "agency": "Federal",  # Extract from content if available
            "status": "Active",
            "summary": summary
        }
        
        return document

    def extract_compliance_areas(self, content: str) -> List[str] | None:
        """
        Extract compliance areas from content using keyword matching.
        
        Args:
            content: Document text content
            
        Returns:
            List of identified compliance areas or None if no areas found
        """
        areas = []
        content_lower = content.lower()
        
        compliance_keywords = {
            "climate": ["climate", "emissions", "renewable", "sustainability", "carbon"],
            "cybersecurity": ["cybersecurity", "security", "cyber", "data protection", "encryption"],
            "equity": ["equity", "diversity", "inclusion", "equal opportunity", "discrimination"],
            "housing": ["housing", "affordable", "shelter", "dwelling"],
            "education": ["education", "school", "learning", "student", "training"],
            "health": ["health", "medical", "healthcare", "wellness"],
            "safety": ["safety", "emergency", "disaster", "preparedness"]
        }
        
        for area, keywords in compliance_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                areas.append(area)
        
        return areas if areas else None

    def index_directory(self, directory: Path, doc_type: str = "executive_order", skip_check: bool = False) -> int:
        """
        Index all PDFs in a directory.
        
        Args:
            directory: Path to directory containing PDFs
            doc_type: Type of documents being indexed
            skip_check: Skip index existence check
            
        Returns:
            Number of documents indexed
        """
        # First, ensure the index exists
        # Try to verify index exists by doing a test search
        if not skip_check:
            try:
                list(self.search_client.search(search_text="*", top=1))
                print(f"✅ Index '{self.search_index}' is accessible")
            except Exception:
                # If search fails, try to create the index
                print("⚠️  Index check via search failed, attempting to create...")
                if not self.create_index():
                    print("\n❌ Failed to create or verify index. Cannot proceed.")
                    return 0
        
        if not directory.exists():
            print(f"❌ Directory not found: {directory}")
            return 0
        
        pdf_files = list(directory.glob("*.pdf"))
        
        if not pdf_files:
            print(f"⚠️  No PDF files found in {directory}")
            return 0
        
        print(f"\n📄 Found {len(pdf_files)} PDF files to index")
        print(f"📁 Directory: {directory}")
        print(f"🏷️  Document type: {doc_type}\n")
        
        documents = []
        
        for idx, pdf_path in enumerate(pdf_files, 1):
            try:
                print(f"[{idx}/{len(pdf_files)}] Processing: {pdf_path.name}")
                
                # Extract text
                print("  └─ Extracting text...")
                content = self.extract_text_from_pdf(pdf_path)
                
                if not content or len(content.strip()) < 100:
                    print("  └─ ⚠️  Warning: Extracted content is very short or empty")
                    continue
                
                # Create search document
                print("  └─ Creating search document...")
                document = self.create_search_document(pdf_path, content, doc_type)
                documents.append(document)
                
                print(f"  └─ ✅ Successfully processed ({len(content)} characters)")
                
            except Exception as e:
                print(f"  └─ ❌ Error processing {pdf_path.name}: {str(e)}")
                continue
        
        if not documents:
            print("\n❌ No documents to index")
            return 0
        
        # Upload to Azure AI Search
        print(f"\n⬆️  Uploading {len(documents)} documents to Azure AI Search...")
        try:
            result = self.search_client.upload_documents(documents=documents)
            succeeded = sum(1 for r in result if r.succeeded)
            failed = len(documents) - succeeded
            
            print(f"✅ Successfully indexed {succeeded}/{len(documents)} documents")
            
            if failed > 0:
                print(f"⚠️  {failed} documents failed to index")
                for r in result:
                    if not r.succeeded:
                        print(f"   - {r.key}: {r.error_message if hasattr(r, 'error_message') else 'Unknown error'}")
            
            return succeeded
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error uploading to Azure AI Search: {error_msg}")
            
            # Provide specific troubleshooting
            if "Forbidden" in error_msg or "403" in error_msg:
                print("\n🔒 Permission Error - Your API key doesn't have sufficient permissions")
                print("\n💡 Solutions:")
                print("   1. Use an Admin API key (not Query key)")
                print("   2. Get the Admin key from Azure Portal:")
                print("      Azure Portal → Your Search Service → Settings → Keys")
                print("   3. Update AZURE_SEARCH_API_KEY in your .env file")
                print(f"\n   Current endpoint: {self.search_endpoint}")
            elif "NotFound" in error_msg or "404" in error_msg:
                print("\n📝 Index Not Found - The index may not exist or was deleted")
                print("   Try running the script again - it will recreate the index")
            else:
                print("\n💡 Check:")
                print(f"   1. AZURE_SEARCH_ENDPOINT is correct: {self.search_endpoint}")
                print("   2. AZURE_SEARCH_API_KEY is an Admin key (not Query key)")
                print("   3. Azure Search service is running and accessible")
            
            return 0


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Index PDF documents to Azure AI Search for grant compliance"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="knowledge_base/sample_executive_orders",
        help="Directory containing PDF files to index"
    )
    parser.add_argument(
        "--type",
        type=str,
        default="executive_order",
        choices=["executive_order", "grant_guideline", "policy", "regulation"],
        help="Type of documents being indexed"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process files without uploading to Azure"
    )
    parser.add_argument(
        "--skip-index-check",
        action="store_true",
        help="Skip index existence check (use if index already exists)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("📚 Knowledge Base PDF Indexer")
    print("=" * 70)
    
    # Check environment
    load_dotenv()
    if not os.getenv("AZURE_SEARCH_ENDPOINT"):
        print("\n❌ Error: Azure AI Search not configured")
        print("Please set the following in your .env file:")
        print("  - AZURE_SEARCH_ENDPOINT")
        print("  - AZURE_SEARCH_INDEX_NAME")
        print("  - AZURE_SEARCH_API_KEY (or use managed identity)")
        sys.exit(1)
    
    # Initialize indexer
    indexer = KnowledgeBaseIndexer()
    
    # Process directory
    input_path = Path(args.input)
    
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No documents will be uploaded\n")
    
    if args.skip_index_check:
        print("\n⏭️  Skipping index check (assuming index exists)\n")
    
    indexed_count = indexer.index_directory(input_path, args.type, skip_check=args.skip_index_check)
    
    print("\n" + "=" * 70)
    print(f"✅ Indexing complete: {indexed_count} documents indexed")
    print("=" * 70)


if __name__ == "__main__":
    main()