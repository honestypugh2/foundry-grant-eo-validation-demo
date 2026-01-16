"""
Sequential Workflow Orchestrator using Azure AI Foundry Agent Service
Uses azure-ai-projects SDK workflow pattern for multi-agent coordination.

This is an alternative implementation to sequential_workflow_orchestrator.py which uses agent-framework.
Set AGENT_SERVICE=foundry in .env to use this implementation.
"""

import os
import logging
import asyncio
from typing import Dict, Any
from pathlib import Path

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    AzureAISearchAgentTool,
    AzureAISearchToolResource,
    AISearchIndexResource,
    AzureAISearchQueryType,
)
from azure.identity.aio import AzureCliCredential, ManagedIdentityCredential

from .document_ingestion_agent import DocumentIngestionAgent
from .risk_scoring_agent import RiskScoringAgent
from .email_trigger_agent import EmailTriggerAgent

logger = logging.getLogger(__name__)


class SequentialWorkflowOrchestratorFoundry:
    """
    Sequential Workflow Orchestrator using Azure AI Foundry Agent Service.
    Coordinates compliance validation through agents using azure-ai-projects SDK.
    """
    
    def __init__(self, use_azure: bool = False, send_email: bool = False):
        """
        Initialize the Sequential Workflow Orchestrator.
        
        Args:
            use_azure: If True, use Azure services
            send_email: If True and risk warrants, send email notification
        """
        self.use_azure = use_azure
        self.send_email = send_email
        
        # Initialize configuration from environment
        self.project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT", "")
        self.deployment_name = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
        self.search_index = os.getenv("AZURE_SEARCH_INDEX_NAME", "grant-compliance-index")
        self.search_connection_id = os.getenv("AI_SEARCH_PROJECT_CONNECTION_ID", "")
        
        # Use managed identity setting
        use_managed_identity = os.getenv("USE_MANAGED_IDENTITY", "true").lower() == "true"
        
        # Initialize non-AI agents locally (they don't need Foundry Agent Service)
        self.document_agent = DocumentIngestionAgent(
            use_azure=use_azure,
            use_managed_identity=use_managed_identity
        )
        self.risk_agent = RiskScoringAgent()
        self.email_agent = EmailTriggerAgent(use_graph_api=use_azure)
        
        logger.info(f"Sequential Workflow Orchestrator (Foundry) initialized (Azure: {use_azure})")

    def _build_summarization_instructions(self) -> str:
        """Build instructions for the summarization agent."""
        return """You are an expert grant proposal analyst specializing in document summarization.

Your responsibilities:
1. Generate concise executive summaries (3-4 sentences)
2. Identify key objectives and deliverables
3. Extract budget highlights and timeline information
4. Identify critical compliance requirements
5. Highlight specific clauses or phrases that may pose compliance risks
6. Extract key topics and themes from the proposal

Output should include:
- Executive Summary: 3-4 sentence overview
- Key Objectives: Bullet points of main goals
- Budget Highlights: Financial information
- Timeline/Deliverables: Key dates and milestones
- Key Topics: Main themes identified
- Key Clauses: Specific text that may require review
"""

    def _build_compliance_instructions(self) -> str:
        """Build instructions for the compliance agent."""
        return """You are a legal compliance analyst specializing in grant proposal review.

You have access to an Azure AI Search tool that searches a knowledge base of executive orders.
You MUST always provide citations for answers using the tool and render them as: `[message_idx:search_idx†source]`.

Your responsibilities:
1. Analyze grant proposals for compliance with relevant executive orders
2. Identify potential compliance issues or concerns
3. Provide detailed insights into how well the grant aligns with current legal standards
4. Highlight specific clauses or phrases that may pose compliance risks
5. Assign confidence scores to your analysis (0-100)

Output Format:
- Overall Compliance Status: [Compliant/Non-Compliant/Requires Review]
- Confidence Score: [0-100]
- Key Findings: [Bullet points with citations]
- Relevant Executive Orders: [List with citations]
- Concerns: [Any issues identified]
- Recommendations: [Actions needed]
"""

    def _build_azure_ai_search_tool(self) -> AzureAISearchAgentTool:
        """Build the Azure AI Search tool for compliance agent."""
        if not self.search_connection_id:
            raise ValueError("AI_SEARCH_PROJECT_CONNECTION_ID must be set for Foundry Agent Service")
        
        return AzureAISearchAgentTool(
            azure_ai_search=AzureAISearchToolResource(
                indexes=[
                    AISearchIndexResource(
                        project_connection_id=self.search_connection_id,
                        index_name=self.search_index,
                        query_type=AzureAISearchQueryType.SIMPLE,
                    ),
                ]
            )
        )

    async def process_grant_proposal_async(
        self,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Process a grant proposal through the workflow (async version).
        
        This implementation uses individual agents coordinated by Python code
        rather than a YAML workflow definition, as the grant compliance use case
        requires passing data between agents and post-processing results.
        
        Args:
            file_path: Path to the grant proposal file
            
        Returns:
            Complete workflow results including all agent outputs
        """
        logger.info(f"Starting Foundry workflow for: {file_path}")
        
        workflow_results = {
            'status': 'in_progress',
            'file_path': file_path,
            'steps': {},
            'service': 'foundry_agent_service'
        }
        
        try:
            # Step 1: Document Ingestion (local - no AI needed)
            logger.info("Step 1: Document Ingestion")
            document_data = self.document_agent.process_document(file_path)
            metadata = self.document_agent.extract_metadata(document_data)
            workflow_results['steps']['ingestion'] = {
                'status': 'completed',
                'metadata': metadata
            }
            logger.info(f"✓ Document ingested: {metadata.get('word_count', 0)} words")
            
            # Create Foundry client for AI agent steps
            # Use ChainedTokenCredential: AzureCliCredential for local dev, ManagedIdentityCredential for Azure
            use_managed_identity = os.getenv("USE_MANAGED_IDENTITY", "true").lower() == "true"
            if use_managed_identity:
                credential = ManagedIdentityCredential()
            else:
                credential = AzureCliCredential()
            
            async with (
                credential,
                AIProjectClient(endpoint=self.project_endpoint, credential=credential) as project_client,
                project_client.get_openai_client() as openai_client,
            ):
                # Step 2: Summarization using Foundry Agent
                logger.info("Step 2: Summarization")
                summary_agent = await project_client.agents.create_version(
                    agent_name="SummarizationAgentFoundry",
                    definition=PromptAgentDefinition(
                        model=self.deployment_name,
                        instructions=self._build_summarization_instructions(),
                    ),
                )
                logger.info(f"Summarization agent created (id: {summary_agent.id})")
                
                try:
                    # Create conversation for summarization
                    summary_conv = await openai_client.conversations.create()
                    
                    try:
                        import json
                        metadata_str = json.dumps(metadata, indent=2, default=str)
                        summary_prompt = f"""Analyze this grant proposal and provide a summary:

PROPOSAL TEXT:
{document_data['text']}

METADATA:
{metadata_str}

Provide Executive Summary, Key Objectives, Budget Highlights, Timeline, Key Topics, and Key Clauses.
"""
                        
                        summary_text = ""
                        stream = await openai_client.responses.create(
                            conversation=summary_conv.id,
                            extra_body={"agent": {"name": summary_agent.name, "type": "agent_reference"}},
                            input=summary_prompt,
                            stream=True,
                        )
                        async for event in stream:
                            if event.type == "response.output_text.delta":
                                summary_text += event.delta
                        
                        # Parse summary
                        summary = self._parse_summary(summary_text, metadata)
                        workflow_results['steps']['summarization'] = {
                            'status': 'completed',
                            'summary': summary
                        }
                        logger.info(f"✓ Summary generated: {len(summary.get('key_clauses', []))} key clauses")
                        
                    finally:
                        await openai_client.conversations.delete(conversation_id=summary_conv.id)
                        
                finally:
                    # Clean up agent (unless persistence is enabled)
                    persist_agents = os.getenv("PERSIST_FOUNDRY_AGENTS", "false").lower() == "true"
                    if not persist_agents:
                        await project_client.agents.delete_version(
                            agent_name=summary_agent.name,
                            agent_version=summary_agent.version
                        )
                    else:
                        logger.info(f"Agent persisted: {summary_agent.name} (version: {summary_agent.version})")
                
                # Step 3: Compliance Validation using Foundry Agent with Azure AI Search
                logger.info("Step 3: Compliance Validation")
                search_tool = self._build_azure_ai_search_tool()
                
                compliance_agent = await project_client.agents.create_version(
                    agent_name="ComplianceAgentFoundry",
                    definition=PromptAgentDefinition(
                        model=self.deployment_name,
                        instructions=self._build_compliance_instructions(),
                        tools=[search_tool],
                    ),
                )
                logger.info(f"Compliance agent created (id: {compliance_agent.id})")
                
                try:
                    compliance_conv = await openai_client.conversations.create()
                    
                    try:
                        compliance_prompt = f"""Analyze this grant proposal for compliance with executive orders.

PROPOSAL TEXT:
{document_data['text']}

SUMMARY:
{summary.get('executive_summary', '')}

KEY CLAUSES TO REVIEW:
{chr(10).join(summary.get('key_clauses', []))}

Search the knowledge base for relevant executive orders and provide a detailed compliance analysis.
Include Compliance Status, Confidence Score (0-100), Key Findings, Relevant Executive Orders, and Recommendations.
"""
                        
                        compliance_text = ""
                        stream = await openai_client.responses.create(
                            conversation=compliance_conv.id,
                            extra_body={"agent": {"name": compliance_agent.name, "type": "agent_reference"}},
                            input=compliance_prompt,
                            stream=True,
                            tool_choice="required",
                        )
                        async for event in stream:
                            if event.type == "response.output_text.delta":
                                compliance_text += event.delta
                        
                        # Parse compliance analysis
                        compliance_report = self._parse_compliance(compliance_text)
                        workflow_results['steps']['compliance'] = {
                            'status': 'completed',
                            'report': compliance_report
                        }
                        logger.info(
                            f"✓ Compliance validated: {compliance_report['compliance_score']:.1f}% "
                            f"({compliance_report['overall_status']})"
                        )
                        
                    finally:
                        await openai_client.conversations.delete(conversation_id=compliance_conv.id)
                        
                finally:
                    # Clean up agent (unless persistence is enabled)
                    persist_agents = os.getenv("PERSIST_FOUNDRY_AGENTS", "false").lower() == "true"
                    if not persist_agents:
                        await project_client.agents.delete_version(
                            agent_name=compliance_agent.name,
                            agent_version=compliance_agent.version
                        )
                    else:
                        logger.info(f"Agent persisted: {compliance_agent.name} (version: {compliance_agent.version})")
            
            # Step 4: Risk Scoring (local - no AI needed)
            logger.info("Step 4: Risk Scoring")
            risk_report = self.risk_agent.calculate_risk_score(
                compliance_report,
                summary,
                metadata
            )
            workflow_results['steps']['risk_scoring'] = {
                'status': 'completed',
                'report': risk_report
            }
            logger.info(
                f"✓ Risk assessed: {risk_report['overall_score']:.1f}% "
                f"({risk_report['risk_level']})"
            )
            
            # Step 5: Email Notification (if needed)
            email_sent = False
            if self.send_email and risk_report['requires_notification']:
                logger.info("Step 5: Email Notification")
                email_data = self.email_agent.prepare_email(
                    risk_report,
                    compliance_report,
                    summary,
                    metadata
                )
                send_result = self.email_agent.send_email(email_data)
                email_sent = True
                workflow_results['steps']['notification'] = {
                    'status': 'completed',
                    'email_data': email_data,
                    'send_result': send_result
                }
                logger.info(f"✓ Email notification sent: {send_result['status']}")
            else:
                workflow_results['steps']['notification'] = {
                    'status': 'skipped',
                    'reason': 'Not required' if not risk_report.get('requires_notification') else 'Disabled'
                }
                logger.info("○ Email notification not required")
            
            # Compile final results
            workflow_results.update({
                'status': 'completed',
                'use_azure': self.use_azure,
                'document_data': document_data,
                'metadata': metadata,
                'summary': summary,
                'compliance_report': compliance_report,
                'risk_report': risk_report,
                'email_sent': email_sent,
                'overall_status': self._determine_overall_status(compliance_report, risk_report)
            })
            
            logger.info(f"✓ Foundry workflow completed successfully for {Path(file_path).name}")
            return workflow_results
            
        except Exception as e:
            logger.error(f"✗ Foundry workflow failed: {str(e)}")
            workflow_results['status'] = 'failed'
            workflow_results['error'] = str(e)
            raise

    def _parse_summary(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse summary response into structured format."""
        import re
        
        def extract_section(pattern: str, text: str) -> str:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            return match.group(1).strip() if match else ""
        
        exec_summary = extract_section(
            r'(?:Executive Summary|Summary)[:\s]*\n(.+?)(?:\n\n|\n(?:Key Objectives|Budget|Timeline|Key Topics|Key Clauses))',
            text
        )
        
        clauses_text = extract_section(
            r'Key Clauses[:\s]*\n(.+?)(?:\n\n|$)',
            text
        )
        key_clauses = [line.strip('- •*"').strip() for line in clauses_text.split('\n') if line.strip() and len(line.strip()) > 20]
        
        return {
            'executive_summary': exec_summary if exec_summary else text[:500],
            'key_clauses': key_clauses[:5],
            'key_topics': self._extract_topics(text),
            'summary_length': len(text.split()),
            'detailed_analysis': text,
            'metadata': {
                'summary_method': 'foundry_agent_service',
                'original_word_count': metadata.get('word_count', 0),
            }
        }

    def _parse_compliance(self, text: str) -> Dict[str, Any]:
        """Parse compliance response into structured format."""
        import re
        
        # Extract confidence score (AI's certainty about its analysis)
        match = re.search(r"confidence\s*score[:\s]*(\d+)", text, re.IGNORECASE)
        confidence_score = min(100, max(0, int(match.group(1)))) if match else 70
        
        # Extract status
        text_lower = text.lower()
        if "compliant" in text_lower and "non-compliant" not in text_lower:
            status = "compliant"
        elif "non-compliant" in text_lower:
            status = "non_compliant"
        else:
            status = "requires_review"
        
        # Extract EO references
        eo_pattern = r'(?:Executive Order|EO|E\.O\.)[\s#]*(\d{5})'
        matches = re.findall(eo_pattern, text, re.IGNORECASE)
        unique_eos = list(set(matches))
        
        executive_orders = []
        for eo_num in unique_eos:
            executive_orders.append({
                'eo_number': eo_num,
                'title': f"Executive Order {eo_num}",
                'source': 'azure_ai_search'
            })
        
        # Calculate compliance_score based on status and analysis findings
        # compliance_score = HOW COMPLIANT the proposal is (0-100)
        # confidence_score = AI's CERTAINTY about its analysis (0-100)
        compliance_score = self._calculate_compliance_score_from_analysis(
            status=status,
            analysis_text=text,
            relevant_eos=executive_orders
        )
        
        return {
            'compliance_score': compliance_score,
            'overall_status': status,
            'analysis': text,
            'confidence_score': confidence_score,
            'violations': [],
            'warnings': [],
            'relevant_executive_orders': executive_orders,
            'citations': []
        }

    def _extract_topics(self, text: str) -> list:
        """Extract key topics from text."""
        keywords = [
            'compliance', 'budget', 'timeline', 'deliverable', 'requirement',
            'objective', 'sustainability', 'equity', 'cybersecurity', 'climate',
            'workforce', 'education', 'infrastructure', 'community', 'innovation',
            'DEI', 'diversity', 'inclusion', 'gender', 'immigration'
        ]
        text_lower = text.lower()
        return [kw for kw in keywords if kw in text_lower][:10]

    def _calculate_compliance_score_from_analysis(
        self,
        status: str,
        analysis_text: str,
        relevant_eos: list
    ) -> float:
        """
        Calculate compliance score based on analysis status and findings.
        
        This calculates HOW COMPLIANT the proposal is (0-100), which is different
        from confidence_score (how certain the AI is about its analysis).
        
        Args:
            status: Compliance status ('compliant', 'non_compliant', 'requires_review')
            analysis_text: Full analysis text from the compliance agent
            relevant_eos: List of relevant executive orders found
            
        Returns:
            Compliance score from 0-100
        """
        
        # Base score from status
        if status == 'compliant':
            base_score = 90.0
        elif status == 'non_compliant':
            base_score = 30.0
        else:  # requires_review
            base_score = 60.0
        
        text_lower = analysis_text.lower()
        
        # Adjust based on negative indicators in the analysis
        negative_indicators = [
            ('violation', -10),
            ('non-compliant', -10),
            ('concern', -5),
            ('issue', -3),
            ('risk', -3),
            ('problem', -5),
            ('fails to', -8),
            ('does not comply', -10),
            ('missing', -5),
            ('lacks', -5),
            ('dei', -5),  # DEI-related concerns
            ('diversity', -3),
            ('gender ideology', -5),
        ]
        
        penalty = 0
        for indicator, weight in negative_indicators:
            # Count occurrences but cap impact
            count = min(text_lower.count(indicator), 3)
            penalty += count * weight
        
        # Adjust based on positive indicators
        positive_indicators = [
            ('compliant', 5),
            ('meets requirements', 8),
            ('aligns with', 5),
            ('satisfies', 5),
            ('complies with', 8),
            ('no concerns', 10),
            ('no issues', 8),
        ]
        
        bonus = 0
        for indicator, weight in positive_indicators:
            if indicator in text_lower:
                bonus += weight
        
        # Bonus for having relevant executive orders (shows thorough analysis)
        if len(relevant_eos) >= 2:
            bonus += 5
        elif len(relevant_eos) == 0:
            penalty -= 10  # No EOs found is concerning
        
        # Calculate final score with bounds
        final_score = base_score + bonus + penalty
        return max(0.0, min(100.0, final_score))

    def _determine_overall_status(
        self,
        compliance_report: Dict[str, Any],
        risk_report: Dict[str, Any]
    ) -> str:
        """Determine overall workflow status."""
        risk_level = risk_report['risk_level']
        compliance_status = compliance_report['overall_status']
        
        if risk_level == 'high' or compliance_status == 'non_compliant':
            return 'requires_legal_review'
        elif risk_level in ['medium-high', 'medium']:
            return 'requires_review'
        else:
            return 'approved_with_conditions'

    def process_grant_proposal(
        self,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Process a grant proposal through the workflow (sync wrapper).
        
        Args:
            file_path: Path to the grant proposal file
            
        Returns:
            Complete workflow results including all agent outputs
        """
        import nest_asyncio
        
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.process_grant_proposal_async(file_path))
        else:
            nest_asyncio.apply()
            return asyncio.run(self.process_grant_proposal_async(file_path))

    def get_workflow_summary(self, workflow_results: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the workflow results."""
        if workflow_results['status'] != 'completed':
            return f"Workflow Status: {workflow_results['status']}"
        
        risk = workflow_results['risk_report']
        compliance = workflow_results['compliance_report']
        metadata = workflow_results['metadata']
        
        summary = f"""
========================================
GRANT PROPOSAL COMPLIANCE SUMMARY
(Foundry Agent Service)
========================================

Document: {metadata.get('file_name', 'Unknown')}
Word Count: {metadata.get('word_count', 0)}
Page Count: {metadata.get('page_count', 0)}

RISK ASSESSMENT
---------------
Overall Score: {risk['overall_score']:.1f}%
Risk Level: {risk['risk_level'].upper()}
Confidence: {risk['confidence']:.1f}%

COMPLIANCE STATUS
-----------------
Compliance Score: {compliance['compliance_score']:.1f}%
Status: {compliance['overall_status'].upper().replace('_', ' ')}
Relevant EOs: {len(compliance.get('relevant_executive_orders', []))}

OVERALL STATUS
--------------
{workflow_results['overall_status'].upper().replace('_', ' ')}

EMAIL NOTIFICATION
------------------
Sent: {'Yes' if workflow_results.get('email_sent') else 'No'}
Required: {'Yes' if risk.get('requires_notification') else 'No'}

========================================
"""
        return summary


async def main():
    """Example usage of the Foundry Workflow Orchestrator."""
    from dotenv import load_dotenv

    load_dotenv()

    # Initialize orchestrator
    orchestrator = SequentialWorkflowOrchestratorFoundry(
        use_azure=True,
        send_email=False
    )

    # Find a sample file
    sample_dir = Path('knowledge_base/sample_proposals')
    sample_files = list(sample_dir.glob('*.pdf')) + list(sample_dir.glob('*.txt'))
    
    if not sample_files:
        print("No sample files found")
        return
    
    test_file = str(sample_files[0])
    print(f"Processing: {test_file}")
    
    # Process proposal
    result = await orchestrator.process_grant_proposal_async(test_file)
    
    # Print summary
    print(orchestrator.get_workflow_summary(result))


if __name__ == "__main__":
    asyncio.run(main())
