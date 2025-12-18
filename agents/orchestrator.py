"""
Agent Orchestrator
Coordinates the workflow between all compliance validation agents.
"""

import logging
import asyncio
import os
from typing import Dict, Any
from pathlib import Path

from .document_ingestion_agent import DocumentIngestionAgent
from .summarization_agent import SummarizationAgent
from .compliance_agent import ComplianceAgent
from .risk_scoring_agent import RiskScoringAgent
from .email_trigger_agent import EmailTriggerAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates the complete compliance validation workflow.
    Coordinates all agents from document ingestion through email notification.
    """
    
    def __init__(self, use_azure: bool = False):
        """
        Initialize the Agent Orchestrator with all sub-agents.
        
        Args:
            use_azure: If True, use Azure services. Otherwise, use local processing.
        """
        self.use_azure = use_azure
        
        # Initialize all agents
        self.document_agent = DocumentIngestionAgent(use_azure=use_azure)
        
        # Initialize configuration from environment
        project_endpoint = os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT") or os.getenv("AZURE_AI_PROJECT_ENDPOINT", "")
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "")
        search_index = os.getenv("AZURE_SEARCH_INDEX_NAME") or os.getenv("AZURE_SEARCH_INDEX", "grant-compliance-index")
        
        # Check if we should use managed identity (only in production/Azure environments)
        use_managed_identity = os.getenv("USE_MANAGED_IDENTITY", "false").lower() == "true"
        
        # Initialize SummarizationAgent with Agent Framework
        self.summary_agent = SummarizationAgent(
            project_endpoint=project_endpoint,
            model_deployment_name=deployment_name,
            use_managed_identity=use_managed_identity,
            api_key=os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_AI_FOUNDRY_API_KEY"),
        )
        
        if use_azure and search_endpoint:
            # For Azure services with API keys (local development and most deployments)
            self.compliance_agent = ComplianceAgent(
                project_endpoint=project_endpoint,
                model_deployment_name=deployment_name,
                search_endpoint=search_endpoint,
                search_index_name=search_index,
                azure_search_document_truncation_size=int(os.getenv("AZURE_SEARCH_DOCUMENT_CONTENT_TRUNCATION_SIZE", "10000")),
                use_managed_identity=use_managed_identity,
                search_api_key=os.getenv("AZURE_SEARCH_API_KEY"),
            )
        else:
            # For local development without Azure Search, use environment variables with API keys
            self.compliance_agent = ComplianceAgent(
                project_endpoint=project_endpoint,
                model_deployment_name=deployment_name,
                search_endpoint=search_endpoint,
                search_index_name=search_index,
                azure_search_document_truncation_size=int(os.getenv("AZURE_SEARCH_DOCUMENT_CONTENT_TRUNCATION_SIZE", "1000")),
                use_managed_identity=False,
                search_api_key=os.getenv("AZURE_SEARCH_API_KEY"),
            )
        
        self.risk_agent = RiskScoringAgent()
        self.email_agent = EmailTriggerAgent(use_graph_api=use_azure)
        
        logger.info(f"Agent Orchestrator initialized (Azure: {use_azure})")
    
    async def process_grant_proposal_async(
        self,
        file_path: str,
        send_email: bool = False
    ) -> Dict[str, Any]:
        """
        Process a grant proposal through the complete validation workflow (async version).
        
        Args:
            file_path: Path to the grant proposal file
            send_email: If True and risk warrants, send email notification
            
        Returns:
            Complete workflow results including all agent outputs
        """
        logger.info(f"Starting workflow for: {file_path}")
        
        workflow_results = {
            'status': 'in_progress',
            'file_path': file_path,
            'steps': {}
        }
        
        try:
            # Step 1: Document Ingestion
            logger.info("Step 1: Document Ingestion")
            document_data = self.document_agent.process_document(file_path)
            metadata = self.document_agent.extract_metadata(document_data)
            workflow_results['steps']['ingestion'] = {
                'status': 'completed',
                'metadata': metadata
            }
            logger.info(f"✓ Document ingested: {metadata.get('word_count', 0)} words")
            
            # Step 2: Summarization
            logger.info("Step 2: Summarization")
            summary = await self.summary_agent.generate_summary(
                document_data['text'],
                metadata
            )
            workflow_results['steps']['summarization'] = {
                'status': 'completed',
                'summary': summary
            }
            logger.info(f"✓ Summary generated: {len(summary.get('key_clauses', []))} key clauses")
            
            # Step 3: Compliance Validation (async)
            logger.info("Step 3: Compliance Validation")
            compliance_analysis = await self.compliance_agent.analyze_proposal(
                document_data['text'],
                context={
                    'file_path': file_path,
                    'metadata': metadata,
                    'summary': summary
                }
            )
            
            # Convert to format expected by risk scoring
            compliance_report = {
                'compliance_score': compliance_analysis['confidence_score'],
                'overall_status': compliance_analysis['status'].lower().replace(' ', '_'),
                'analysis': compliance_analysis['analysis'],
                'confidence_score': compliance_analysis['confidence_score'],
                'violations': [],
                'warnings': [],
                'relevant_executive_orders': compliance_analysis.get('relevant_executive_orders', []),
                'citations': compliance_analysis.get('citations', [])  # Include citations
            }
            
            workflow_results['steps']['compliance'] = {
                'status': 'completed',
                'report': compliance_report
            }
            logger.info(
                f"✓ Compliance validated: {compliance_report['compliance_score']:.1f}% "
                f"({compliance_report['overall_status']})"
            )
            
            # Step 4: Risk Scoring
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
            if send_email and risk_report['requires_notification']:
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
                    'reason': 'Not required' if not risk_report['requires_notification'] else 'Disabled'
                }
                logger.info("○ Email notification not required")
            
            # Compile final results
            workflow_results.update({
                'status': 'completed',
                'document_data': document_data,
                'metadata': metadata,
                'summary': summary,
                'compliance_report': compliance_report,
                'risk_report': risk_report,
                'email_sent': email_sent,
                'overall_status': self._determine_overall_status(
                    compliance_report,
                    risk_report
                )
            })
            
            logger.info(f"✓ Workflow completed successfully for {Path(file_path).name}")
            return workflow_results
            
        except Exception as e:
            logger.error(f"✗ Workflow failed: {str(e)}")
            workflow_results['status'] = 'failed'
            workflow_results['error'] = str(e)
            raise
    
    def process_grant_proposal(
        self,
        file_path: str,
        send_email: bool = False
    ) -> Dict[str, Any]:
        """
        Process a grant proposal through the complete validation workflow.
        
        This is a synchronous wrapper around process_grant_proposal_async.
        
        Args:
            file_path: Path to the grant proposal file
            send_email: If True and risk warrants, send email notification
            
        Returns:
            Complete workflow results including all agent outputs
        """
        try:
            # Try to get the running event loop
            asyncio.get_running_loop()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            return asyncio.run(self.process_grant_proposal_async(file_path, send_email))
        else:
            # Event loop is already running, create task instead
            import nest_asyncio
            nest_asyncio.apply()
            return asyncio.run(self.process_grant_proposal_async(file_path, send_email))
    
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
    
    def get_workflow_summary(self, workflow_results: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of the workflow results.
        
        Args:
            workflow_results: Results from process_grant_proposal
            
        Returns:
            Formatted summary string
        """
        if workflow_results['status'] != 'completed':
            return f"Workflow Status: {workflow_results['status']}"
        
        risk = workflow_results['risk_report']
        compliance = workflow_results['compliance_report']
        metadata = workflow_results['metadata']
        
        summary = f"""
========================================
GRANT PROPOSAL COMPLIANCE SUMMARY
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
Violations: {len(compliance.get('violations', []))}
Warnings: {len(compliance.get('warnings', []))}
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
