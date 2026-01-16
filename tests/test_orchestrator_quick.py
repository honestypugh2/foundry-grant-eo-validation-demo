"""
Quick Orchestrator Test
Tests the workflow using updated agents with Agent Framework
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import asyncio
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import agents
from agents.document_ingestion_agent import DocumentIngestionAgent
from agents.summarization_agent import SummarizationAgent
from agents.compliance_agent import ComplianceAgent
from agents.risk_scoring_agent import RiskScoringAgent
from agents.email_trigger_agent import EmailTriggerAgent


async def main():
    print('=' * 80)
    print('ORCHESTRATOR WORKFLOW TEST')
    print('=' * 80)

    # Load environment
    load_dotenv()

    # Find a sample file
    sample_dir = Path('knowledge_base/sample_proposals')
    sample_files = list(sample_dir.glob('*.pdf')) + list(sample_dir.glob('*.txt'))

    if not sample_files:
        # Try executive orders as fallback
        sample_dir = Path('knowledge_base/executive_orders')
        sample_files = list(sample_dir.glob('*.txt'))

    if not sample_files:
        print('❌ No sample files found')
        sys.exit(1)

    test_file = str(sample_files[0])
    print(f'\n📄 Testing with: {test_file}')
    print()

    # Initialize agents
    print('1. Initializing Agents...')
    doc_agent = DocumentIngestionAgent(use_azure=False)

    # Initialize configuration from environment (matching orchestrator.py)
    project_endpoint = os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT") or os.getenv("AZURE_AI_PROJECT_ENDPOINT", "")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    search_index = os.getenv("AZURE_SEARCH_INDEX_NAME") or os.getenv("AZURE_SEARCH_INDEX", "grant-compliance-index")
    use_managed_identity = os.getenv("USE_MANAGED_IDENTITY", "true").lower() == "true"

    # Initialize SummarizationAgent with Agent Framework
    summary_agent = SummarizationAgent(
        project_endpoint=project_endpoint,
        model_deployment_name=deployment_name,
        use_managed_identity=use_managed_identity,
        api_key=os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_AI_FOUNDRY_API_KEY"),
    )

    # Initialize ComplianceAgent with hosted Azure AI Search tool
    compliance_agent = ComplianceAgent(
        project_endpoint=project_endpoint,
        model_deployment_name=deployment_name,
        search_index_name=search_index,
        search_connection_id=os.getenv("AI_SEARCH_PROJECT_CONNECTION_ID"),
        search_query_type=os.getenv("AI_SEARCH_QUERY_TYPE", "simple"),
    )

    risk_agent = RiskScoringAgent()
    email_agent = EmailTriggerAgent(use_graph_api=False)
    print('   ✅ All agents initialized')

    # Run workflow manually
    print('\n2. Running workflow steps...')
    print('-' * 80)

    # Step 1: Document Ingestion
    print('\n📄 Step 1: Document Ingestion')
    document_data = doc_agent.process_document(test_file)
    metadata = doc_agent.extract_metadata(document_data)
    print(f'   ✅ Extracted {metadata.get("word_count", 0)} words, {metadata.get("page_count", 0)} pages')
    
    # Step 2: Summarization
    print('\n📋 Step 2: Summarization')
    summary = await summary_agent.generate_summary(
        document_data['text'],
        metadata  # Pass full metadata dict, not just filename
    )
    key_clauses = len(summary.get('key_clauses', []))
    print(f'   ✅ Generated summary with {key_clauses} key clauses')
    
    # Step 3: Compliance Validation
    print('\n✅ Step 3: Compliance Validation')
    compliance_report = await compliance_agent.analyze_proposal(
        document_data['text'],
        context=metadata
    )
    compliance_score = compliance_report.get('compliance_score', compliance_report.get('confidence_score', 0))
    status = compliance_report.get('overall_status', compliance_report.get('status', 'unknown'))
    print(f'   ✅ Compliance: {compliance_score:.1f}% ({status})')
    
    # Step 4: Risk Scoring
    print('\n⚠️  Step 4: Risk Scoring')
    # Normalize compliance report for risk agent
    normalized_compliance = {
        'compliance_score': compliance_score,
        'overall_status': status.lower().replace(' ', '_'),
        'violations': compliance_report.get('violations', []),
        'warnings': compliance_report.get('warnings', []),
        'relevant_executive_orders': compliance_report.get('relevant_executive_orders', []),
    }
    risk_report = risk_agent.calculate_risk_score(
        normalized_compliance,
        summary,
        metadata
    )
    risk_score = risk_report['overall_score']
    risk_level = risk_report['risk_level']
    print(f'   ✅ Risk: {risk_score:.1f}% ({risk_level.upper()})')
    
    # Step 5: Email Notification
    print('\n📧 Step 5: Email Notification')
    requires_notification = risk_report['requires_notification']
    if requires_notification:
        _email_data = email_agent.prepare_email(
            risk_report,
            normalized_compliance,
            summary,
            metadata
        )
        print('   ⚠️  Would send email (disabled for test)')
    else:
        print('   ℹ️  No notification required')
    
    # Summary
    print('\n' + '=' * 80)
    print('WORKFLOW SUMMARY')
    print('=' * 80)
    print('\n✅ All 5 steps completed successfully!')
    print(f'\nDocument: {metadata.get("file_name", "Unknown")}')
    print(f'Compliance Score: {compliance_score:.1f}%')
    print(f'Risk Score: {risk_score:.1f}%')
    print(f'Risk Level: {risk_level.upper()}')
    print(f'Notification Required: {"Yes" if requires_notification else "No"}')
    
    # Confidence score check
    if 'confidence_score' in compliance_report:
        print(f'Confidence: {compliance_report["confidence_score"]:.1f}%')
    
    print('\n✅ Workflow test completed successfully!')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print(f'\n❌ Workflow failed: {str(e)}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
