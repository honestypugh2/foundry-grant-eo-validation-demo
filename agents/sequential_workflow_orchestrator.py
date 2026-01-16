"""
Sequential Workflow Orchestrator
Uses Agent Framework's Sequential Workflow pattern to coordinate compliance validation agents.
"""

import logging
import os
from typing import Dict, Any, Optional
from pathlib import Path

from agent_framework import (
    Executor,
    WorkflowBuilder,
    WorkflowContext,
    WorkflowOutputEvent,
    WorkflowStatusEvent,
    ExecutorFailedEvent,
    WorkflowFailedEvent,
    WorkflowRunState,
    handler,
    SequentialBuilder,
)
from azure.identity import DefaultAzureCredential
from typing_extensions import Never

from .document_ingestion_agent import DocumentIngestionAgent
from .summarization_agent import SummarizationAgent
from .compliance_agent import ComplianceAgent
from .risk_scoring_agent import RiskScoringAgent
from .email_trigger_agent import EmailTriggerAgent

logger = logging.getLogger(__name__)


# Define typed data structures for workflow state
class DocumentData(dict):
    """Document ingestion result"""
    pass


class WorkflowState(dict):
    """Complete workflow state passed between executors"""
    pass


class DocumentIngestionExecutor(Executor):
    """
    Executor for document ingestion step.
    Processes the document file and extracts metadata.
    """
    
    def __init__(self, use_azure: bool = False, use_managed_identity: bool = True):
        self.agent = DocumentIngestionAgent(
            use_azure=use_azure,
            use_managed_identity=use_managed_identity
        )
        super().__init__(id="document_ingestion")
    
    @handler
    async def process(
        self,
        file_path: str,
        ctx: WorkflowContext[WorkflowState]
    ) -> None:
        """
        Process document and forward state to next executor.
        
        Args:
            file_path: Path to the document file
            ctx: Workflow context for forwarding state
        """
        logger.info("Step 1: Document Ingestion")
        
        # Process document
        document_data = self.agent.process_document(file_path)
        metadata = self.agent.extract_metadata(document_data)
        
        logger.info(f"✓ Document ingested: {metadata.get('word_count', 0)} words")
        
        # Create workflow state
        state = WorkflowState({
            'file_path': file_path,
            'document_data': document_data,
            'metadata': metadata,
            'steps': {
                'ingestion': {
                    'status': 'completed',
                    'metadata': metadata
                }
            }
        })
        
        # Forward to next executor
        await ctx.send_message(state)


class SummarizationExecutor(Executor):
    """
    Executor for document summarization step.
    Generates summary and key clauses from the document.
    """
    
    def __init__(
        self,
        project_endpoint: str,
        model_deployment_name: str,
        use_managed_identity: bool = True,
        api_key: Optional[str] = None,
    ):
        self.agent = SummarizationAgent(
            project_endpoint=project_endpoint,
            model_deployment_name=model_deployment_name,
            use_managed_identity=use_managed_identity,
            api_key=api_key
        )
        super().__init__(id="summarization")
    
    @handler
    async def process(
        self,
        state: WorkflowState,
        ctx: WorkflowContext[WorkflowState]
    ) -> None:
        """
        Generate summary and forward updated state.
        
        Args:
            state: Current workflow state
            ctx: Workflow context for forwarding state
        """
        logger.info("Step 2: Summarization")
        
        # Generate summary
        summary = await self.agent.generate_summary(
            state['document_data']['text'],
            state['metadata']
        )
        
        logger.info(f"✓ Summary generated: {len(summary.get('key_clauses', []))} key clauses")
        
        # Update state
        state['summary'] = summary
        state['steps']['summarization'] = {
            'status': 'completed',
            'summary': summary
        }
        
        # Forward to next executor
        await ctx.send_message(state)


