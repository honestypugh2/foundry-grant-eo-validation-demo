"""
Compliance Agent using Azure AI Foundry Agent Service
Uses azure-ai-projects SDK with Azure AI Search tool for knowledge base retrieval.

This is an alternative implementation to compliance_agent.py which uses agent-framework.
Set AGENT_SERVICE=foundry in .env to use this implementation.
"""

import os
import re
import logging
import asyncio
from typing import Optional, Dict, Any
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import (
    AzureAISearchAgentTool,
    PromptAgentDefinition,
    AzureAISearchToolResource,
    AISearchIndexResource,
    AzureAISearchQueryType,
)
from azure.identity.aio import DefaultAzureCredential

logger = logging.getLogger(__name__)


class ComplianceAgentFoundry:
    """
    AI Agent for analyzing grant proposal compliance with executive orders.
    Uses Azure AI Foundry Agent Service (azure-ai-projects SDK) with Azure AI Search.
    """

    def __init__(
        self,
        project_endpoint: str,
        model_deployment_name: str,
        search_index_name: str,
        search_connection_id: Optional[str] = None,
        search_query_type: str = "simple",
    ):
        """
        Initialize the Compliance Agent.

        Args:
            project_endpoint: Azure AI Foundry project endpoint
            model_deployment_name: Name of the deployed model
            search_index_name: Name of the search index for executive orders
            search_connection_id: Azure AI Search connection ID configured in the Foundry project
                                  (from AI_SEARCH_PROJECT_CONNECTION_ID env var)
            search_query_type: Query type for search (simple, semantic, or vector)
        """
        self.project_endpoint = project_endpoint
        self.model_deployment_name = model_deployment_name
        self.search_index_name = search_index_name
        self.search_connection_id = search_connection_id or os.getenv("AI_SEARCH_PROJECT_CONNECTION_ID", "")
        self.search_query_type = search_query_type
        
        # Map query type string to enum
        self.query_type_map = {
            "simple": AzureAISearchQueryType.SIMPLE,
            "semantic": AzureAISearchQueryType.SEMANTIC,
            "vector": AzureAISearchQueryType.VECTOR,
            "hybrid": AzureAISearchQueryType.VECTOR_SEMANTIC_HYBRID,
        }

        # Agent instructions - updated to use hosted Azure AI Search tool
        self.instructions = """You are a legal compliance analyst specializing in grant proposal review.

You have access to an Azure AI Search tool that searches a knowledge base of executive orders.
You MUST always provide citations for answers using the tool and render them as: `[message_idx:search_idx†source]`.

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

    def _build_azure_ai_search_tool(self) -> AzureAISearchAgentTool:
        """
        Build the Azure AI Search tool for the agent.
        
        Returns:
            AzureAISearchAgentTool: Configured search tool
        """
        if not self.search_connection_id:
            raise ValueError(
                "AI_SEARCH_PROJECT_CONNECTION_ID environment variable must be set "
                "for Azure AI Search tool. Configure the connection in your Azure AI Foundry project."
            )
        
        query_type = self.query_type_map.get(
            self.search_query_type.lower(),
            AzureAISearchQueryType.SIMPLE
        )
        
        return AzureAISearchAgentTool(
            azure_ai_search=AzureAISearchToolResource(
                indexes=[
                    AISearchIndexResource(
                        project_connection_id=self.search_connection_id,
                        index_name=self.search_index_name,
                        query_type=query_type,
                    ),
                ]
            )
        )

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
        """
        logger.info("Analyzing proposal using Foundry Agent Service")
        
        # Create credentials and clients fresh to avoid pickle issues
        async with (
            DefaultAzureCredential() as credential,
            AIProjectClient(endpoint=self.project_endpoint, credential=credential) as project_client,
            project_client.get_openai_client() as openai_client,
        ):
            # Build the Azure AI Search tool
            search_tool = self._build_azure_ai_search_tool()
            
            # Create agent version with Azure AI Search tool
            agent = await project_client.agents.create_version(
                agent_name="ComplianceAgentFoundry",
                definition=PromptAgentDefinition(
                    model=self.model_deployment_name,
                    instructions=self.instructions,
                    tools=[search_tool],
                ),
                description="Compliance agent for grant proposals - analyzes against executive orders",
            )
            logger.info(f"Agent created (id: {agent.id}, name: {agent.name}, version: {agent.version})")
            
            try:
                # Build context string
                context_str = ""
                if context:
                    import json
                    context_str = f"\n\nADDITIONAL CONTEXT:\n{json.dumps(context, indent=2, default=str)}"
                
                # Build analysis prompt
                prompt = f"""Analyze the following grant proposal for compliance with relevant executive orders.

GRANT PROPOSAL TEXT:
{proposal_text}
{context_str}

Search the knowledge base for relevant executive orders and provide a detailed compliance analysis.

Include in your response:
1. Overall Compliance Status: [Compliant/Non-Compliant/Requires Review]
2. Confidence Score: [0-100] - how certain you are about your analysis
3. Key Findings - with citations to specific executive orders
4. Relevant Executive Orders - list all applicable EOs with their numbers
5. Concerns - any compliance issues or risks identified
6. Recommendations - actions needed to address any issues

Use the Azure AI Search tool to find and cite relevant executive orders.
Render citations as: `[message_idx:search_idx†source]`
"""

                # Create conversation and get response
                conversation = await openai_client.conversations.create()
                logger.info(f"Created conversation (id: {conversation.id})")
                
                try:
                    # Stream response with tool_choice required
                    response_text = ""
                    citations = []
                    
                    stream = await openai_client.responses.create(
                        conversation=conversation.id,
                        extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
                        input=prompt,
                        stream=True,
                        tool_choice="required",
                    )
                    
                    async for event in stream:
                        if event.type == "response.output_text.delta":
                            response_text += event.delta
                        elif event.type == "response.output_item.done":
                            # Extract citations from output item annotations
                            if hasattr(event, 'item'):
                                item = event.item
                                if hasattr(item, 'type') and item.type == "message":
                                    if hasattr(item, 'content') and item.content:
                                        for content_item in item.content:
                                            # Check if content_item has annotations (skip ResponseOutputRefusal types)
                                            annotations = getattr(content_item, 'annotations', None)
                                            if annotations:
                                                for annotation in annotations:
                                                    annotation_type = getattr(annotation, 'type', '')
                                                    if annotation_type in ("url_citation", "file_citation", "file_path"):
                                                        citations.append({
                                                            'url': getattr(annotation, 'url', getattr(annotation, 'file_id', '')),
                                                            'title': getattr(annotation, 'title', getattr(annotation, 'filename', '')),
                                                            'text': getattr(annotation, 'text', ''),
                                                            'type': annotation_type,
                                                        })
                    
                    logger.info("Successfully completed compliance analysis using Foundry Agent Service")
                    
                finally:
                    # Clean up conversation
                    await openai_client.conversations.delete(conversation_id=conversation.id)
                    logger.info("Conversation deleted")
            
            finally:
                # Clean up agent
                await project_client.agents.delete_version(
                    agent_name=agent.name,
                    agent_version=agent.version
                )
                logger.info("Agent deleted")

        # Parse response into structured format
        result = {
            "analysis": response_text,
            "confidence_score": self._extract_confidence_score(response_text),
            "status": self._extract_status(response_text),
            "relevant_executive_orders": self._extract_relevant_executive_orders(response_text),
            "citations": citations,
            "compliance_score": self._extract_confidence_score(response_text),  # Alias for risk scoring
            "overall_status": self._extract_status(response_text).lower().replace(' ', '_'),
        }

        return result

    def _extract_confidence_score(self, text: str) -> int:
        """Extract confidence score from analysis text."""
        match = re.search(r"confidence\s*score[:\s]*(\d+)", text, re.IGNORECASE)
        if match:
            return min(100, max(0, int(match.group(1))))
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
        executive_orders = []
        
        # Pattern to match EO numbers (14151, 14173, etc.)
        eo_pattern = r'(?:Executive Order|EO|E\.O\.)[\s#]*(\d{5})'
        matches = re.findall(eo_pattern, text, re.IGNORECASE)
        
        # Get unique EO numbers
        unique_eos = list(set(matches))
        
        # For each EO number found, try to extract more context
        for eo_num in unique_eos:
            # Try to find the full title/description
            title_pattern = rf'(?:Executive Order|EO|E\.O\.)\s*#?{eo_num}[:\s,\-]*([^\n\[\]]+)'
            title_match = re.search(title_pattern, text, re.IGNORECASE)
            
            eo_entry = {
                'eo_number': eo_num,
                'title': title_match.group(1).strip()[:100] if title_match else f"Executive Order {eo_num}",
                'source': 'azure_ai_search'
            }
            executive_orders.append(eo_entry)
        
        return executive_orders

    async def cleanup(self):
        """Clean up resources."""
        # All resources are managed via async context managers
        logger.info("ComplianceAgentFoundry cleaned up")


