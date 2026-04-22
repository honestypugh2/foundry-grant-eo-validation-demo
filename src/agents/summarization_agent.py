"""
Summarization Agent
Generates concise summaries of proposal sections and highlights key clauses.
"""

import os
import json
import logging
import asyncio
from typing import Annotated, Dict, Any, List, Optional
from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

logger = logging.getLogger(__name__)


class SummarizationAgent:
    """
    Agent responsible for generating summaries of grant proposals.
    Uses Azure AI Foundry Agent Framework for intelligent summarization.
    """
    
    def __init__(
        self,
        project_endpoint: str,
        model_deployment_name: str,
        use_managed_identity: bool = True,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the Summarization Agent.
        
        Args:
            project_endpoint: Azure AI Foundry project endpoint
            model_deployment_name: Name of the deployed model
            use_managed_identity: Whether to use Managed Identity for authentication
            api_key: API key for Azure OpenAI (if not using managed identity)
        """
        self.project_endpoint = project_endpoint
        self.model_deployment_name = model_deployment_name
        self.use_managed_identity = use_managed_identity
        
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

    @staticmethod
    @tool(name="extract_document_info", description="Extract and format basic document information for context. This tool helps the agent understand the document's basic properties.")
    def extract_document_info(
        metadata: Annotated[str, "JSON string containing document metadata like file_name, page_count, word_count"]
    ) -> str:
        """Extract and format basic document information for context."""
        try:
            meta = json.loads(metadata)
        except Exception:
            meta = {}
        
        info = ["\n=== Document Information ==="]
        info.append(f"File: {meta.get('file_name', 'Unknown')}")
        info.append(f"Pages: {meta.get('page_count', 'N/A')}")
        info.append(f"Word Count: {meta.get('word_count', 'N/A')}")
        
        if meta.get('deadline'):
            info.append(f"Deadline: {meta['deadline']}")
        if meta.get('budget_amount'):
            info.append(f"Budget: {meta['budget_amount']}")
        if meta.get('applicant'):
            info.append(f"Applicant: {meta['applicant']}")
        
        return "\n".join(info)

    async def generate_summary(self, document_text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of the grant proposal.
        
        Args:
            document_text: Full text of the document
            metadata: Document metadata
            
        Returns:
            Dictionary containing executive summary and key highlights
        """
        logger.info("Generating document summary")
        
        try:
            client = FoundryChatClient(
                project_endpoint=self.project_endpoint,
                model=self.model_deployment_name,
                credential=AzureCliCredential(),
            )

            agent = Agent(
                client=client,
                name="SummarizationAgent",
                instructions=self.instructions,
                tools=[self.extract_document_info],
            )

            # Build metadata JSON for the tool
            metadata_json = json.dumps(metadata)
            
            # Build summarization prompt
            prompt = f"""Analyze the following grant proposal and provide a comprehensive summary.

GRANT PROPOSAL TEXT:
{document_text}

DOCUMENT METADATA (use extract_document_info tool):
{metadata_json}

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

            # Get summary from agent via streaming
            response_text = ""
            async for chunk in agent.run(prompt, stream=True):
                if chunk.text:
                    response_text += chunk.text
            
            # Parse response into structured format
            summary_data = self._parse_summary_response(response_text)
            
            # Add metadata
            summary_data['metadata'] = {
                'summary_method': 'agent_framework',
                'original_word_count': metadata.get('word_count', 0),
                'original_page_count': metadata.get('page_count', 0)
            }
            
            logger.info("Successfully generated summary")
            return summary_data
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            # Fallback to local generation
            logger.warning("Falling back to local summarization")
            return self._generate_locally(document_text, metadata)
    
    def _parse_summary_response(self, text: str) -> Dict[str, Any]:
        """
        Parse the agent's response into structured data.
        
        Handles both plain text and markdown-formatted sections (e.g., **Key Clauses:**).
        
        Args:
            text: Raw response text from the agent
            
        Returns:
            Structured dictionary with summary components
        """
        import re
        
        # Extract sections using regex patterns
        # Uses .*? after header name to handle markdown like **Key Clauses:**
        def extract_section(pattern: str, text: str) -> str:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            return match.group(1).strip() if match else ""
        
        # Extract key clauses - matches **Key Clauses:** or Key Clauses:
        clauses_text = extract_section(
            r'Key Clauses.*?\n(.+?)(?=\n\n|$)',
            text
        )
        
        # Also extract "Potential Compliance Risk Clauses" section
        risk_clauses_text = extract_section(
            r'Potential Compliance Risk Clauses.*?\n(.+?)(?=\n\n|$)',
            text
        )
        
        # Parse key clauses from the extracted text
        key_clauses = self._parse_clause_bullets(clauses_text)
        
        # Add risk clauses if found
        if risk_clauses_text:
            risk_clauses = self._parse_clause_bullets(risk_clauses_text)
            key_clauses.extend(risk_clauses)
        
        # Extract key topics
        topics_text = extract_section(
            r'Key Topics.*?\n(.+?)(?=\n\n|$)',
            text
        )
        topics = self._extract_topics(topics_text if topics_text else text)
        
        # Extract executive summary
        exec_summary = extract_section(
            r'(?:Executive )?Summary.*?\n(.+?)(?=\n\n|$)',
            text
        )
        
        # Extract key objectives
        objectives_text = extract_section(
            r'Key Objectives.*?\n(.+?)(?=\n\n|$)',
            text
        )
        objectives = [line.strip('- •*').strip() for line in objectives_text.split('\n') if line.strip()]
        
        # Extract budget highlights
        budget = extract_section(
            r'Budget(?:\s+Highlights)?.*?\n(.+?)(?=\n\n|$)',
            text
        )
        
        # Extract timeline
        timeline = extract_section(
            r'Timeline(?:/Deliverables)?.*?\n(.+?)(?=\n\n|$)',
            text
        )
        
        return {
            'executive_summary': exec_summary if exec_summary else text[:500],
            'key_objectives': objectives[:5],
            'budget_highlights': budget,
            'timeline': timeline,
            'key_topics': topics,
            'key_clauses': key_clauses[:10],  # Allow more clauses
            'summary_length': len(text.split()),
            'detailed_analysis': text
        }
    
    def _parse_clause_bullets(self, text: str) -> list:
        """
        Parse bullet points from clause text, handling markdown formatting.
        
        Args:
            text: Raw text containing clause bullet points
            
        Returns:
            List of clause strings
        """
        import re
        
        if not text:
            return []
        
        clauses = []
        
        # Split by newlines and process each line
        for line in text.split('\n'):
            line = line.strip()
            if not line or len(line) < 20:
                continue
            
            # Skip section dividers
            if line.startswith('---'):
                continue
            
            # Remove bullet markers and markdown
            # Handle formats like: "- **Collaboration Requirement:** text"
            cleaned = re.sub(r'^[-*•]\s*', '', line)  # Remove bullet
            cleaned = cleaned.strip()
            
            # Extract the clause content (may include bold label)
            # Handle **Label:** format - remove ** but keep label and colon
            if cleaned and len(cleaned) > 20:
                # Replace **text:** with "text:" (handles colon inside bold)
                cleaned = re.sub(r'\*\*([^*:]+):\*\*', r'\1:', cleaned)
                # Replace **text**: with "text:" (handles colon outside bold)
                cleaned = re.sub(r'\*\*([^*]+)\*\*:', r'\1:', cleaned)
                # Replace remaining **text** with just text
                cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
                clauses.append(cleaned)
        
        return clauses
    
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
        logger.info("SummarizationAgent cleaned up")


async def main():
    """Example usage of the Summarization Agent."""
    from dotenv import load_dotenv

    load_dotenv()

    # Initialize agent
    use_managed_identity = os.getenv("USE_MANAGED_IDENTITY", "false").lower() == "true"
    
    agent = SummarizationAgent(
        project_endpoint=os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT") or os.getenv("AZURE_AI_PROJECT_ENDPOINT") or "",
        model_deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT") or "gpt-4o",
        use_managed_identity=use_managed_identity,
        api_key=None if use_managed_identity else os.getenv("AZURE_OPENAI_API_KEY"),
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
    print("Generating summary...\n")
    result = await agent.generate_summary(sample_proposal, metadata)

    print("=== Summary Results ===")
    print(f"\nExecutive Summary:\n{result.get('executive_summary', 'N/A')}")
    print(f"\nKey Topics: {', '.join(result.get('key_topics', []))}")
    print(f"\nSummary Length: {result.get('summary_length', 0)} words")
    
    await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
