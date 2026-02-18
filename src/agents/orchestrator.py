"""
Agent Orchestrator
Coordinates the workflow between all compliance validation agents.
"""

import logging
import asyncio
import os
from typing import Dict, Any, Optional
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
        
        # Check if we should use managed identity (default: True for production-ready authentication)
        use_managed_identity = os.getenv("USE_MANAGED_IDENTITY", "true").lower() == "true"
        
        # Initialize all agents with consistent managed identity setting
        self.document_agent = DocumentIngestionAgent(use_azure=use_azure, use_managed_identity=use_managed_identity)
        
        # Initialize configuration from environment
        project_endpoint = os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT") or os.getenv("AZURE_AI_PROJECT_ENDPOINT", "")
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        search_index = os.getenv("AZURE_SEARCH_INDEX_NAME") or os.getenv("AZURE_SEARCH_INDEX", "grant-compliance-index")
        
        # Initialize SummarizationAgent with Agent Framework
        self.summary_agent = SummarizationAgent(
            project_endpoint=project_endpoint,
            model_deployment_name=deployment_name,
            use_managed_identity=use_managed_identity,
            api_key=os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_AI_FOUNDRY_API_KEY"),
        )
        
        # ComplianceAgent now uses hosted Azure AI Search tool
        # Requires AI_SEARCH_PROJECT_CONNECTION_ID to be configured in Azure AI Foundry project
        self.compliance_agent = ComplianceAgent(
            project_endpoint=project_endpoint,
            model_deployment_name=deployment_name,
            search_index_name=search_index,
            search_connection_id=os.getenv("AI_SEARCH_PROJECT_CONNECTION_ID"),
            search_query_type=os.getenv("AI_SEARCH_QUERY_TYPE", "simple"),
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
            
            # Calculate compliance_score based on status and findings
            # compliance_score = HOW COMPLIANT the proposal is (0-100)
            # confidence_score = AI's CERTAINTY about its analysis (0-100)
            status = compliance_analysis['status'].lower().replace(' ', '_')
            compliance_score = self._calculate_compliance_score_from_analysis(
                status=status,
                analysis_text=compliance_analysis['analysis'],
                relevant_eos=compliance_analysis.get('relevant_executive_orders', [])
            )
            
            # Extract violations and warnings from analysis
            violations = self._extract_violations_from_analysis(
                analysis_text=compliance_analysis['analysis'],
                status=status,
                relevant_eos=compliance_analysis.get('relevant_executive_orders', []),
                compliance_score=compliance_score
            )
            
            warnings = self._extract_warnings_from_analysis(
                analysis_text=compliance_analysis['analysis'],
                status=status
            )
            
            # Convert to format expected by risk scoring
            compliance_report = {
                'compliance_score': compliance_score,
                'overall_status': status,
                'analysis': compliance_analysis['analysis'],
                'confidence_score': compliance_analysis['confidence_score'],
                'violations': violations,
                'warnings': warnings,
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
                'use_azure': self.use_azure,
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

    def _extract_violations_from_analysis(
        self,
        analysis_text: str,
        status: str,
        relevant_eos: list,
        compliance_score: float = None
    ) -> list:
        """
        Extract compliance violations from the analysis text.
        
        Parses the AI analysis to identify specific compliance violations
        and associates them with relevant executive orders. Handles both
        structured output (Key Findings:, Concerns:) and inline mentions.
        
        Args:
            analysis_text: Full analysis text from the compliance agent
            status: Compliance status ('compliant', 'non_compliant', 'requires_review')
            relevant_eos: List of relevant executive orders found
            compliance_score: Optional compliance score to determine extraction threshold
            
        Returns:
            List of violation dictionaries with message, executive_order, and requirement
        """
        import re
        
        violations = []
        text_lower = analysis_text.lower()
        
        # Helper to get associated EO
        def get_associated_eo(text_context: str = '') -> str:
            if not relevant_eos:
                return 'Unknown'
            # Try to find an EO mentioned in the context
            for eo in relevant_eos:
                eo_name = eo.get('name', eo.get('eo_number', eo.get('number', '')))
                if eo_name and str(eo_name) in text_context:
                    return str(eo_name)
            # Default to first EO
            return relevant_eos[0].get('name', relevant_eos[0].get('eo_number', relevant_eos[0].get('number', 'Unknown')))
        
        # Helper to get requirement from EOs
        def get_requirement() -> str:
            for eo in relevant_eos:
                if eo.get('key_requirements'):
                    reqs = eo['key_requirements']
                    return reqs[0] if reqs else ''
            return ''
        
        # Extract violations if:
        # 1. Status indicates non-compliance or review needed, OR
        # 2. Compliance score is low (below 80), OR
        # 3. Analysis text contains violation keywords
        has_violation_keywords = any(kw in text_lower for kw in [
            'violation', 'non-compliant', 'does not comply', 'fails to', 
            'concern', 'issue', 'problem', 'dei', 'gender ideology',
            'key findings', 'concerns'
        ])
        
        # Skip only if status is compliant AND no violation keywords AND score is high
        if status == 'compliant' and not has_violation_keywords:
            if compliance_score is None or compliance_score >= 80:
                return violations
        
        # === SECTION-BASED EXTRACTION ===
        # Extract from "Key Findings:" section (bullet points)
        key_findings_match = re.search(
            r'(?:^|\n)\s*[-*]?\s*Key\s+Findings[:\s]*\n((?:[ \t]*[-*•]\s*[^\n]+\n?)+)',
            analysis_text, re.IGNORECASE | re.MULTILINE
        )
        if key_findings_match:
            findings_text = key_findings_match.group(1)
            bullets = re.findall(r'[-*•]\s*([^\n]+)', findings_text)
            for bullet in bullets:
                bullet_clean = bullet.strip()
                if bullet_clean and len(bullet_clean) > 10:
                    violations.append({
                        'message': f"Key Finding: {bullet_clean[:200]}",
                        'executive_order': get_associated_eo(bullet_clean),
                        'requirement': get_requirement(),
                        'severity': 'high' if any(kw in bullet_clean.lower() for kw in ['violation', 'non-compliant', 'critical']) else 'medium'
                    })
        
        # Extract from "Concerns:" section (bullet points)
        concerns_match = re.search(
            r'(?:^|\n)\s*[-*]?\s*Concerns[:\s]*\n((?:[ \t]*[-*•]\s*[^\n]+\n?)+)',
            analysis_text, re.IGNORECASE | re.MULTILINE
        )
        if concerns_match:
            concerns_text = concerns_match.group(1)
            bullets = re.findall(r'[-*•]\s*([^\n]+)', concerns_text)
            for bullet in bullets:
                bullet_clean = bullet.strip()
                if bullet_clean and len(bullet_clean) > 10:
                    violations.append({
                        'message': f"Concern: {bullet_clean[:200]}",
                        'executive_order': get_associated_eo(bullet_clean),
                        'requirement': get_requirement(),
                        'severity': 'medium'
                    })
        
        # === PATTERN-BASED EXTRACTION (for less structured text) ===
        violation_patterns = [
            (r'(?:violation|non-compliant|does not comply|fails to comply)[:\s]+([^.\n]+)', 'Compliance Violation'),
            (r'(?:lacks|missing|absent)[:\s]+([^.\n]+(?:requirement|provision|clause))', 'Missing Requirement'),
            (r'(?:DEI|diversity|equity|inclusion)[^.\n]*(?:violation|concern|issue)[^.\n]*', 'DEI-Related Concern'),
            (r'(?:gender ideology|gender-related)[^.\n]*(?:violation|concern|issue)[^.\n]*', 'Gender Policy Concern'),
            (r'(?:climate|environmental)[^.\n]*(?:violation|concern|non-compliant)[^.\n]*', 'Environmental Compliance'),
            (r'(?:cybersecurity|security)[^.\n]*(?:violation|concern|issue|non-compliant)[^.\n]*', 'Cybersecurity Concern'),
            # Additional patterns for finding issues
            (r'(?:does not|doesn\'t|fails to|unable to)[:\s]+([^.\n]+)', 'Compliance Issue'),
            (r'(?:inconsistent with|contradicts|conflicts with)[:\s]+([^.\n]+)', 'Policy Conflict'),
        ]
        
        # Extract specific violations from text
        for pattern, violation_type in violation_patterns:
            matches = re.findall(pattern, analysis_text, re.IGNORECASE)
            for match in matches:
                message = match.strip() if isinstance(match, str) else str(match)
                message = message[:200]
                
                # Skip if too short or generic
                if len(message) < 10:
                    continue
                
                violations.append({
                    'message': f"{violation_type}: {message}",
                    'executive_order': get_associated_eo(message),
                    'requirement': get_requirement(),
                    'severity': 'high' if 'violation' in violation_type.lower() else 'medium'
                })
        
        # Check for general non-compliance indicators if no specific violations found
        if not violations and status == 'non_compliant':
            general_indicators = [
                ('non-compliant', 'Proposal marked as non-compliant'),
                ('does not comply', 'Proposal does not comply with requirements'),
                ('fails to', 'Proposal fails to meet requirements'),
                ('violation', 'Compliance violation identified'),
            ]
            
            for indicator, message in general_indicators:
                if indicator in text_lower:
                    violations.append({
                        'message': message,
                        'executive_order': get_associated_eo(analysis_text),
                        'requirement': get_requirement(),
                        'severity': 'high'
                    })
                    break
        
        # Deduplicate violations by message content
        seen_messages = set()
        unique_violations = []
        for v in violations:
            # Normalize message for comparison
            msg_key = re.sub(r'\s+', ' ', v['message'].lower()[:60])
            if msg_key not in seen_messages:
                seen_messages.add(msg_key)
                unique_violations.append(v)
        
        return unique_violations[:10]

    def _extract_warnings_from_analysis(
        self,
        analysis_text: str,
        status: str
    ) -> list:
        """
        Extract compliance warnings from the analysis text.
        
        Warnings are less severe than violations but still require attention.
        
        Args:
            analysis_text: Full analysis text from the compliance agent
            status: Compliance status
            
        Returns:
            List of warning dictionaries
        """
        import re
        
        warnings = []
        text_lower = analysis_text.lower()
        
        warning_indicators = [
            (r'(?:concern|caution|attention)[:\s]+([^.\n]+)', 'Requires Attention'),
            (r'(?:recommend|suggest|should)[:\s]+([^.\n]+)', 'Recommendation'),
            (r'(?:unclear|ambiguous|vague)[:\s]+([^.\n]+)', 'Clarification Needed'),
            (r'(?:review|verify|confirm)[:\s]+([^.\n]+)', 'Review Required'),
        ]
        
        for pattern, warning_type in warning_indicators:
            matches = re.findall(pattern, analysis_text, re.IGNORECASE)
            for match in matches[:2]:  # Limit per pattern
                message = match.strip() if isinstance(match, str) else str(match)
                warnings.append({
                    'message': f"{warning_type}: {message[:150]}",
                    'severity': 'medium'
                })
        
        # Status-based warning
        if status == 'requires_review' and not warnings:
            warnings.append({
                'message': 'Proposal requires manual review due to compliance complexity',
                'severity': 'medium'
            })
        
        return warnings[:5]  # Limit to 5 warnings
    
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
