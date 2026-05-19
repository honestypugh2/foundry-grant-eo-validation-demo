"""
Compliance Agent for Grant Proposal Review

This agent analyzes grant proposals for compliance with executive orders
using Azure AI Foundry and Azure AI Search for knowledge base retrieval.
"""

import json
import logging
import os
from typing import Annotated, Optional, Dict, Any

from agent_framework import Agent, Annotation, TextSpanRegion, tool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

logger = logging.getLogger(__name__)


class ComplianceAgent:
    """
    AI Agent for analyzing grant proposal compliance with executive orders.
    """

    def __init__(
        self,
        project_endpoint: str,
        model_deployment_name: str,
        search_index_name: str,
        search_endpoint: Optional[str] = None,
        search_api_key: Optional[str] = None,
        search_query_type: str = "semantic",
    ):
        """
        Initialize the Compliance Agent.

        Args:
            project_endpoint: Azure AI Foundry project endpoint
            model_deployment_name: Name of the deployed model
            search_index_name: Name of the search index for executive orders
            search_endpoint: Azure AI Search endpoint URL
            search_api_key: Azure AI Search API key (if not using managed identity)
            search_query_type: Query type for search (simple or semantic)
        """
        self.project_endpoint = project_endpoint
        self.model_deployment_name = model_deployment_name
        self.search_index_name = search_index_name
        self.search_endpoint = search_endpoint or os.getenv("AZURE_SEARCH_ENDPOINT", "")
        self.search_api_key = search_api_key or os.getenv("AZURE_SEARCH_API_KEY")
        self.search_query_type = search_query_type

        # Agent instructions
        self.instructions = """You are a legal compliance analyst specializing in grant proposal review.

You have access to a search_executive_orders tool that searches a knowledge base of executive orders.
You MUST use this tool to find relevant executive orders and cite the sources in your analysis.

Your responsibilities:
1. Analyze grant proposals for compliance with relevant executive orders against a knowledge base of executive orders
2. Identify potential compliance issues or concerns
3. Provide detailed insights into how well the grant aligns with current legal standards (executive orders and agency guidance) and highlight specific clauses or phrases that may pose compliance risks (for example, address DEI initiatives, green new deal, gender ideology, immigration)
4. Provide structured compliance summaries with specific citations
5. Assign confidence scores to your analysis (0-100)
6. Highlight areas requiring attorney review

When analyzing documents:
- Use the azure_ai_search tool to find relevant executive orders
- Quote specific sections that apply to the grant proposal with proper citations
- Explain how the proposal aligns or conflicts with requirements
- Be thorough but concise
- Flag ambiguous areas for human review

Output Format:
- Overall Compliance Status: [Compliant/Non-Compliant/Requires Review]
- Confidence Score: [0-100]
- Key Findings: [Bullet points with citations]
- Relevant Executive Orders: [List with citations]
- Concerns: [Any issues identified]
- Recommendations: [Actions needed]
"""

    @tool(
        name="search_executive_orders",
        description="Search the knowledge base of executive orders for compliance requirements relevant to a grant proposal query.",
    )
    def search_executive_orders(
        self,
        query: Annotated[str, "Search query describing the compliance topic or executive order to find"],
    ) -> str:
        """Search the executive orders knowledge base using Azure AI Search."""
        if not self.search_endpoint:
            return "Error: Azure AI Search endpoint not configured. Set AZURE_SEARCH_ENDPOINT."

        if self.search_api_key:
            credential = AzureKeyCredential(self.search_api_key)
        else:
            credential = AzureCliCredential()

        client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.search_index_name,
            credential=credential,
        )

        search_kwargs: Dict[str, Any] = {
            "search_text": query,
            "query_type": self.search_query_type,
            "top": 5,
        }
        if self.search_query_type == "semantic":
            search_kwargs["semantic_configuration_name"] = os.getenv(
                "AI_SEARCH_SEMANTIC_CONFIG", "default-semantic-config"
            )

        results = client.search(**search_kwargs)

        output_parts = []
        for i, result in enumerate(results, 1):
            title = result.get("title", result.get("metadata_storage_name", "Unknown"))
            content = result.get("content", result.get("chunk", ""))
            score = result.get("@search.score", 0)
            output_parts.append(f"[Result {i}] (score: {score:.2f})\nSource: {title}\n{content}\n")

        if not output_parts:
            return f"No results found for query: {query}"

        return "\n---\n".join(output_parts)

    @staticmethod
    @tool(
        name="format_grant_context",
        description="Format pre-extracted grant proposal context (metadata, summary, document info) for analysis.",
    )
    def format_grant_context(
        context_data: Annotated[
            str, "JSON string containing pre-extracted metadata, summary, and document info"
        ],
    ) -> str:
        """Format pre-extracted grant proposal context for analysis."""
        try:
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
        
        # Create citation using Annotation TypedDict
        citation: Annotation = {
            "type": "citation",
            "title": f"{doc_info.get('title', 'Executive Order')} (Page {page_number})",
            "url": file_path if file_path.startswith('http') else f"file://{file_path}#page={page_number}",
            "file_id": doc_info.get('id', ''),
            "tool_name": "search_executive_orders",
            "snippet": text_snippet,
            "annotated_regions": [text_region],
            "additional_properties": {
                "executive_order_number": doc_info.get('exec_order_number', 'N/A'),
                "effective_date": doc_info.get('date', 'N/A'),
                "page_number": page_number,
                "document_type": "Executive Order"
            },
        }
        
        return citation


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
            
        NOTE: This is DIFFERENT from compliance_score, which measures HOW COMPLIANT
        the proposal is. The compliance_score is calculated by the orchestrators
        using _calculate_compliance_score_from_analysis() based on the status
        and analysis findings returned by this agent.
            
        See docs/SCORING_SYSTEM.md for complete scoring documentation.
        """
        # Create agent with FoundryChatClient and function tools
        client = FoundryChatClient(
            project_endpoint=self.project_endpoint,
            model=self.model_deployment_name,
            credential=AzureCliCredential(),
        )

        # Build tools list: Azure AI Search function tool + context formatter
        tools = [
            self.search_executive_orders,   # Function tool for Azure AI Search
            self.format_grant_context,       # Function tool for formatting context
        ]

        agent = Agent(
            client=client,
            name="ComplianceAgent",
            instructions=self.instructions,
            tools=tools,
        )

        # Build analysis prompt
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
2. Use the search_executive_orders tool to find relevant executive orders in the knowledge base
3. Identify applicable compliance requirements from the executive orders
4. Assess the proposal against these requirements
5. Provide a structured compliance summary with confidence score and proper citations

Note: Document metadata has already been extracted using Azure Document Intelligence during ingestion.
"""

        # Get analysis from agent via streaming
        response_text = ""
        async for chunk in agent.run(prompt, stream=True):
            if chunk.text:
                response_text += chunk.text

        # Parse response into structured format (outside the context manager)
        # Note: compliance_score is calculated by the orchestrators using
        # _calculate_compliance_score_from_analysis() based on status and analysis findings.
        # This agent returns confidence_score (AI certainty) and status (compliance determination).
        result = {
            "analysis": response_text,
            "confidence_score": self._extract_confidence_score(response_text),
            "status": self._extract_status(response_text),
            "relevant_executive_orders": self._extract_relevant_executive_orders(response_text),
            "citations": [],  # Citations extracted separately if needed
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
        import re
        
        # Try multiple patterns to handle different AI output formats
        # Pattern 1: "Confidence Score: 85" (inline)
        match = re.search(r"confidence\s*score[:\s]*(\d+)", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # Pattern 2: Markdown format with newline and bold
        # "### Confidence Score:\n- **85**" or "Confidence Score:\n- **85**"
        match = re.search(r"confidence\s*score[:\s]*\n[-*\s]*\**(\d+)\**", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # Pattern 3: Just look for a number after "confidence score" within next 50 chars
        match = re.search(r"confidence\s*score[:\s\n\-*]*(\d+)", text, re.IGNORECASE)
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
        """
        Extract relevant executive orders from analysis text.
        
        Handles both structured output (Relevant Executive Orders: section)
        and inline mentions of EO numbers.
        """
        import re
        
        executive_orders = []
        seen_eos = set()  # Track seen EO numbers to avoid duplicates
        
        # === SECTION-BASED EXTRACTION ===
        # Look for "Relevant Executive Orders:" section with bullet points
        eo_section_match = re.search(
            r'(?:^|\n)\s*[-*]?\s*Relevant\s+Executive\s+Orders[:\s]*\n((?:[ \t]*[-*•]\s*[^\n]+\n?)+)',
            text, re.IGNORECASE | re.MULTILINE
        )
        
        if eo_section_match:
            section_text = eo_section_match.group(1)
            # Extract each bullet point
            bullets = re.findall(r'[-*•]\s*([^\n]+)', section_text)
            for bullet in bullets:
                bullet_clean = bullet.strip()
                if not bullet_clean:
                    continue
                    
                # Try to extract EO number from bullet
                eo_num_match = re.search(r'(?:Executive Order|EO|E\.O\.)\s*#?(\d{4,5})', bullet_clean, re.IGNORECASE)
                if eo_num_match:
                    eo_num = eo_num_match.group(1)
                    if eo_num in seen_eos:
                        continue
                    seen_eos.add(eo_num)
                    
                    # Extract title (text after EO number)
                    title_match = re.search(rf'{eo_num}\s*[-–—:]\s*([^(\[]+)', bullet_clean)
                    title = title_match.group(1).strip() if title_match else bullet_clean
                    
                    executive_orders.append({
                        'name': f"EO {eo_num}",
                        'number': eo_num,
                        'title': title[:150],
                        'relevance': 90.0,
                        'key_requirements': [bullet_clean[:300]],
                        'source': 'section_extraction'
                    })
                else:
                    # Bullet without clear EO number - still valuable context
                    # Try to extract any numeric reference
                    any_num = re.search(r'(\d{4,5})', bullet_clean)
                    if any_num:
                        eo_num = any_num.group(1)
                        if eo_num not in seen_eos:
                            seen_eos.add(eo_num)
                            executive_orders.append({
                                'name': f"EO {eo_num}",
                                'number': eo_num,
                                'title': bullet_clean[:150],
                                'relevance': 80.0,
                                'key_requirements': [bullet_clean[:300]],
                                'source': 'section_extraction'
                            })
        
        # === PATTERN-BASED EXTRACTION (for inline mentions) ===
        # Pattern to match EO numbers (14151, 14173, etc.)
        eo_pattern = r'(?:Executive Order|EO|E\.O\.)[\s#]*(\d{4,5})'
        matches = re.findall(eo_pattern, text, re.IGNORECASE)
        
        # Get unique EO numbers
        unique_eos = [m for m in matches if m not in seen_eos]
        
        # For each EO number found, try to extract more context
        for eo_num in unique_eos:
            if eo_num in seen_eos:
                continue
            seen_eos.add(eo_num)
            
            # Look for the EO in context (get surrounding text)
            eo_context_pattern = rf'(?:Executive Order|EO|E\.O\.)[\s#]*{eo_num}[^\n]*'
            context_match = re.search(eo_context_pattern, text, re.IGNORECASE)
            
            context_text = context_match.group(0) if context_match else f"Executive Order {eo_num}"
            
            # Extract title if available (text after EO number, before date or section)
            title_match = re.search(rf'{eo_num}[^\n]*?[\u2013\-–—:]\s*([^\n(\[]+)', text)
            title = title_match.group(1).strip() if title_match else f"Executive Order {eo_num}"
            
            # Look for key requirements mentioned with this EO
            key_reqs = []
            # Search for text immediately following this EO mention
            req_pattern = rf'(?:Executive Order|EO|E\.O\.)\s*#?{eo_num}[^.]*\.\s*([^.]+\.)'
            req_match = re.search(req_pattern, text, re.IGNORECASE)
            if req_match:
                key_reqs.append(req_match.group(1).strip()[:300])
            else:
                key_reqs.append(context_text[:300])
            
            executive_orders.append({
                'name': f"EO {eo_num}",
                'number': eo_num,
                'title': title[:150],
                'relevance': 85.0,
                'key_requirements': key_reqs,
                'source': 'pattern_extraction'
            })
        
        return executive_orders

    async def _extract_citations_from_response(self, response: Any) -> list:
        """
        Extract citations from the agent's response messages.
        
        The Agent Framework may include citation annotations in response content.
        This method attempts to retrieve them from the response.
        """
        citations_list = []
        
        try:
            if hasattr(response, 'messages'):
                for message in response.messages:
                    if hasattr(message, 'contents'):
                        for content in message.contents:
                            if hasattr(content, 'annotations') and content.annotations:
                                for annotation in content.annotations:
                                    if isinstance(annotation, dict) and annotation.get('type') == 'citation':
                                        citations_list.append(annotation)
        except Exception as e:
            logger.info(f"Citation auto-extraction not available: {e}")
            return []
        
        if citations_list:
            return self._format_citations(citations_list)
        
        return []

    def _format_citations(self, citations: list) -> list:
        """
        Format citation annotations for frontend display.
        
        Converts Annotation TypedDicts into dictionaries with all
        relevant metadata including page numbers.
        """
        formatted_citations = []
        
        for citation in citations:
            citation_dict = {
                'title': citation.get('title', 'Untitled'),
                'url': citation.get('url'),
                'file_id': citation.get('file_id'),
                'tool_name': citation.get('tool_name'),
                'snippet': citation.get('snippet'),
                'annotated_regions': [],
                'additional_properties': {}
            }
            
            # Extract annotated regions (text spans)
            regions = citation.get('annotated_regions', [])
            if regions:
                for region in regions:
                    if isinstance(region, dict):
                        citation_dict['annotated_regions'].append({
                            'start_index': region.get('start_index', 0),
                            'end_index': region.get('end_index', 0),
                        })
                    else:
                        citation_dict['annotated_regions'].append({
                            'start_index': getattr(region, 'start_index', 0),
                            'end_index': getattr(region, 'end_index', 0),
                        })
            
            # Extract additional properties (including page_number)
            additional = citation.get('additional_properties', {})
            if additional:
                citation_dict['additional_properties'] = dict(additional)
            
            formatted_citations.append(citation_dict)
        
        return formatted_citations


    async def cleanup(self):
        """
        Cleanup resources.
        Call this when you're done with the agent to free resources.
        """
        pass


async def main():
    """Example usage of the Compliance Agent."""
    from dotenv import load_dotenv

    load_dotenv()

    # Initialize agent with Azure AI Search function tool
    # Requires AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_API_KEY environment variables
    
    agent = ComplianceAgent(
        project_endpoint=os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT") or os.getenv("AZURE_AI_PROJECT_ENDPOINT") or "",
        model_deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT") or "gpt-4",
        search_index_name=os.getenv("AZURE_SEARCH_INDEX_NAME") or os.getenv("AZURE_SEARCH_INDEX") or "grant-compliance-index",
        search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        search_api_key=os.getenv("AZURE_SEARCH_API_KEY"),
        search_query_type=os.getenv("AI_SEARCH_QUERY_TYPE", "semantic"),
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
