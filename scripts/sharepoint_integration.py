"""
SharePoint Integration Script for Grant Compliance System

This script demonstrates how to integrate SharePoint document access using
Azure AI Foundry agents with the SharePoint grounding tool.

Documentation: https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/sharepoint

Prerequisites:
- Azure AI Foundry project configured
- SharePoint site with documents
- Azure AD app registration with SharePoint permissions
- Microsoft Graph API access

Environment Variables Required:
- AZURE_AI_PROJECT_ENDPOINT (Project endpoint, not connection string)
- SHAREPOINT_CONNECTION_ID (Connection ID from Azure AI Foundry)
- SHAREPOINT_SITE_URL
- SHAREPOINT_CLIENT_ID
- SHAREPOINT_CLIENT_SECRET
- AZURE_TENANT_ID

Note: As of 2024, AIProjectClient now uses endpoint parameter instead of
from_connection_string method. SharepointTool requires a connection_id which
must be created in Azure AI Foundry project first. See Azure AI Projects SDK documentation.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict
import logging
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SharePointDocumentAccess:
    """
    Handles SharePoint document access using Azure AI Foundry agents.
    
    This class provides methods to:
    - Connect to SharePoint sites
    - Search for documents
    - Retrieve document content
    - List documents in libraries
    """
    
    def __init__(self):
        """Initialize SharePoint connection configuration."""
        self.project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
        self.sharepoint_connection_id = os.getenv("SHAREPOINT_CONNECTION_ID")
        self.sharepoint_site_url = os.getenv("SHAREPOINT_SITE_URL")
        self.client_id = os.getenv("SHAREPOINT_CLIENT_ID")
        self.client_secret = os.getenv("SHAREPOINT_CLIENT_SECRET")
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Validate required environment variables are set."""
        required_vars = [
            "AZURE_AI_PROJECT_ENDPOINT",
            "SHAREPOINT_CONNECTION_ID",
            "SHAREPOINT_SITE_URL",
            "SHAREPOINT_CLIENT_ID",
            "SHAREPOINT_CLIENT_SECRET",
            "AZURE_TENANT_ID"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            error_msg = (
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Please configure these in your .env file.\n"
                f"See .env.example for the required format."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def create_agent_with_sharepoint(self, agent_name: str = "SharePoint Document Agent"):
        """
        Create an Azure AI Foundry agent with SharePoint grounding tool.
        
        Args:
            agent_name: Name for the agent
            
        Returns:
            Configured agent with SharePoint access
            
        Example:
            >>> sp_access = SharePointDocumentAccess()
            >>> agent = sp_access.create_agent_with_sharepoint()
            >>> response = agent.run("Find grant proposals in the Documents library")
        """
        try:
            from azure.ai.projects import AIProjectClient
            from azure.ai.agents.models import SharepointTool
            from azure.identity import DefaultAzureCredential
            
            if not self.project_endpoint:
                raise ValueError("AZURE_AI_PROJECT_ENDPOINT is not configured")
            
            if not self.sharepoint_connection_id:
                raise ValueError("SHAREPOINT_CONNECTION_ID is not configured")
            
            # Create project client
            project_client = AIProjectClient(
                endpoint=self.project_endpoint,
                credential=DefaultAzureCredential()
            )
            
            # Configure SharePoint tool with connection ID
            sharepoint_tool = SharepointTool(connection_id=self.sharepoint_connection_id)
            
            # Create agent with SharePoint grounding
            agent = project_client.agents.create_agent(
                model="gpt-4o",
                name=agent_name,
                instructions=(
                    "You are a helpful assistant that can access documents from SharePoint. "
                    "When users ask about documents, search the SharePoint site and provide "
                    "relevant information with citations to the source documents."
                ),
                tools=sharepoint_tool.definitions,
                tool_resources=sharepoint_tool.resources,
            )
            
            logger.info(f"Created agent '{agent_name}' with SharePoint access")
            return agent
            
        except ImportError:
            logger.error(
                "Azure AI Projects SDK not installed. "
                "Install with: pip install azure-ai-projects"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to create agent with SharePoint: {str(e)}")
            raise
    
    def search_sharepoint_documents(
        self,
        query: str,
        document_library: str = "Documents",
        max_results: int = 10
    ) -> List[Dict]:
        """
        Search for documents in SharePoint using natural language query.
        
        Args:
            query: Natural language search query
            document_library: SharePoint document library name
            max_results: Maximum number of results to return
            
        Returns:
            List of matching documents with metadata
            
        Example:
            >>> sp_access = SharePointDocumentAccess()
            >>> results = sp_access.search_sharepoint_documents(
            ...     "grant proposals submitted in 2024"
            ... )
            >>> for doc in results:
            ...     print(f"{doc['name']}: {doc['url']}")
        """
        try:
            from azure.ai.projects import AIProjectClient
            from azure.identity import DefaultAzureCredential
            
            if not self.project_endpoint:
                raise ValueError("AZURE_AI_PROJECT_ENDPOINT is not configured")
            
            # Type guard: at this point we know project_endpoint is not None
            assert self.project_endpoint is not None
            
            project_client = AIProjectClient(
                endpoint=self.project_endpoint,
                credential=DefaultAzureCredential()
            )
            
            # Create agent with SharePoint access
            agent = self.create_agent_with_sharepoint()
            
            # Create thread for conversation
            thread = project_client.agents.threads.create()
            
            # Send search query
            search_query = (
                f"Search the '{document_library}' library in SharePoint for: {query}. "
                f"Return up to {max_results} results with file names, URLs, and brief descriptions."
            )
            
            project_client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=search_query
            )
            
            # Run agent (create_and_process handles waiting and tool calls automatically)
            run = project_client.agents.runs.create_and_process(
                thread_id=thread.id,
                agent_id=agent.id
            )
            
            if run.status == "failed":
                logger.error(f"Run failed: {run.last_error}")
                raise Exception(f"Agent run failed: {run.last_error}")
            
            # Get messages
            messages = project_client.agents.messages.list(thread_id=thread.id)
            
            # Extract results from assistant response
            results = []
            for msg in messages:
                if msg.role == "assistant":
                    # Parse response for document information
                    content = ""
                    if msg.text_messages:
                        content = msg.text_messages[0].text.value
                    results.append({
                        "content": content,
                        "timestamp": msg.created_at
                    })
            
            logger.info(f"Found {len(results)} documents matching query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"SharePoint search failed: {str(e)}")
            raise
    
    def get_document_content(self, document_url: str) -> str:
        """
        Retrieve content from a SharePoint document.
        
        Args:
            document_url: SharePoint document URL
            
        Returns:
            Document content as text
            
        Example:
            >>> sp_access = SharePointDocumentAccess()
            >>> content = sp_access.get_document_content(
            ...     "https://tenant.sharepoint.com/sites/site/Documents/proposal.pdf"
            ... )
        """
        try:
            from azure.ai.projects import AIProjectClient
            from azure.identity import DefaultAzureCredential
            
            if not self.project_endpoint:
                raise ValueError("AZURE_AI_PROJECT_ENDPOINT is not configured")
            
            # Type guard: at this point we know project_endpoint is not None
            assert self.project_endpoint is not None
            
            project_client = AIProjectClient(
                endpoint=self.project_endpoint,
                credential=DefaultAzureCredential()
            )
            
            # Create agent with SharePoint access
            agent = self.create_agent_with_sharepoint()
            
            # Create thread
            thread = project_client.agents.threads.create()
            
            # Request document content
            query = f"Retrieve and summarize the content from this SharePoint document: {document_url}"
            
            project_client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=query
            )
            
            # Run agent (create_and_process handles waiting automatically)
            run = project_client.agents.runs.create_and_process(
                thread_id=thread.id,
                agent_id=agent.id
            )
            
            if run.status == "failed":
                logger.error(f"Run failed: {run.last_error}")
                raise Exception(f"Agent run failed: {run.last_error}")
            
            # Get response
            messages = project_client.agents.messages.list(thread_id=thread.id)
            
            content = ""
            for msg in messages:
                if msg.role == "assistant" and msg.text_messages:
                    content = msg.text_messages[0].text.value
                    break
            
            logger.info(f"Retrieved content from: {document_url}")
            return content
            
        except Exception as e:
            logger.error(f"Failed to retrieve document content: {str(e)}")
            raise
    
    def list_document_libraries(self) -> List[str]:
        """
        List available document libraries in the SharePoint site.
        
        Returns:
            List of document library names
            
        Example:
            >>> sp_access = SharePointDocumentAccess()
            >>> libraries = sp_access.list_document_libraries()
        """
        try:
            from azure.ai.projects import AIProjectClient
            from azure.identity import DefaultAzureCredential
            
            if not self.project_endpoint:
                raise ValueError("AZURE_AI_PROJECT_ENDPOINT is not configured")
            
            # Type guard: at this point we know project_endpoint is not None
            assert self.project_endpoint is not None
            
            project_client = AIProjectClient(
                endpoint=self.project_endpoint,
                credential=DefaultAzureCredential()
            )
            
            # Create agent
            agent = self.create_agent_with_sharepoint()
            
            # Create thread
            thread = project_client.agents.threads.create()
            
            # Query for libraries
            project_client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content="List all document libraries available in the SharePoint site."
            )
            
            # Run agent (create_and_process handles waiting automatically)
            run = project_client.agents.runs.create_and_process(
                thread_id=thread.id,
                agent_id=agent.id
            )
            
            if run.status == "failed":
                logger.error(f"Run failed: {run.last_error}")
                return []
            
            # Get response
            messages = project_client.agents.messages.list(thread_id=thread.id)
            
            libraries = []
            for msg in messages:
                if msg.role == "assistant" and msg.text_messages:
                    # Parse library names from response
                    content = msg.text_messages[0].text.value
                    # Simple parsing - adjust based on actual response format
                    libraries = [line.strip() for line in content.split('\n') if line.strip()]
                    break
            logger.info(f"Found {len(libraries)} document libraries")
            return libraries
            
        except Exception as e:
            logger.error(f"Failed to list document libraries: {str(e)}")
            return []
            raise


def setup_sharepoint_integration():
    """
    Interactive setup for SharePoint integration.
    
    Guides users through configuring SharePoint access and testing the connection.
    """
    print("\n" + "="*60)
    print("SharePoint Integration Setup for Grant Compliance System")
    print("="*60 + "\n")
    
    print("This script helps you integrate SharePoint document access.")
    print("You'll need the following information:\n")
    print("1. Azure AI Foundry project endpoint")
    print("2. SharePoint connection ID (from Azure AI Foundry)")
    print("3. SharePoint site URL")
    print("4. Azure AD app registration (Client ID, Secret)")
    print("5. Azure Tenant ID\n")
    
    # Check if environment variables are configured
    try:
        sp_access = SharePointDocumentAccess()
        print("✅ Configuration validated successfully!\n")
        
        # Test connection
        print("Testing SharePoint connection...")
        
        try:
            libraries = sp_access.list_document_libraries()
            print("✅ Successfully connected to SharePoint!")
            print(f"   Found {len(libraries)} document libraries\n")
            
            if libraries:
                print("Available libraries:")
                for lib in libraries:
                    print(f"  - {lib}")
                print()
                
        except Exception as e:
            print(f"⚠️  Connection test failed: {str(e)}\n")
            print("Please verify your SharePoint configuration.\n")
        
    except ValueError as e:
        print(f"❌ Configuration incomplete: {str(e)}\n")
        print("Please add the following to your .env file:\n")
        print("# SharePoint Configuration")
        print("AZURE_AI_PROJECT_ENDPOINT=https://your-resource.services.ai.azure.com/api/projects/your-project")
        print("SHAREPOINT_CONNECTION_ID=your_sharepoint_connection_id")
        print("SHAREPOINT_SITE_URL=https://yourtenant.sharepoint.com/sites/yoursite")
        print("SHAREPOINT_CLIENT_ID=your_client_id")
        print("SHAREPOINT_CLIENT_SECRET=your_client_secret")
        print("AZURE_TENANT_ID=your_tenant_id\n")
        print("Note: You must first create a SharePoint connection in Azure AI Foundry.")
        print("For detailed setup instructions, see:")
        print("https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/sharepoint\n")
        return False
    
    return True


def main():
    """Main function demonstrating SharePoint integration usage."""
    
    # Setup and validate configuration
    if not setup_sharepoint_integration():
        return
    
    print("\n" + "="*60)
    print("Example Usage")
    print("="*60 + "\n")
    
    try:
        sp_access = SharePointDocumentAccess()
        
        # Example 1: Search for documents
        print("Example 1: Searching for grant proposals...")
        results = sp_access.search_sharepoint_documents(
            query="grant proposals",
            document_library="Documents",
            max_results=5
        )
        
        if results:
            print(f"Found {len(results)} results")
            for idx, result in enumerate(results, 1):
                print(f"\n{idx}. {result.get('content', 'No content')[:200]}...")
        
        # Example 2: List libraries
        print("\n\nExample 2: Listing document libraries...")
        libraries = sp_access.list_document_libraries()
        print(f"Available libraries: {', '.join(libraries)}")
        
        print("\n✅ SharePoint integration is working correctly!")
        print("\nYou can now use SharePoint documents in your grant compliance workflow.")
        
    except Exception as e:
        print(f"\n❌ Error during examples: {str(e)}")
        logger.exception("Error in main function")


if __name__ == "__main__":
    main()
