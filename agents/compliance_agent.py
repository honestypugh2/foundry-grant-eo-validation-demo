"""
Compliance Agent for Grant Proposal Review

This agent analyzes grant proposals for compliance with executive orders
using Azure AI Foundry and Azure AI Search for knowledge base retrieval.
"""

import os
from typing import Annotated, Optional, Dict, Any
from agent_framework import ChatAgent, CitationAnnotation, TextSpanRegion
from agent_framework_azure_ai import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient


class ComplianceAgent:
    """
    AI Agent for analyzing grant proposal compliance with executive orders.
    """

    def __init__(
        self,
        project_endpoint: str,
        model_deployment_name: str,
        search_endpoint: str,
        search_index_name: str,
        azure_search_document_truncation_size: int,
        use_managed_identity: bool = True,
        search_api_key: Optional[str] = None,
    ):
        """
        Initialize the Compliance Agent.

        Args:
            project_endpoint: Azure AI Foundry project endpoint
            model_deployment_name: Name of the deployed model
            search_endpoint: Azure AI Search service endpoint
            search_index_name: Name of the search index for executive orders
            azure_search_document_truncation_size: Document content truncation size for search results
            use_managed_identity: Whether to use Managed Identity for authentication
            search_api_key: API key for Azure Search (if not using managed identity)
        """
        self.project_endpoint = project_endpoint
        self.model_deployment_name = model_deployment_name
        self.search_endpoint = search_endpoint
        self.search_index_name = search_index_name
        self.use_managed_identity = use_managed_identity
        self.azure_search_document_truncation_size = azure_search_document_truncation_size
        
        # Agent will be created on first use and reused
        self._agent = None
        self._credential = None

        # Set up credentials
        if use_managed_identity:
            # Exclude EnvironmentCredential to avoid Conditional Access blocking
            # Service principal credentials in .env may be blocked by CA policies or have invalid values
            self.credential = DefaultAzureCredential(exclude_environment_credential=True)
            self.search_credential = DefaultAzureCredential(exclude_environment_credential=True)
        else:
            self.credential = None  # Will use API key in client
            if search_api_key is None:
                raise ValueError("search_api_key must be provided when not using managed identity")
            self.search_credential = AzureKeyCredential(search_api_key)

        # Initialize search client
        self.search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=search_index_name,
            credential=self.search_credential,
        )

        # Agent instructions
        self.instructions = """You are a legal compliance analyst specializing in grant proposal review.

Your responsibilities:
1. Analyze grant proposals for compliance with relevant executive orders against a knowledge base of executive orders
2. Identify potential compliance issues or concerns
3. Provide detailed insights into how well the grant aligns with current legal standards (executive orders and agency guidance) and highlight specific clauses or phrases that may pose compliance risks (for example, address DEI initiatives, green new deal, gender ideology, immigration)
4. Provide structured compliance summaries with specific citations
5. Assign confidence scores to your analysis (0-100)
6. Highlight areas requiring attorney review

When analyzing documents:
- Search the knowledge base for relevant executive orders
- Quote specific sections that apply to the grant proposal
- Explain how the proposal aligns or conflicts with requirements
- Be thorough but concise
- Flag ambiguous areas for human review

Output Format:
- Overall Compliance Status: [Compliant/Non-Compliant/Requires Review]
- Confidence Score: [0-100]
- Key Findings: [Bullet points]
- Relevant Executive Orders: [List with citations]
- Concerns: [Any issues identified]
- Recommendations: [Actions needed]
"""

    async def search_knowledge_base(
        self, query: Annotated[str, "The search query for finding relevant executive orders"]
    ) -> str:
        """
        Search the knowledge base for relevant executive orders and compliance guidelines.

        This tool performs semantic search against indexed executive orders and returns
        the most relevant documents with their content and metadata.
        """
        try:
            # Perform semantic search
            results = await self.search_client.search(
                search_text=query, top=5, include_total_count=True
            )

            # Format results
            formatted_results = []
            idx = 1
            async for result in results:
                doc_title = result.get("title", "Untitled Document")
                doc_content = result.get("content", "")
                doc_number = result.get("executive_order_number", "N/A")
                doc_date = result.get("effective_date", "N/A")

                formatted_results.append(
                    f"\n--- Document {idx}: {doc_title} ---\n"
                    f"Executive Order Number: {doc_number}\n"
                    f"Effective Date: {doc_date}\n"
                    f"Content:\n{doc_content[:self.azure_search_document_truncation_size]}...\n"
                )
                idx += 1

            if not formatted_results:
                return "No relevant executive orders found in the knowledge base."

            return "\n".join(formatted_results)

        except Exception as e:
            return f"Error searching knowledge base: {str(e)}"

    def format_grant_context(
        self,
        context_data: Annotated[
            str, "JSON string containing pre-extracted metadata, summary, and document info"
        ],
    ) -> str:
        """
        Format pre-extracted grant proposal context for analysis.
        
        This tool formats metadata and context that was already extracted
        during document ingestion, making it easier for the agent to reference.
        Note: Document Intelligence processing already happened in document_ingestion_agent.
        """
        try:
            import json
            context = json.loads(context_data)
        except Exception:
            context = {}
        
        metadata = context.get('metadata', {})
        summary = context.get('summary', {})
        
        formatted = ["\n=== Grant Proposal Context ==="]
        
        # Document info
        formatted.append(f"\nDocument: {metadata.get('file_name', 'Unknown')}")
        formatted.append(f"Pages: {metadata.get('page_count', 'N/A')}")
        formatted.append(f"Word Count: {metadata.get('word_count', 'N/A')}")
        
        # Extracted metadata (from Document Intelligence in Step 1)
        if metadata.get('deadline'):
            formatted.append(f"Deadline: {metadata['deadline']}")
        if metadata.get('budget_amount'):
            formatted.append(f"Budget Amount: {metadata['budget_amount']}")
        if metadata.get('applicant'):
            formatted.append(f"Applicant: {metadata['applicant']}")
        if metadata.get('document_type'):
            formatted.append(f"Document Type: {metadata['document_type']}")
        
        # Summary info (from SummarizationAgent in Step 2)
        formatted.append("\n--- Summary Information ---")
        
        if summary.get('executive_summary'):
            formatted.append(f"\nExecutive Summary: {summary['executive_summary']}...") # [:300]
        
        if summary.get('key_topics'):
            topics = summary['key_topics']
            if isinstance(topics, list):
                formatted.append(f"\nKey Topics: {', '.join(topics)}")
            else:
                formatted.append(f"\nKey Topics: {topics}")
        
        if summary.get('key_clauses'):
            clauses = summary['key_clauses']
            if isinstance(clauses, list) and clauses:
                formatted.append(f"\nKey Clauses Identified: {len(clauses)}")
                # Show first 2 clauses as examples
                for i, clause in enumerate(clauses[:2], 1):
                    clause_preview = clause[:150] + "..." if len(clause) > 150 else clause
                    formatted.append(f"  {i}. {clause_preview}")
        
        formatted.append("\n(Document metadata extracted via Document Intelligence in Step 1)")
        formatted.append("(Summary generated by SummarizationAgent in Step 2)")
        
        return "\n".join(formatted)

    def create_citation_for_document(self, doc_info, text_snippet, start_index, end_index):
        """
        Create a properly formatted citation annotation for a document excerpt.
        """
        # Create text span region for the citation
        text_region = TextSpanRegion(
            start_index=start_index,
            end_index=end_index
        )
        
        # Build file path or URL for the executive order PDF
        file_path = doc_info.get('file_path', '')
        page_number = doc_info.get('page_number', 1)
        
        # Create citation with exact location information
        citation = CitationAnnotation(
            title=f"{doc_info.get('title', 'Executive Order')} (Page {page_number})",
            url=file_path if file_path.startswith('http') else f"file://{file_path}#page={page_number}",
            file_id=doc_info.get('id', ''),
            tool_name="search_knowledge_base",
            snippet=text_snippet,
            annotated_regions=[text_region],
            additional_properties={
                "executive_order_number": doc_info.get('exec_order_number', 'N/A'),
                "effective_date": doc_info.get('date', 'N/A'),
                "page_number": page_number,
                "document_type": "Executive Order"
            }
        )
        
        return citation


    async def create_agent(self) -> ChatAgent:
        """
        Create and configure the compliance agent with tools.
        Agent is reused across multiple calls to avoid recreation/deletion.

        Returns:
            Configured ChatAgent instance
        """
        # Return cached agent if already created
        if self._agent is not None:
            return self._agent
            
        # Create chat client
        # Note: Azure AI Foundry agents require a credential
        # For local development with Azure CLI: use DefaultAzureCredential with exclude_environment_credential
        # For production with Managed Identity: use DefaultAzureCredential without exclusions
        from azure.identity.aio import DefaultAzureCredential
        
        # Exclude environment credential to avoid service principal auth issues in local dev
        # This allows Azure CLI credential to work properly
        if self._credential is None:
            self._credential = DefaultAzureCredential(exclude_environment_credential=True)
        
        chat_client = AzureAIAgentClient(
            project_endpoint=self.project_endpoint,
            model_deployment_name=self.model_deployment_name,
            async_credential=self._credential,
            agent_name="ComplianceAgent",
        )

        # Create agent with tools - don't use context manager to prevent auto-deletion
        self._agent = ChatAgent(
            chat_client=chat_client,
            instructions=self.instructions,
            tools=[self.search_knowledge_base, self.format_grant_context],
        )

        return self._agent

    async def analyze_proposal(
        self, proposal_text: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a grant proposal for compliance with executive orders.

        Args:
            proposal_text: The full text of the grant proposal
            context: Additional context (department, previous grants, etc.)

        Returns:
            Dictionary containing compliance analysis results with:
            - analysis: Full text analysis with citations
            - confidence_score: AI's certainty in analysis (0-100)
            - status: Compliant/Non-Compliant/Requires Review
            - relevant_executive_orders: List of applicable EOs with citations
            
        SCORES RETURNED:
        
        confidence_score (0-100):
            How certain the AI is about its analysis
            - 90-100: Very reliable, proceed with standard review
            - 70-89: Reliable, may need minor clarification
            - 50-69: Significant uncertainty, prioritize manual review
            - <50: Unreliable, require immediate expert review
            
            This score is also used as the compliance_score in the risk calculation.
            
        See docs/SCORING_SYSTEM.md for complete scoring documentation.
        """
        # Get or create the agent (will be reused)
        agent = await self.create_agent()
        
        # Create thread for this analysis
        thread = agent.get_new_thread()

        # Build analysis prompt
        import json
        context_json = json.dumps(context) if context else "{}"
        
        prompt = f"""Analyze the following grant proposal for compliance with executive orders:

GRANT PROPOSAL:
{proposal_text}

"""
        if context:
            prompt += f"\nADDITIONAL CONTEXT (use format_grant_context tool to view formatted):\n{context_json}\n"

        prompt += """
Please perform a thorough compliance analysis using the following steps:
1. Use format_grant_context tool to review the pre-extracted document metadata and summary
2. Search the knowledge base for relevant executive orders using search_knowledge_base tool
3. Identify applicable compliance requirements from the executive orders
4. Assess the proposal against these requirements
5. Provide a structured compliance summary with confidence score

Note: Document metadata has already been extracted using Azure Document Intelligence during ingestion.
"""

        # Get analysis from agent
        response_text = ""
        async for chunk in agent.run_stream(prompt, thread=thread):
            if chunk.text:
                response_text += chunk.text

        # Extract citations from thread messages after run completes
        citations = await self._extract_citations_from_thread(agent, thread)

        # Parse response into structured format
        # In production, you might want to use structured outputs or JSON mode
        result = {
            "analysis": response_text,
            "confidence_score": self._extract_confidence_score(response_text),
            "status": self._extract_status(response_text),
            "relevant_executive_orders": self._extract_relevant_executive_orders(response_text),
            "citations": citations,
            "thread_id": None,
        }

        return result

    def _extract_confidence_score(self, text: str) -> int:
        """
        Extract confidence score from analysis text.
        
        CONFIDENCE SCORE (0-100):
        - Measures how certain the AI is about its compliance analysis
        - Higher score = more reliable AI recommendations
        
        Score Ranges:
        - 90-100: Very high confidence - AI is very certain
        - 70-89: High confidence - Generally reliable
        - 50-69: Moderate confidence - Manual review strongly recommended
        - <50: Low confidence - Immediate human expert review required
        
        Impact:
        - Low confidence (<60%) increases risk score
        - Used to determine priority of attorney review
        - Indicates reliability of AI analysis
        
        See docs/SCORING_SYSTEM.md for complete documentation.
        """
        # Simple regex-based extraction
        import re

        match = re.search(r"confidence\s*score[:\s]*(\d+)", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 70  # Default confidence if not found

    def _extract_status(self, text: str) -> str:
        """Extract compliance status from analysis text."""
        text_lower = text.lower()
        if "compliant" in text_lower and "non-compliant" not in text_lower:
            return "Compliant"
        elif "non-compliant" in text_lower:
            return "Non-Compliant"
        else:
            return "Requires Review"
    
    def _extract_relevant_executive_orders(self, text: str) -> list:
        """Extract relevant executive orders from analysis text."""
        import re
        
        executive_orders = []
        
        # Pattern to match EO numbers (14151, 14173, etc.)
        eo_pattern = r'(?:Executive Order|EO|E\.O\.)[\s#]*(\d{5})'
        matches = re.findall(eo_pattern, text, re.IGNORECASE)
        
        # Get unique EO numbers
        unique_eos = list(set(matches))
        
        # For each EO number found, try to extract more context
        for eo_num in unique_eos:
            # Look for the EO in context
            eo_context_pattern = rf'(?:Executive Order|EO|E\.O\.)[\s#]*{eo_num}[^\n]*(?:\n[^\n]*)?(?:\n[^\n]*)?'
            context_match = re.search(eo_context_pattern, text, re.IGNORECASE | re.MULTILINE)
            
            context_text = context_match.group(0) if context_match else f"Executive Order {eo_num}"
            
            # Extract title if available (text after EO number, before date or section)
            title_match = re.search(rf'{eo_num}[^\n]*?[\u2013\-]\s*([^\n(]+)', text)
            title = title_match.group(1).strip() if title_match else f"Executive Order {eo_num}"
            
            executive_orders.append({
                'name': f"EO {eo_num}",
                'number': eo_num,
                'title': title[:100],  # Limit title length
                'relevance': 85.0,  # Default relevance score
                'key_requirements': [context_text[:300]]  # First 300 chars of context
            })
        
        return executive_orders

    async def _extract_citations_from_thread(self, agent: ChatAgent, thread) -> list:
        """
        Extract citations from the agent's thread messages.
        
        The Agent Framework automatically creates citations when tools return document content.
        This method attempts to retrieve them from the thread.
        
        Note: Citation extraction from the Agent Framework is not fully supported yet.
        We return an empty list and rely on the search_knowledge_base tool results 
        being referenced in the analysis text.
        """
        citations_list = []
        
        try:
            # Attempt 1: Check if thread has a messages attribute directly
            if hasattr(thread, 'messages') and thread.messages:
                for message in thread.messages:
                    if hasattr(message, 'annotations') and message.annotations:
                        for annotation in message.annotations:
                            if isinstance(annotation, CitationAnnotation):
                                citations_list.append(annotation)
            
            # Attempt 2: Check if thread has a method to get messages
            elif hasattr(thread, 'get_messages'):
                messages = await thread.get_messages()
                for message in messages:
                    if hasattr(message, 'annotations') and message.annotations:
                        for annotation in message.annotations:
                            if isinstance(annotation, CitationAnnotation):
                                citations_list.append(annotation)
                                
        except Exception as e:
            # Citation extraction failed - this is expected behavior
            # The tool output is still visible in the analysis text
            print(f"Info: Citation auto-extraction not available: {e}")
            return []
        
        # Format citations for API response
        if citations_list:
            return self._format_citations(citations_list)
        
        return []

    def _format_citations(self, citations: list) -> list:
        """
        Format citation annotations for frontend display.
        
        Converts Agent Framework CitationAnnotation objects into
        dictionaries with all relevant metadata including page numbers.
        """
        formatted_citations = []
        
        for citation in citations:
            # Convert CitationAnnotation to dictionary
            citation_dict = {
                'title': citation.title if hasattr(citation, 'title') else 'Untitled',
                'url': citation.url if hasattr(citation, 'url') else None,
                'file_id': citation.file_id if hasattr(citation, 'file_id') else None,
                'tool_name': citation.tool_name if hasattr(citation, 'tool_name') else None,
                'snippet': citation.snippet if hasattr(citation, 'snippet') else None,
                'annotated_regions': [],
                'additional_properties': {}
            }
            
            # Extract annotated regions (text spans)
            if hasattr(citation, 'annotated_regions') and citation.annotated_regions:
                for region in citation.annotated_regions:
                    citation_dict['annotated_regions'].append({
                        'start_index': region.start_index if hasattr(region, 'start_index') else 0,
                        'end_index': region.end_index if hasattr(region, 'end_index') else 0
                    })
            
            # Extract additional properties (including page_number)
            if hasattr(citation, 'additional_properties') and citation.additional_properties:
                citation_dict['additional_properties'] = dict(citation.additional_properties)
            
            formatted_citations.append(citation_dict)
        
        return formatted_citations


    async def cleanup(self):
        """
        Cleanup resources and optionally delete the agent.
        Call this when you're done with the agent to free resources.
        """
        if self._agent is not None:
            # Agent cleanup handled by Azure AI Foundry SDK
            self._agent = None
        
        if self.search_client:
            await self.search_client.close()
        
        if self._credential and hasattr(self._credential, 'close'):
            await self._credential.close()


async def main():
    """Example usage of the Compliance Agent."""
    from dotenv import load_dotenv

    load_dotenv()

    # Initialize agent
    use_managed_identity = os.getenv("USE_MANAGED_IDENTITY", "false").lower() == "true"
    
    agent = ComplianceAgent(
        project_endpoint=os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT") or os.getenv("AZURE_AI_PROJECT_ENDPOINT") or "",
        model_deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT") or "gpt-4",
        search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT") or "",
        search_index_name=os.getenv("AZURE_SEARCH_INDEX_NAME") or os.getenv("AZURE_SEARCH_INDEX") or "grant-compliance-index",
        azure_search_document_truncation_size=int(os.getenv("AZURE_SEARCH_DOCUMENT_CONTENT_TRUNCATION_SIZE", "1000")),
        use_managed_identity=use_managed_identity,
        search_api_key=None if use_managed_identity else os.getenv("AZURE_SEARCH_API_KEY"),
    )

    # Example proposal
    sample_proposal = """
    Grant Application for Community Development Project
    
    Requesting Department: Housing and Urban Development
    Project: Affordable Housing Initiative
    Requested Amount: $2,500,000
    Timeline: 24 months
    
    Purpose: Develop 150 units of affordable housing for low-income families,
    with focus on sustainability and accessibility requirements.
    """

    # Analyze proposal
    print("Analyzing grant proposal for compliance...\n")
    result = await agent.analyze_proposal(sample_proposal)

    print("=== Compliance Analysis ===")
    print(f"\nStatus: {result['status']}")
    print(f"Confidence: {result['confidence_score']}%")
    print(f"\n{result['analysis']}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