async def main():
    """Example usage of the Compliance Agent with Foundry."""
    from dotenv import load_dotenv

    load_dotenv()

    # Initialize agent with Azure AI Search tool
    agent = ComplianceAgentFoundry(
        project_endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT", ""),
        model_deployment_name=os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
        search_index_name=os.getenv("AZURE_SEARCH_INDEX_NAME", "grant-compliance-index"),
        search_connection_id=os.getenv("AI_SEARCH_PROJECT_CONNECTION_ID"),
        search_query_type=os.getenv("AI_SEARCH_QUERY_TYPE", "simple"),
    )

    # Example proposal
    sample_proposal = """
    Grant Application for Community Development Project
    
    Requesting Department: Housing and Urban Development
    Project: Affordable Housing Initiative
    Requested Amount: $2,500,000
    Timeline: 24 months
    
    Purpose: Develop 150 units of affordable housing for low-income families,
    with focus on sustainability and accessibility requirements. The project
    will prioritize environmental justice and equitable access to housing.
    We will implement DEI initiatives and promote diversity in hiring.
    """

    # Analyze proposal
    print("Analyzing grant proposal for compliance using Foundry Agent Service...\n")
    result = await agent.analyze_proposal(sample_proposal)

    print("=== Compliance Analysis ===")
    print(f"\nStatus: {result['status']}")
    print(f"Confidence: {result['confidence_score']}%")
    print(f"\nRelevant EOs: {len(result['relevant_executive_orders'])}")
    for eo in result['relevant_executive_orders']:
        print(f"  - EO {eo['eo_number']}: {eo['title']}")
    print(f"\n{result['analysis'][:1000]}...")
    
    await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
