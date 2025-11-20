"""
Quick Orchestrator Test with Fallback
Tests the workflow using ComplianceValidatorAgent instead of ComplianceAgent
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

print('=' * 80)
print('ORCHESTRATOR WORKFLOW TEST (with fallback)')
print('=' * 80)

# Load environment
load_dotenv()

# Import agents individually
from agents.document_ingestion_agent import DocumentIngestionAgent
from agents.summarization_agent import SummarizationAgent
from agents.compliance_validator_agent import ComplianceValidatorAgent  # Using old agent
from agents.risk_scoring_agent import RiskScoringAgent
from agents.email_trigger_agent import EmailTriggerAgent

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
summary_agent = SummarizationAgent(use_azure=False)
compliance_agent = ComplianceValidatorAgent(use_azure_search=False)
risk_agent = RiskScoringAgent()
email_agent = EmailTriggerAgent(use_graph_api=False)
print('   ✅ All agents initialized')

# Run workflow manually
print('\n2. Running workflow steps...')
print('-' * 80)

try:
    # Step 1: Document Ingestion
    print('\n📄 Step 1: Document Ingestion')
    document_data = doc_agent.process_document(test_file)
    metadata = doc_agent.extract_metadata(document_data)
    print(f'   ✅ Extracted {metadata.get("word_count", 0)} words, {metadata.get("page_count", 0)} pages')
    
    # Step 2: Summarization
    print('\n📋 Step 2: Summarization')
    summary = summary_agent.generate_summary(document_data['text'], metadata)
    key_clauses = len(summary.get('key_clauses', []))
    print(f'   ✅ Generated summary with {key_clauses} key clauses')
    
    # Step 3: Compliance Validation
    print('\n✅ Step 3: Compliance Validation')
    compliance_report = compliance_agent.validate_compliance(
        document_data['text'],
        summary,
        metadata
    )
    compliance_score = compliance_report['compliance_score']
    status = compliance_report['overall_status']
    print(f'   ✅ Compliance: {compliance_score:.1f}% ({status})')
    
    # Step 4: Risk Scoring
    print('\n⚠️  Step 4: Risk Scoring')
    risk_report = risk_agent.calculate_risk_score(
        compliance_report,
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
        email_data = email_agent.prepare_email(
            risk_report,
            compliance_report,
            summary,
            metadata
        )
        print(f'   ⚠️  Would send email (disabled for test)')
    else:
        print(f'   ℹ️  No notification required')
    
    # Summary
    print('\n' + '=' * 80)
    print('WORKFLOW SUMMARY')
    print('=' * 80)
    print(f'\n✅ All 5 steps completed successfully!')
    print(f'\nDocument: {metadata.get("file_name", "Unknown")}')
    print(f'Compliance Score: {compliance_score:.1f}%')
    print(f'Risk Score: {risk_score:.1f}%')
    print(f'Risk Level: {risk_level.upper()}')
    print(f'Notification Required: {"Yes" if requires_notification else "No"}')
    
    # Confidence score check
    if 'confidence_score' in compliance_report:
        print(f'Confidence: {compliance_report["confidence_score"]:.1f}%')
    
    print('\n✅ Workflow test completed successfully!')
    
except Exception as e:
    print(f'\n❌ Workflow failed: {str(e)}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
