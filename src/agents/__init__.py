"""
Grant Proposal Compliance Automation Agents

This package contains all the AI agents for the compliance validation system.

Two orchestration patterns are available:
  Agent Framework (default): compliance_agent.py, summarization_agent.py, sequential_workflow_orchestrator.py
  Foundry Agent Service:     *_foundry.py variants — set AGENT_SERVICE=foundry in .env
"""

from .document_ingestion_agent import DocumentIngestionAgent
from .summarization_agent import SummarizationAgent
from .compliance_agent import ComplianceAgent
from .risk_scoring_agent import RiskScoringAgent
from .email_trigger_agent import EmailTriggerAgent
from .sequential_workflow_orchestrator import SequentialWorkflowOrchestrator

__all__ = [
    'DocumentIngestionAgent',
    'SummarizationAgent',
    'ComplianceAgent',
    'RiskScoringAgent',
    'EmailTriggerAgent',
    'SequentialWorkflowOrchestrator'
]