class ComplianceValidationExecutor(Executor):
    """
    Executor for compliance validation step.
    Analyzes document against regulatory requirements.
    Uses hosted Azure AI Search tool for knowledge base queries.
    """
    
    def __init__(
        self,
        project_endpoint: str,
        model_deployment_name: str,
        search_index_name: str,
        search_connection_id: Optional[str] = None,
        search_query_type: str = "simple",
    ):
        self.agent = ComplianceAgent(
            project_endpoint=project_endpoint,
            model_deployment_name=model_deployment_name,
            search_index_name=search_index_name,
            search_connection_id=search_connection_id,
            search_query_type=search_query_type,
        )
        super().__init__(id="compliance_validation")
    
    @handler
    async def process(
        self,
        state: WorkflowState,
        ctx: WorkflowContext[WorkflowState]
    ) -> None:
        """
        Validate compliance and forward updated state.
        
        Args:
            state: Current workflow state
            ctx: Workflow context for forwarding state
        """
        logger.info("Step 3: Compliance Validation")
        
        # Analyze compliance
        compliance_analysis = await self.agent.analyze_proposal(
            state['document_data']['text'],
            context={
                'file_path': state['file_path'],
                'metadata': state['metadata'],
                'summary': state['summary']
            }
        )
        
        # Convert to expected format
        compliance_report = {
            'compliance_score': compliance_analysis['confidence_score'],
            'overall_status': compliance_analysis['status'].lower().replace(' ', '_'),
            'analysis': compliance_analysis['analysis'],
            'confidence_score': compliance_analysis['confidence_score'],
            'violations': [],
            'warnings': [],
            'relevant_executive_orders': compliance_analysis.get('relevant_executive_orders', []),
            'citations': compliance_analysis.get('citations', [])
        }
        
        logger.info(
            f"✓ Compliance validated: {compliance_report['compliance_score']:.1f}% "
            f"({compliance_report['overall_status']})"
        )
        
        # Update state
        state['compliance_report'] = compliance_report
        state['steps']['compliance'] = {
            'status': 'completed',
            'report': compliance_report
        }
        
        # Forward to next executor
        await ctx.send_message(state)


class RiskScoringExecutor(Executor):
    """
    Executor for risk scoring step.
    Calculates risk score based on compliance and other factors.
    """
    
    def __init__(self):
        self.agent = RiskScoringAgent()
        super().__init__(id="risk_scoring")
    
    @handler
    async def process(
        self,
        state: WorkflowState,
        ctx: WorkflowContext[WorkflowState]
    ) -> None:
        """
        Calculate risk score and forward updated state.
        
        Args:
            state: Current workflow state
            ctx: Workflow context for forwarding state
        """
        logger.info("Step 4: Risk Scoring")
        
        # Calculate risk
        risk_report = self.agent.calculate_risk_score(
            state['compliance_report'],
            state['summary'],
            state['metadata']
        )
        
        logger.info(
            f"✓ Risk assessed: {risk_report['overall_score']:.1f}% "
            f"({risk_report['risk_level']})"
        )
        
        # Update state
        state['risk_report'] = risk_report
        state['steps']['risk_scoring'] = {
            'status': 'completed',
            'report': risk_report
        }
        
        # Forward to next executor
        await ctx.send_message(state)


class EmailNotificationExecutor(Executor):
    """
    Executor for email notification step (terminal node).
    Sends email if risk warrants notification and yields final output.
    """
    
    def __init__(self, use_graph_api: bool = False, send_email: bool = False):
        self.agent = EmailTriggerAgent(use_graph_api=use_graph_api)
        self.send_email = send_email
        super().__init__(id="email_notification")
    
    @handler
    async def process(
        self,
        state: WorkflowState,
        ctx: WorkflowContext[Never, Dict[str, Any]]
    ) -> None:
        """
        Send email notification if needed and yield final workflow output.
        
        Args:
            state: Current workflow state
            ctx: Workflow context for yielding output
        """
        logger.info("Step 5: Email Notification")
        
        email_sent = False
        risk_report = state['risk_report']
        
        if self.send_email and risk_report['requires_notification']:
            # Prepare and send email
            email_data = self.agent.prepare_email(
                risk_report,
                state['compliance_report'],
                state['summary'],
                state['metadata']
            )
            
            send_result = self.agent.send_email(email_data)
            email_sent = True
            
            state['steps']['notification'] = {
                'status': 'completed',
                'email_data': email_data,
                'send_result': send_result
            }
            logger.info(f"✓ Email notification sent: {send_result['status']}")
        else:
            state['steps']['notification'] = {
                'status': 'skipped',
                'reason': 'Not required' if not risk_report['requires_notification'] else 'Disabled'
            }
            logger.info("○ Email notification not required")
        
        # Determine overall status
        overall_status = self._determine_overall_status(
            state['compliance_report'],
            state['risk_report']
        )
        
        # Compile final results
        final_results = {
            'status': 'completed',
            'file_path': state['file_path'],
            'document_data': state['document_data'],
            'metadata': state['metadata'],
            'summary': state['summary'],
            'compliance_report': state['compliance_report'],
            'risk_report': state['risk_report'],
            'email_sent': email_sent,
            'overall_status': overall_status,
            'steps': state['steps']
        }
        
        logger.info(f"✓ Workflow completed successfully for {Path(state['file_path']).name}")
        
        # Yield final output (terminal node)
        await ctx.yield_output(final_results)
    
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


