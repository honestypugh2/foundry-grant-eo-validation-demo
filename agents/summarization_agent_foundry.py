"""
Summarization Agent using Azure AI Foundry Agent Service
Uses azure-ai-projects SDK for intelligent summarization.

This is an alternative implementation to summarization_agent.py which uses agent-framework.
Set AGENT_SERVICE=foundry in .env to use this implementation.
"""

import os
import logging
import asyncio
from typing import Dict, Any, List
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity.aio import DefaultAzureCredential

logger = logging.getLogger(__name__)


class SummarizationAgentFoundry:
    """
    Agent responsible for generating summaries of grant proposals.
    Uses Azure AI Foundry Agent Service (azure-ai-projects SDK).
    """
    
    def __init__(
        self,
        project_endpoint: str,
        model_deployment_name: str,
    ):
        """
        Initialize the Summarization Agent.
        
        Args:
            project_endpoint: Azure AI Foundry project endpoint
            model_deployment_name: Name of the deployed model
        """
        self.project_endpoint = project_endpoint
        self.model_deployment_name = model_deployment_name
        
        # Agent instructions
        self.instructions = """You are an expert grant proposal analyst specializing in document summarization.

Your responsibilities:
1. Generate concise executive summaries (3-4 sentences)
2. Identify key objectives and deliverables
3. Extract budget highlights and timeline information
4. Identify critical compliance requirements
5. Highlight specific clauses or phrases that may pose compliance risks
6. Extract key topics and themes from the proposal

When analyzing documents:
- Be thorough but concise
- Focus on actionable information
- Identify potential risk areas (DEI initiatives, climate/environmental mandates, immigration-related content)
- Extract verbatim clauses when relevant
- Provide clear, structured output

Output should include:
- Executive Summary: 3-4 sentence overview
- Key Objectives: Bullet points of main goals
- Budget Highlights: Financial information
- Timeline/Deliverables: Key dates and milestones
- Key Topics: Main themes identified
- Key Clauses: Specific text that may require review
"""

    async def generate_summary(self, document_text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of the grant proposal.
        
        Args:
            document_text: Full text of the document
            metadata: Document metadata
            
        Returns:
            Dictionary containing executive summary and key highlights
        """
        logger.info("Generating document summary using Foundry Agent Service")
        
        try:
            # Create credentials and clients fresh to avoid pickle issues
            async with (
                DefaultAzureCredential() as credential,
                AIProjectClient(endpoint=self.project_endpoint, credential=credential) as project_client,
                project_client.get_openai_client() as openai_client,
            ):
                # Create agent version
                agent = await project_client.agents.create_version(
                    agent_name="SummarizationAgentFoundry",
                    definition=PromptAgentDefinition(
                        model=self.model_deployment_name,
                        instructions=self.instructions,
                    ),
                    description="Summarization agent for grant proposals - generates concise summaries and extracts key clauses",
                )
                logger.info(f"Agent created (id: {agent.id}, name: {agent.name}, version: {agent.version})")
                
                try:
                    # Build metadata context
                    import json
                    metadata_str = json.dumps(metadata, indent=2, default=str)
                    
                    # Build summarization prompt
                    prompt = f"""Analyze the following grant proposal and provide a comprehensive summary.

GRANT PROPOSAL TEXT:
{document_text}

DOCUMENT METADATA:
{metadata_str}

Please provide:
1. Executive Summary (3-4 sentences capturing the essence of the proposal)
2. Key Objectives (main goals and deliverables as bullet points)
3. Budget Highlights (financial information mentioned)
4. Timeline/Deliverables (key dates and milestones)
5. Key Topics (main themes: compliance, sustainability, equity, cybersecurity, etc.)
6. Key Clauses (specific phrases or requirements that may pose compliance risks - extract verbatim)

Focus especially on identifying clauses related to:
- DEI (Diversity, Equity, Inclusion) initiatives
- Climate/environmental mandates
- Gender ideology or social policy requirements
- Immigration-related provisions
- Any other politically sensitive content

Structure your response clearly with section headers.
"""

                    # Create conversation and get response
                    conversation = await openai_client.conversations.create()
                    logger.info(f"Created conversation (id: {conversation.id})")
                    
                    try:
                        # Stream response
                        response_text = ""
                        stream = await openai_client.responses.create(
                            conversation=conversation.id,
                            extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
                            input=prompt,
                            stream=True,
                        )
                        
                        async for event in stream:
                            if event.type == "response.output_text.delta":
                                response_text += event.delta
                        
                        logger.info("Successfully generated summary using Foundry Agent Service")
                        
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
            summary_data = self._parse_summary_response(response_text)
            
            # Add metadata
            summary_data['metadata'] = {
                'summary_method': 'foundry_agent_service',
                'original_word_count': metadata.get('word_count', 0),
                'original_page_count': metadata.get('page_count', 0)
            }
            
            return summary_data
            
        except Exception as e:
            logger.error(f"Error generating summary with Foundry: {str(e)}")
            # Fallback to local generation
            logger.warning("Falling back to local summarization")
            return self._generate_locally(document_text, metadata)
    
    def _parse_summary_response(self, text: str) -> Dict[str, Any]:
        """
        Parse the agent's response into structured data.
        
        Args:
            text: Raw response text from the agent
            
        Returns:
            Structured dictionary with summary components
        """
        import re
        
        # Extract sections using regex patterns
        def extract_section(pattern: str, text: str) -> str:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            return match.group(1).strip() if match else ""
        
        # Extract executive summary
        exec_summary = extract_section(
            r'(?:Executive Summary|Summary)[:\s]*\n(.+?)(?:\n\n|\n(?:Key Objectives|Budget|Timeline|Key Topics|Key Clauses))',
            text
        )
        
        # Extract key objectives
        objectives_text = extract_section(
            r'Key Objectives[:\s]*\n(.+?)(?:\n\n|\n(?:Budget|Timeline|Key Topics|Key Clauses))',
            text
        )
        objectives = [line.strip('- •*').strip() for line in objectives_text.split('\n') if line.strip()]
        
        # Extract budget highlights
        budget = extract_section(
            r'Budget(?:\s+Highlights)?[:\s]*\n(.+?)(?:\n\n|\n(?:Timeline|Key Topics|Key Clauses))',
            text
        )
        
        # Extract timeline
        timeline = extract_section(
            r'Timeline(?:/Deliverables)?[:\s]*\n(.+?)(?:\n\n|\n(?:Key Topics|Key Clauses))',
            text
        )
        
        # Extract key topics
        topics_text = extract_section(
            r'Key Topics[:\s]*\n(.+?)(?:\n\n|\nKey Clauses)',
            text
        )
        topics = self._extract_topics(topics_text if topics_text else text)
        
        # Extract key clauses
        clauses_text = extract_section(
            r'Key Clauses[:\s]*\n(.+?)(?:\n\n|$)',
            text
        )
        key_clauses = [line.strip('- •*"').strip() for line in clauses_text.split('\n') if line.strip() and len(line.strip()) > 20]
        
        return {
            'executive_summary': exec_summary if exec_summary else text[:500],
            'key_objectives': objectives[:5],
            'budget_highlights': budget,
            'timeline': timeline,
            'key_topics': topics,
            'key_clauses': key_clauses[:5],
            'summary_length': len(text.split()),
            'detailed_analysis': text
        }
    
    def _generate_locally(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary using simple text extraction."""
        lines = text.split('\n')
        paragraphs = [line.strip() for line in lines if line.strip() and len(line.strip()) > 50]
        
        # Take first few paragraphs as summary
        executive_summary = '\n\n'.join(paragraphs[:3]) if paragraphs else text[:500]
        
        # Extract potential key phrases
        key_clauses = []
        keywords = ['compliance', 'requirement', 'objective', 'budget', 'timeline', 'deliverable']
        
        for paragraph in paragraphs:
            para_lower = paragraph.lower()
            if any(keyword in para_lower for keyword in keywords):
                key_clauses.append(paragraph)
                if len(key_clauses) >= 5:
                    break
        
        return {
            'executive_summary': executive_summary,
            'key_clauses': key_clauses[:5],
            'key_topics': keywords,
            'summary_length': len(executive_summary.split()),
            'metadata': {
                'summary_method': 'local',
                'original_word_count': metadata.get('word_count', 0),
                'original_page_count': metadata.get('page_count', 0)
            }
        }
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract key topics from summary text."""
        keywords = [
            'compliance', 'budget', 'timeline', 'deliverable', 'requirement',
            'objective', 'sustainability', 'equity', 'cybersecurity', 'climate',
            'workforce', 'education', 'infrastructure', 'community', 'innovation',
            'DEI', 'diversity', 'inclusion', 'gender', 'immigration'
        ]
        
        text_lower = text.lower()
        found_topics = [kw for kw in keywords if kw in text_lower]
        
        return found_topics[:10]
    
    async def cleanup(self):
        """Clean up resources."""
        # All resources are managed via async context managers
        logger.info("SummarizationAgentFoundry cleaned up")


async def main():
    """Example usage of the Summarization Agent with Foundry."""
    from dotenv import load_dotenv

    load_dotenv()

    # Initialize agent
    agent = SummarizationAgentFoundry(
        project_endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT", ""),
        model_deployment_name=os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
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
    
    Key Deliverables:
    - Complete environmental impact assessment by month 6
    - Begin construction by month 9
    - Deliver first 50 units by month 18
    - Complete all 150 units by month 24
    
    Budget Breakdown:
    - Land acquisition: $500,000
    - Construction: $1,800,000
    - Environmental compliance: $100,000
    - Community engagement: $100,000
    """

    metadata = {
        'file_name': 'sample_proposal.pdf',
        'page_count': 5,
        'word_count': 1250,
        'applicant': 'City Housing Authority'
    }

    # Generate summary
    print("Generating summary using Foundry Agent Service...\n")
    result = await agent.generate_summary(sample_proposal, metadata)

    print("=== Summary Results ===")
    print(f"\nExecutive Summary:\n{result.get('executive_summary', 'N/A')}")
    print(f"\nKey Topics: {', '.join(result.get('key_topics', []))}")
    print(f"\nSummary Length: {result.get('summary_length', 0)} words")
    print(f"\nMethod: {result.get('metadata', {}).get('summary_method', 'N/A')}")
    
    await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
