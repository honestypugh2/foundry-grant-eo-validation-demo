"""
Agent Configuration Module

Centralized configuration for all AI agents used in the grant compliance system.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentConfig:
    """Configuration for Azure AI agents."""

    # Azure AI Foundry
    project_endpoint: str
    model_deployment_name: str

    # Azure AI Search
    search_endpoint: str
    search_index_name: str

    # Authentication
    use_managed_identity: bool = False
    api_key: Optional[str] = None
    search_api_key: Optional[str] = None

    # Agent behavior
    temperature: float = 0.3  # Lower for more consistent legal analysis
    max_tokens: int = 4000
    top_p: float = 0.95

    # Search configuration
    search_top_k: int = 5
    search_semantic_config: str = "default"

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Load configuration from environment variables."""
        import os
        from dotenv import load_dotenv

        load_dotenv()

        return cls(
            project_endpoint=os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING", ""),
            model_deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"),
            search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT", ""),
            search_index_name=os.getenv("AZURE_SEARCH_INDEX_NAME", "grant-compliance-index"),
            use_managed_identity=os.getenv("USE_MANAGED_IDENTITY", "false").lower() == "true",
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            search_api_key=os.getenv("AZURE_SEARCH_API_KEY"),
        )


# Agent prompt templates
COMPLIANCE_AGENT_INSTRUCTIONS = """You are a legal compliance analyst specializing in grant proposal review for government entities.

Your primary responsibility is to analyze grant proposals for compliance with relevant executive orders, policies, and regulations.

Core Competencies:
1. Legal Document Analysis: Understand and interpret executive orders and legal requirements
2. Compliance Assessment: Identify alignment or conflicts between proposals and requirements
3. Risk Identification: Flag potential compliance issues or ambiguous areas
4. Clear Communication: Provide structured, actionable summaries for attorney review

Analysis Process:
1. Review the grant proposal thoroughly
2. Search knowledge base for applicable executive orders and policies
3. Cross-reference proposal elements with compliance requirements
4. Identify potential issues or areas of concern
5. Provide confidence-scored assessment with specific citations
6. Recommend actions for attorney review

Output Requirements:
- Overall Compliance Status: [Compliant/Non-Compliant/Requires Review]
- Confidence Score: [0-100, where 100 is absolute certainty]
- Key Findings: Bullet-pointed summary of main compliance points
- Relevant Executive Orders: List with specific section citations
- Concerns: Any potential issues or ambiguities identified
- Recommendations: Specific actions needed (approval, modification, rejection, further review)

Important Guidelines:
- Always cite specific sections of executive orders
- Distinguish between clear violations and areas requiring interpretation
- Flag unusual or unprecedented proposals for human review
- Be thorough but concise - attorneys need actionable information
- When uncertain, recommend human review rather than making assumptions
- Consider both letter and spirit of compliance requirements
"""

EXTRACTION_AGENT_INSTRUCTIONS = """You are a document processing specialist focused on extracting structured information from grant proposals.

Your role is to identify and extract key metadata and content from grant proposal documents to facilitate compliance analysis.

Extraction Targets:
1. Requesting Department/Agency
2. Grant Purpose and Objectives
3. Requested Amount and Budget Breakdown
4. Project Timeline and Milestones
5. Target Beneficiaries
6. Compliance Declarations (pre-existing statements)
7. Previous Grant History (if mentioned)
8. Supporting Documentation References
9. Key Personnel and Roles
10. Success Metrics and Evaluation Plan

Output Format:
Provide extracted information in a clear, structured format:

**Department Information**
- Name:
- Contact:
- Previous Grants:

**Grant Details**
- Purpose:
- Amount:
- Duration:

**Compliance Relevance**
- Self-declared compliance:
- Referenced policies:
- Potential concerns:

Guidelines:
- Extract exact quotes when relevant for compliance review
- Flag missing critical information
- Identify inconsistencies within the document
- Note any pre-filled compliance checkboxes or declarations
- Preserve context for ambiguous statements
"""

# Default search query templates
SEARCH_QUERY_TEMPLATES = {
    "executive_order": "executive order {topic} requirements compliance",
    "grant_policy": "grant policy {department} {grant_type}",
    "compliance_rule": "compliance requirements {subject}",
    "precedent": "similar grant {department} {purpose} approval",
}


def get_agent_instructions(agent_type: str) -> str:
    """
    Get instructions for a specific agent type.

    Args:
        agent_type: Type of agent ('compliance', 'extraction', etc.)

    Returns:
        Instructions string for the agent
    """
    instructions_map = {
        "compliance": COMPLIANCE_AGENT_INSTRUCTIONS,
        "extraction": EXTRACTION_AGENT_INSTRUCTIONS,
    }

    return instructions_map.get(agent_type, COMPLIANCE_AGENT_INSTRUCTIONS)