class SequentialWorkflowOrchestrator:
    """
    Sequential Workflow Orchestrator using Agent Framework.
    Coordinates compliance validation through a sequential pipeline of agents.
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
        
        # Check if we should use managed identity
        self.use_managed_identity = os.getenv("USE_MANAGED_IDENTITY", "true").lower() == "true"
        
        # Initialize configuration from environment
        self.project_endpoint = os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT") or os.getenv("AZURE_AI_PROJECT_ENDPOINT", "")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "")
        self.search_index = os.getenv("AZURE_SEARCH_INDEX_NAME") or os.getenv("AZURE_SEARCH_INDEX", "grant-compliance-index")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_AI_FOUNDRY_API_KEY")
        
        logger.info(f"Sequential Workflow Orchestrator initialized (Azure: {use_azure})")
    
    def _build_workflow(self) -> Any:
        """
        Build the sequential workflow with all executors.
        
        Returns:
            Configured workflow ready for execution
        """
        # Create executors
        doc_executor = DocumentIngestionExecutor(
            use_azure=self.use_azure,
            use_managed_identity=self.use_managed_identity
        )
        
        summary_executor = SummarizationExecutor(
            project_endpoint=self.project_endpoint,
            model_deployment_name=self.deployment_name,
            use_managed_identity=self.use_managed_identity,
            api_key=self.api_key
        )
        
        # ComplianceValidationExecutor uses hosted Azure AI Search tool
        # Requires AI_SEARCH_PROJECT_CONNECTION_ID to be set in the Azure AI Foundry project
        compliance_executor = ComplianceValidationExecutor(
            project_endpoint=self.project_endpoint,
            model_deployment_name=self.deployment_name,
            search_index_name=self.search_index,
            search_connection_id=os.getenv("AI_SEARCH_PROJECT_CONNECTION_ID"),
            search_query_type=os.getenv("AI_SEARCH_QUERY_TYPE", "simple"),
        )
        
        risk_executor = RiskScoringExecutor()
        
        email_executor = EmailNotificationExecutor(
            use_graph_api=self.use_azure,
            send_email=self.send_email
        )
        
        # Build sequential workflow: doc -> summary -> compliance -> risk -> email
        workflow = (
            WorkflowBuilder()
            .set_start_executor(doc_executor)
            .add_edge(doc_executor, summary_executor)
            .add_edge(summary_executor, compliance_executor)
            .add_edge(compliance_executor, risk_executor)
            .add_edge(risk_executor, email_executor)
            .build()
        )
        
        return workflow
    
    async def process_grant_proposal_async(
        self,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Process a grant proposal through the sequential workflow (async version).
        
        Args:
            file_path: Path to the grant proposal file
            
        Returns:
            Complete workflow results including all agent outputs
        """
        logger.info(f"Starting sequential workflow for: {file_path}")
        
        workflow_results = {
            'status': 'in_progress',
            'file_path': file_path,
            'steps': {}
        }
        
        try:
            # Build the workflow
            workflow = self._build_workflow()
            
            # Run workflow with streaming
            output_event: WorkflowOutputEvent | None = None
            
            async for event in workflow.run_stream(file_path):
                if isinstance(event, WorkflowStatusEvent):
                    if event.state == WorkflowRunState.IN_PROGRESS:
                        logger.debug("Workflow state: IN_PROGRESS")
                    elif event.state == WorkflowRunState.IDLE:
                        logger.debug("Workflow state: IDLE")
                
                elif isinstance(event, WorkflowOutputEvent):
                    output_event = event
                    logger.info("Workflow output received")
                
                elif isinstance(event, ExecutorFailedEvent):
                    logger.error(
                        f"Executor failed: {event.executor_id} - "
                        f"{event.details.error_type}: {event.details.message}"
                    )
                    raise Exception(f"Executor {event.executor_id} failed: {event.details.message}")
                
                elif isinstance(event, WorkflowFailedEvent):
                    logger.error(
                        f"Workflow failed: {event.details.error_type}: {event.details.message}"
                    )
                    raise Exception(f"Workflow failed: {event.details.message}")
            
            # Extract final results from output event
            if output_event and output_event.data is not None:
                return output_event.data
            else:
                raise Exception("No workflow output received")
        
        except Exception as e:
            logger.error(f"✗ Workflow failed: {str(e)}")
            workflow_results['status'] = 'failed'
            workflow_results['error'] = str(e)
            raise
    
    def process_grant_proposal(
        self,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Process a grant proposal through the sequential workflow (sync wrapper).
        
        Args:
            file_path: Path to the grant proposal file
            
        Returns:
            Complete workflow results including all agent outputs
        """
        import asyncio
        
        try:
            # Try to get the running event loop
            asyncio.get_running_loop()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            return asyncio.run(self.process_grant_proposal_async(file_path))
        else:
            # Event loop is already running, create task instead
            import nest_asyncio
            nest_asyncio.apply()
            return asyncio.run(self.process_grant_proposal_async(file_path))
    
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
(Sequential Workflow)
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
