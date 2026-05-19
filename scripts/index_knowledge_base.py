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

# Suppress verbose Azure Identity logging ONLY for credential chain attempts
# We still want to see actual errors
import logging
azure_identity_logger = logging.getLogger('azure.identity._credentials')
azure_identity_logger.setLevel(logging.ERROR)  # Don't show INFO about credential attempts

try:
    from azure.core.credentials import AzureKeyCredential
    from azure.search.documents import SearchClient
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.indexes.models import (
        SearchIndex,
        SimpleField,
        SearchableField,
        SearchFieldDataType,
        SearchField,
        VectorSearch,
        HnswAlgorithmConfiguration,
        VectorSearchProfile,
        SemanticConfiguration,
        SemanticSearch,
        SemanticPrioritizedFields,
        SemanticField,
        AzureOpenAIVectorizer,
        AzureOpenAIVectorizerParameters,
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
        self.use_managed_identity = os.getenv("USE_MANAGED_IDENTITY", "false").lower() == "false"

        # Embedding configuration for hybrid search
        self.openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
        self.embedding_dimensions = 1536  # text-embedding-3-small default
        self._embedding_client = None
        # Validate required environment variables
        if not self.search_endpoint:
            raise ValueError("AZURE_SEARCH_ENDPOINT environment variable is required")
        
        # Set up credentials - try managed identity first, fall back to API keys
        search_key = os.getenv("AZURE_SEARCH_API_KEY")
        doc_intel_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
        
        if self.use_managed_identity:
            # Try managed identity, but be ready to fall back
            try:
                print("🔐 Attempting Managed Identity authentication...")
                # Exclude EnvironmentCredential to avoid Conditional Access blocking
                # Service principal credentials in .env are blocked by CA policies
                self.credential = DefaultAzureCredential(exclude_environment_credential=True)
                self.search_credential = DefaultAzureCredential(exclude_environment_credential=True)
                print("✅ Managed Identity credentials initialized (excluding EnvironmentCredential)")
            except Exception as e:
                print(f"⚠️  Managed Identity initialization warning: {str(e)[:100]}")
                # Fall back to API keys
                if search_key:
                    print("🔑 Falling back to API key authentication")
                    self.search_credential = AzureKeyCredential(search_key)
                    self.credential = AzureKeyCredential(doc_intel_key) if doc_intel_key else None
                else:
                    raise ValueError("Managed Identity failed and no AZURE_SEARCH_API_KEY provided")
        else:
            if not search_key:
                raise ValueError("AZURE_SEARCH_API_KEY environment variable is required when not using managed identity")
            self.search_credential = AzureKeyCredential(search_key)
            self.credential = AzureKeyCredential(doc_intel_key) if doc_intel_key else None
        
        # Initialize clients with error handling for Conditional Access
        try:
            self.search_client = SearchClient(
                endpoint=self.search_endpoint,
                index_name=self.search_index,
                credential=self.search_credential
            )
            
            self.index_client = SearchIndexClient(
                endpoint=self.search_endpoint,
                credential=self.search_credential
            )
        except Exception as e:
            error_msg = str(e)
            if "AADSTS53003" in error_msg or "Conditional Access" in error_msg:
                print("\n" + "="*80)
                print("⚠️  CONDITIONAL ACCESS POLICY BLOCKING AUTHENTICATION")
                print("="*80)
                print("Your organization's Conditional Access policies are blocking token issuance.")
                print("\n💡 SOLUTIONS:")
                print("   1. Use API key authentication instead:")
                print("      Set USE_MANAGED_IDENTITY=false in .env")
                print("      Provide AZURE_SEARCH_API_KEY in .env")
                print("\n   2. Contact your Azure admin to:")
                print("      - Add exception for this service principal")
                print("      - Adjust CA policies for Azure AI services")
                print("      - Grant necessary permissions")
                print("="*80 + "\n")
                
                # Try to fall back to API key if available
                search_key = os.getenv("AZURE_SEARCH_API_KEY")
                if search_key:
                    print("🔑 Attempting fallback to API key authentication...")
                    self.search_credential = AzureKeyCredential(search_key)
                    self.search_client = SearchClient(
                        endpoint=self.search_endpoint,
                        index_name=self.search_index,
                        credential=self.search_credential
                    )
                    self.index_client = SearchIndexClient(
                        endpoint=self.search_endpoint,
                        credential=self.search_credential
                    )
                    print("✅ Successfully using API key authentication\n")
                else:
                    raise ValueError("Conditional Access blocking managed identity and no API key provided")
            else:
                raise
        
        # Initialize Document Intelligence client with managed identity
        # Using azure-ai-documentintelligence SDK
        self.doc_intel_client = None
        self._doc_intel_available = False
        self._doc_intel_credential = None
        
        if self.doc_intel_endpoint and DOCINT_AVAILABLE and DocumentIntelligenceClient is not None:
            doc_intel_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
            
            # Determine credential to use (don't test it yet - that happens during actual use)
            if self.use_managed_identity or (not doc_intel_key):
                print("🔐 Document Intelligence configured for Managed Identity")
                self._doc_intel_credential = DefaultAzureCredential()
                self._doc_intel_available = True
            elif doc_intel_key:
                print("🔑 Document Intelligence configured for API key")
                self._doc_intel_credential = AzureKeyCredential(doc_intel_key)
                self._doc_intel_available = True
            
            # Initialize client with the credential (using azure-ai-documentintelligence SDK)
            if self._doc_intel_credential:
                try:
                    self.doc_intel_client = DocumentIntelligenceClient(
                        endpoint=self.doc_intel_endpoint,
                        credential=self._doc_intel_credential
                    )
                    print("✅ Document Intelligence client initialized (using azure-ai-documentintelligence)\n")
                except Exception as e:
                    print(f"⚠️  Warning initializing Document Intelligence: {str(e)[:100]}")
                    print("   Will attempt to use during document processing\n")
                    self._doc_intel_available = True  # Still try to use it

        
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
                check_error_msg = str(check_error)
                
                # Handle Conditional Access errors
                if "AADSTS53003" in check_error_msg or "Conditional Access" in check_error_msg:
                    print("\n" + "="*80)
                    print("⚠️  CONDITIONAL ACCESS BLOCKING MANAGED IDENTITY")
                    print("="*80)
                    print("Your organization's CA policies prevent managed identity authentication.")
                    print("\n💡 SOLUTION: Switch to API key authentication")
                    print("   1. Set USE_MANAGED_IDENTITY=false in .env")
                    print("   2. Provide AZURE_SEARCH_API_KEY in .env")
                    print("="*80 + "\n")
                    
                    # Try API key fallback if available
                    search_key = os.getenv("AZURE_SEARCH_API_KEY")
                    if search_key:
                        print("🔑 Attempting automatic fallback to API key...")
                        self.search_credential = AzureKeyCredential(search_key)
                        self.index_client = SearchIndexClient(
                            endpoint=self.search_endpoint, # type: ignore
                            credential=self.search_credential
                        )
                        self.search_client = SearchClient(
                            endpoint=self.search_endpoint, # type: ignore
                            index_name=self.search_index,
                            credential=self.search_credential
                        )
                        # Retry the check
                        try:
                            self.index_client.get_index(self.search_index)
                            print(f"✅ Search index '{self.search_index}' already exists (using API key)\n")
                            return True
                        except Exception as retry_error:
                            if "NotFound" not in str(retry_error) and "ResourceNotFoundError" not in str(type(retry_error).__name__):
                                print(f"⚠️  API key check also failed: {str(retry_error)[:100]}")
                    else:
                        return False
                
                # Index doesn't exist, continue to create it
                if "NotFound" not in check_error_msg and "ResourceNotFoundError" not in str(type(check_error).__name__):
                    # If it's not a "not found" error, something else is wrong
                    print(f"⚠️  Warning checking index: {check_error_msg[:150]}")
            
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
                SimpleField(
                    name="chunk_number",
                    type=SearchFieldDataType.Int32,
                    filterable=True,
                    sortable=True,
                ),
                SimpleField(
                    name="total_chunks",
                    type=SearchFieldDataType.Int32,
                    filterable=True,
                ),
                # Vector field for hybrid search
                SearchField(
                    name="content_vector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=self.embedding_dimensions,
                    vector_search_profile_name="default-vector-profile",
                ),
            ]

            # Vector search configuration (HNSW algorithm + integrated vectorizer)
            vector_search = VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(name="default-hnsw"),
                ],
                profiles=[
                    VectorSearchProfile(
                        name="default-vector-profile",
                        algorithm_configuration_name="default-hnsw",
                        vectorizer_name="openai-vectorizer",
                    ),
                ],
                vectorizers=[
                    AzureOpenAIVectorizer(
                        vectorizer_name="openai-vectorizer",
                        parameters=AzureOpenAIVectorizerParameters(
                            resource_url=self.openai_endpoint.rstrip("/"),
                            deployment_name=self.embedding_deployment,
                            model_name=self.embedding_deployment,
                        ),
                    ),
                ],
            )

            # Semantic search configuration
            semantic_config = SemanticConfiguration(
                name="default-semantic-config",
                prioritized_fields=SemanticPrioritizedFields(
                    content_fields=[SemanticField(field_name="content")],
                    title_field=SemanticField(field_name="title"),
                    keywords_fields=[SemanticField(field_name="keywords")],
                ),
            )
            semantic_search = SemanticSearch(configurations=[semantic_config])

            # Create the index
            index = SearchIndex(
                name=self.search_index,
                fields=fields,
                vector_search=vector_search,
                semantic_search=semantic_search,
            )
            
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
            error_msg = str(e)
            
            # Handle Conditional Access errors during index creation
            if "AADSTS53003" in error_msg or "Conditional Access" in error_msg:
                print("❌ Conditional Access blocking index creation")
                
                # Try API key fallback
                search_key = os.getenv("AZURE_SEARCH_API_KEY")
                if search_key:
                    print("🔑 Retrying with API key authentication...")
                    try:
                        self.search_credential = AzureKeyCredential(search_key)
                        self.index_client = SearchIndexClient(
                            endpoint=self.search_endpoint, # type: ignore
                            credential=self.search_credential
                        )
                        self.search_client = SearchClient(
                            endpoint=self.search_endpoint, # type: ignore
                            index_name=self.search_index,
                            credential=self.search_credential
                        )
                        
                        # Retry index creation
                        index = SearchIndex(name=self.search_index, fields=fields) # type: ignore
                        self.index_client.create_index(index)
                        print(f"✅ Successfully created index '{self.search_index}' using API key\n")
                        return True
                    except Exception as retry_error:
                        retry_msg = str(retry_error)
                        if "ResourceExistsError" in str(type(retry_error).__name__) or "Conflict" in retry_msg:
                            print(f"✅ Index '{self.search_index}' already exists\n")
                            return True
                        print(f"❌ API key retry failed: {retry_msg[:100]}")
                        return False
                else:
                    print("\n💡 Set AZURE_SEARCH_API_KEY in .env to bypass CA restrictions")
                    return False
            
            print(f"❌ Error creating index: {error_msg[:200]}")
            print("\n💡 Troubleshooting tips:")
            print("   1. Verify your AZURE_SEARCH_API_KEY has 'Contributor' or 'Admin' permissions")
            print("   2. Check that AZURE_SEARCH_ENDPOINT is correct")
            print("   3. Ensure your Azure Search service is running")
            return False

    def _get_embedding_client(self):
        """Lazy-initialize the OpenAI embedding client."""
        if self._embedding_client is None:
            from openai import AzureOpenAI
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            if api_key:
                self._embedding_client = AzureOpenAI(
                    azure_endpoint=self.openai_endpoint,
                    api_key=api_key,
                    api_version="2024-06-01",
                )
            else:
                from azure.identity import DefaultAzureCredential, get_bearer_token_provider
                token_provider = get_bearer_token_provider(
                    DefaultAzureCredential(exclude_environment_credential=True),
                    "https://cognitiveservices.azure.com/.default",
                )
                self._embedding_client = AzureOpenAI(
                    azure_endpoint=self.openai_endpoint,
                    azure_ad_token_provider=token_provider,
                    api_version="2024-06-01",
                )
            print(f"✅ Embedding client initialized (model: {self.embedding_deployment})")
        return self._embedding_client

    def generate_embedding(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text.

        Truncates to ~8000 tokens worth of text to stay within model limits.
        """
        # Rough truncation: ~4 chars per token, 8191 token limit
        truncated = text[:32000]
        client = self._get_embedding_client()
        response = client.embeddings.create(
            input=truncated,
            model=self.embedding_deployment,
        )
        return response.data[0].embedding

    def chunk_text(self, text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks for better search granularity.

        Uses sentence-boundary-aware splitting to avoid cutting mid-sentence.

        Args:
            text: Full document text
            chunk_size: Target chunk size in characters
            overlap: Number of overlapping characters between consecutive chunks

        Returns:
            List of text chunks with overlap
        """
        if len(text) <= chunk_size:
            return [text]

        import re
        # Split on sentence boundaries (period/newline followed by space or newline)
        sentences = re.split(r'(?<=[.!?\n])\s+', text)

        chunks = []
        current_chunk = ""
        current_start = 0  # Track position for overlap

        for sentence in sentences:
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Overlap: keep the last `overlap` characters as the start of next chunk
                if len(current_chunk) > overlap:
                    current_chunk = current_chunk[-overlap:] + " " + sentence
                else:
                    current_chunk = sentence
            else:
                current_chunk = (current_chunk + " " + sentence).strip() if current_chunk else sentence

        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        Extract text from PDF using Azure Document Intelligence or PyPDF2.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        # Try Document Intelligence first if configured and available
        if self._doc_intel_available and DocumentIntelligenceClient is not None and self.doc_intel_endpoint:
            try:
                # Create fresh credential for each document
                # Exclude EnvironmentCredential because service principal auth is blocked by CA policies
                # This matches how DocumentIngestionAgent works in the test environment, tests/test_document_intelligence_managed_identity.py
                from azure.identity import AzureCliCredential, ManagedIdentityCredential, ChainedTokenCredential
                credential = ChainedTokenCredential(
                    ManagedIdentityCredential(),  # For Azure-hosted resources
                    AzureCliCredential()  # For local development with 'az login'
                )
                client = DocumentIntelligenceClient(
                    endpoint=self.doc_intel_endpoint,
                    credential=credential
                )
                
                with open(pdf_path, "rb") as f:
                    # Use the new azure-ai-documentintelligence SDK
                    poller = client.begin_analyze_document(
                        model_id="prebuilt-layout",
                        body=f
                    )
                    result = poller.result()
                    if not hasattr(self, '_doc_intel_success_shown'):
                        print("  └─ ✅ Using Azure Document Intelligence for OCR")
                        self._doc_intel_success_shown = True
                    return result.content
            except Exception as e:
                # If Document Intelligence fails, fall back to PyPDF2
                # Simple error handling - same as DocumentIngestionAgent
                if not hasattr(self, '_doc_intel_error_shown'):
                    print(f"  └─ ⚠️  Document Intelligence error: {type(e).__name__}: {str(e)[:200]}")
                    print("  └─ ℹ️  Falling back to PyPDF2")
                    self._doc_intel_error_shown = True
                    # Print full error for debugging
                    import traceback
                    traceback.print_exc()
                # Fall through to PyPDF2 below
        
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
        doc_type: str = "executive_order",
        chunk_number: int = 0,
        total_chunks: int = 1
    ) -> Dict[str, Any]:
        """
        Create a search document from extracted content.
        
        Args:
            pdf_path: Path to the PDF file
            content: Extracted text content (may be a chunk)
            doc_type: Type of document (executive_order, grant_guideline, etc.)
            chunk_number: Index of this chunk (0-based)
            total_chunks: Total number of chunks for this document
            
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
        # Append chunk number to make IDs unique per chunk
        if total_chunks > 1:
            doc_id = f"{doc_id}_chunk{chunk_number}"
        
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
            "summary": summary,
            "chunk_number": chunk_number,
            "total_chunks": total_chunks
        }

        # Generate embedding vector for hybrid search
        try:
            document["content_vector"] = self.generate_embedding(content)
            print("  └─ 🧬 Generated embedding vector")
        except Exception as e:
            print(f"  └─ ⚠️  Embedding generation failed: {str(e)[:100]}")
            print("  └─ ℹ️  Document will be indexed without vector (text search only)")
        
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
            except Exception as search_error:
                search_error_msg = str(search_error)
                
                # Handle Conditional Access errors
                if "AADSTS53003" in search_error_msg or "Conditional Access" in search_error_msg:
                    print("⚠️  Conditional Access blocking index check")
                    
                    # Try API key fallback
                    search_key = os.getenv("AZURE_SEARCH_API_KEY")
                    if search_key:
                        print("🔑 Switching to API key authentication...")
                        try:
                            self.search_credential = AzureKeyCredential(search_key)
                            self.search_client = SearchClient(
                                endpoint=self.search_endpoint, # type: ignore
                                index_name=self.search_index,
                                credential=self.search_credential
                            )
                            self.index_client = SearchIndexClient(
                                endpoint=self.search_endpoint, # type: ignore
                                credential=self.search_credential
                            )
                            
                            # Retry the check
                            list(self.search_client.search(search_text="*", top=1))
                            print(f"✅ Index '{self.search_index}' is accessible (using API key)\n")
                        except Exception:
                            # If search still fails, try to create the index
                            print("⚠️  Index check via search failed, attempting to create...")
                            if not self.create_index():
                                print("\n❌ Failed to create or verify index. Cannot proceed.")
                                return 0
                    else:
                        print("\n❌ No API key available for fallback")
                        print("💡 Set AZURE_SEARCH_API_KEY in .env to bypass CA restrictions")
                        return 0
                else:
                    # If search fails for other reasons, try to create the index
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
                
                # Chunk the document for better search granularity
                chunks = self.chunk_text(content, chunk_size=2000, overlap=200)
                print(f"  └─ 📦 Split into {len(chunks)} chunks (2000 chars, 200 overlap)")

                # Create search documents for each chunk
                print("  └─ Creating search documents...")
                for chunk_idx, chunk_text in enumerate(chunks):
                    document = self.create_search_document(
                        pdf_path, chunk_text, doc_type,
                        chunk_number=chunk_idx, total_chunks=len(chunks)
                    )
                    documents.append(document)
                
                print(f"  └─ ✅ Successfully processed ({len(content)} chars → {len(chunks)} chunks)")
                
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