#!/usr/bin/env python3
"""
End-to-End Test Script for Foundry Agents

Tests the Azure AI Foundry Agent Service implementations:
  - SummarizationAgentFoundry
  - ComplianceAgentFoundry
  - SequentialWorkflowOrchestratorFoundry

Requires AGENT_SERVICE=foundry and valid Azure AI Foundry environment variables.
"""

import asyncio
import logging
import os
import sys
import traceback
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from dotenv import load_dotenv

from agents.summarization_agent_foundry import SummarizationAgentFoundry
from agents.compliance_agent_foundry import ComplianceAgentFoundry
from agents.sequential_workflow_orchestrator_foundry import SequentialWorkflowOrchestratorFoundry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sample proposal texts for testing
# ---------------------------------------------------------------------------

SAMPLE_PROPOSAL_STANDARD = """
Grant Proposal: Highway Bridge Repair and Maintenance

Requesting Department: Public Works
Requested Amount: $5,000,000
Timeline: 18 months

Purpose: Repair and upgrade 12 highway bridges that have been identified
as structurally deficient. All work will follow federal safety standards
and environmental guidelines. Project includes accessibility improvements
to comply with ADA requirements.

Budget:
- Bridge structural repairs: $3,000,000
- Safety upgrades: $1,000,000
- Accessibility improvements: $500,000
- Project management: $300,000
- Environmental compliance: $200,000

Expected Outcomes:
- Improved public safety
- Enhanced infrastructure resilience
- Job creation in local construction sector
- Compliance with federal bridge safety standards
"""

SAMPLE_PROPOSAL_DEI = """
Grant Proposal: Equitable Affordable Housing Program

Requesting Department: Housing and Community Development
Requested Amount: $3,500,000
Timeline: 24 months

Purpose: Develop 200 units of affordable housing with focus on advancing
racial equity and environmental justice. The project will prioritize
historically underserved communities and include diversity, equity, and
inclusion training for all contractors and staff.

Key Features:
- Preference for minority-owned businesses
- DEI compliance training required
- Focus on communities disproportionately affected by climate change
- Gender-neutral facilities and inclusive design principles

Compliance Requirements:
This project addresses Executive Order 13985 on Advancing Racial Equity
and EO 14008 on Tackling the Climate Crisis. Comprehensive equity analysis
per EO 13985 requirements included.

Expected Outcomes:
- Increased housing access for marginalized communities
- Advancement of equity goals
- Environmental justice improvements
"""

SAMPLE_PROPOSAL_IMMIGRATION = """
Grant Proposal: Comprehensive Immigration Assistance Program

Requesting Department: Social Services
Requested Amount: $2,000,000
Timeline: 12 months

Purpose: Establish services to assist undocumented immigrants with
citizenship applications, legal representation, and integration support.
Program will provide translation services in 15+ languages and connect
migrants with community resources.

Services Include:
- Legal aid for asylum seekers
- Support for undocumented families
- Sanctuary city coordination
- Immigration status navigation assistance

Expected Outcomes:
- Increased immigrant community support
- Enhanced access to government services regardless of immigration status
- Protection for vulnerable populations
"""

# ---------------------------------------------------------------------------
# Environment setup helpers
# ---------------------------------------------------------------------------

REQUIRED_ENV_VARS = {
    'project_endpoint': ['AZURE_AI_PROJECT_ENDPOINT', 'AZURE_AI_FOUNDRY_PROJECT_ENDPOINT'],
    'deployment_name': ['AZURE_AI_MODEL_DEPLOYMENT_NAME', 'AZURE_OPENAI_DEPLOYMENT_NAME'],
    'search_index': ['AZURE_SEARCH_INDEX_NAME'],
    'search_connection_id': ['AI_SEARCH_PROJECT_CONNECTION_ID'],
}


def get_env(keys: list, default: str = '') -> str:
    """Return the first non-empty env var from *keys*, or *default*."""
    for key in keys:
        val = os.getenv(key)
        if val:
            return val
    return default


def check_environment() -> dict:
    """
    Verify required environment variables and return a config dict.

    Returns:
        dict with resolved config values

    Raises:
        SystemExit if required vars are missing
    """
    config = {}
    missing = []
    for name, keys in REQUIRED_ENV_VARS.items():
        val = get_env(keys)
        if not val and name not in ('search_index',):  # search_index has a default
            missing.append(' or '.join(keys))
        config[name] = val
    # Apply defaults
    config.setdefault('search_index', config.get('search_index') or 'grant-compliance-index')
    config['search_query_type'] = os.getenv('AI_SEARCH_QUERY_TYPE', 'simple')

    if missing:
        print("\n❌ Missing required environment variables:")
        for m in missing:
            print(f"   - {m}")
        print("\nPlease configure these in your .env file.")
        sys.exit(1)
    return config


def print_header(title: str, char: str = '=', width: int = 70):
    print(f"\n{char * width}")
    print(f"  {title}")
    print(f"{char * width}")


# ---------------------------------------------------------------------------
# Individual Agent Tests
# ---------------------------------------------------------------------------

async def test_summarization_agent(config: dict) -> bool:
    """Test SummarizationAgentFoundry with a sample proposal."""
    print_header("TEST 1: SummarizationAgentFoundry")

    agent = SummarizationAgentFoundry(
        project_endpoint=config['project_endpoint'],
        model_deployment_name=config['deployment_name'],
    )
    print("  ✅ Agent initialized")
    print(f"     Endpoint : {config['project_endpoint'][:60]}...")
    print(f"     Model    : {config['deployment_name']}")

    metadata = {
        'word_count': len(SAMPLE_PROPOSAL_DEI.split()),
        'page_count': 1,
        'filename': 'test_equitable_housing_proposal.txt',
    }

    print(f"\n  ⏳ Generating summary ({metadata['word_count']} words)...")
    result = await agent.generate_summary(SAMPLE_PROPOSAL_DEI, metadata)

    # Validate structure
    assert isinstance(result, dict), "Result should be a dict"
    expected_keys = ['executive_summary', 'key_clauses', 'key_topics', 'summary_length', 'metadata']
    for key in expected_keys:
        assert key in result, f"Missing expected key: {key}"

    print(f"\n  📋 Executive Summary:\n     {result['executive_summary'][:300]}...")
    print(f"\n  🔑 Key Clauses ({len(result.get('key_clauses', []))}):")
    for i, clause in enumerate(result.get('key_clauses', [])[:5], 1):
        print(f"     {i}. {clause[:120]}{'...' if len(clause) > 120 else ''}")
    print(f"\n  🏷️  Key Topics: {', '.join(result.get('key_topics', []))}")
    print(f"  📊 Summary length: {result.get('summary_length', 0)} words")
    print(f"  🔧 Method: {result.get('metadata', {}).get('summary_method', 'unknown')}")

    print("\n  ✅ SummarizationAgentFoundry test PASSED")
    return True


async def test_compliance_agent(config: dict) -> bool:
    """Test ComplianceAgentFoundry with multiple proposal scenarios."""
    print_header("TEST 2: ComplianceAgentFoundry")

    agent = ComplianceAgentFoundry(
        project_endpoint=config['project_endpoint'],
        model_deployment_name=config['deployment_name'],
        search_index_name=config['search_index'],
        search_connection_id=config['search_connection_id'],
        search_query_type=config['search_query_type'],
    )
    print("  ✅ Agent initialized")
    print(f"     Search Index : {config['search_index']}")
    print(f"     Query Type   : {config['search_query_type']}")

    scenarios = [
        ('Standard Infrastructure Grant', SAMPLE_PROPOSAL_STANDARD),
        ('DEI / Climate Components', SAMPLE_PROPOSAL_DEI),
        ('Immigration Services', SAMPLE_PROPOSAL_IMMIGRATION),
    ]

    for idx, (name, proposal) in enumerate(scenarios, 1):
        print(f"\n  📋 Scenario {idx}: {name}")
        print(f"  {'-' * 60}")

        result = await agent.analyze_proposal(
            proposal,
            context={'scenario': name},
        )

        # Validate structure
        assert isinstance(result, dict), "Result should be a dict"
        for key in ['analysis', 'confidence_score', 'status', 'overall_status']:
            assert key in result, f"Missing expected key: {key}"

        status = result['status']
        confidence = result['confidence_score']
        eos = result.get('relevant_executive_orders', [])
        citations = result.get('citations', [])

        emoji = '✅' if status == 'Compliant' else ('❌' if status == 'Non-Compliant' else '⚠️')
        print(f"     {emoji} Status     : {status}")
        print(f"     🎯 Confidence : {confidence}%")
        print(f"     📜 Relevant EOs: {len(eos)}")
        for eo in eos[:3]:
            eo_label = eo.get('name', eo.get('eo_number', 'Unknown'))
            print(f"        - {eo_label}: {eo.get('title', '')[:80]}")
        print(f"     📎 Citations   : {len(citations)}")
        print(f"     📝 Analysis    : {result['analysis'][:200]}...")

    print(f"\n  ✅ ComplianceAgentFoundry test PASSED ({len(scenarios)} scenarios)")
    return True


async def test_sequential_workflow_orchestrator(config: dict) -> bool:
    """Test SequentialWorkflowOrchestratorFoundry end-to-end with a file."""
    print_header("TEST 3: SequentialWorkflowOrchestratorFoundry (E2E)")

    orchestrator = SequentialWorkflowOrchestratorFoundry(
        use_azure=True,
        send_email=False,
    )
    print("  ✅ Orchestrator initialized")

    # Locate a test document (prefer txt for speed, fall back to PDF)
    test_doc = Path(__file__).parent / 'test_document.txt'
    if not test_doc.exists():
        sample_dir = Path(__file__).parent.parent / 'knowledge_base' / 'sample_proposals'
        candidates = list(sample_dir.glob('*.txt')) + list(sample_dir.glob('*.pdf'))
        if candidates:
            test_doc = candidates[0]
        else:
            print("  ❌ No test document found")
            return False

    print(f"  📄 Test document: {test_doc.name}")

    # --- Async workflow ---
    print("\n  ⏳ Running async workflow...")
    results = await orchestrator.process_grant_proposal_async(str(test_doc))

    # Validate top-level structure
    assert results['status'] == 'completed', f"Workflow status should be 'completed', got '{results['status']}'"
    assert results['service'] == 'foundry_agent_service'
    for step in ['ingestion', 'summarization', 'compliance', 'risk_scoring', 'notification']:
        assert step in results['steps'], f"Missing step: {step}"

    # Print step statuses
    print(f"\n  {'─' * 60}")
    print("  WORKFLOW STEPS")
    print(f"  {'─' * 60}")
    for step_name, step_data in results['steps'].items():
        status_emoji = '✅' if step_data['status'] == 'completed' else ('⏭️' if step_data['status'] == 'skipped' else '❌')
        print(f"     {status_emoji} {step_name}: {step_data['status']}")

    # Metadata
    metadata = results.get('metadata', {})
    print(f"\n  📄 Document : {metadata.get('file_name', 'Unknown')}")
    print(f"     Words   : {metadata.get('word_count', 0)}")

    # Summary
    summary = results.get('summary', {})
    print(f"\n  📋 Summary  : {summary.get('executive_summary', '')[:200]}...")
    print(f"     Clauses  : {len(summary.get('key_clauses', []))}")
    print(f"     Topics   : {', '.join(summary.get('key_topics', []))}")

    # Compliance
    compliance = results.get('compliance_report', {})
    print(f"\n  ⚖️  Compliance Score  : {compliance.get('compliance_score', 0):.1f}%")
    print(f"     Status            : {compliance.get('overall_status', 'unknown')}")
    print(f"     Confidence        : {compliance.get('confidence_score', 0)}%")
    print(f"     Relevant EOs      : {len(compliance.get('relevant_executive_orders', []))}")
    print(f"     Violations        : {len(compliance.get('violations', []))}")
    print(f"     Warnings          : {len(compliance.get('warnings', []))}")

    # Risk
    risk = results.get('risk_report', {})
    print(f"\n  🎲 Risk Score : {risk.get('overall_score', 0):.1f}%")
    print(f"     Level     : {risk.get('risk_level', 'unknown')}")
    print(f"     Notify    : {risk.get('requires_notification', False)}")

    # Overall
    print(f"\n  🏁 Overall Status : {results.get('overall_status', 'unknown')}")
    print(f"     Email Sent     : {results.get('email_sent', False)}")

    # Print the formatted summary
    print(f"\n{orchestrator.get_workflow_summary(results)}")

    # --- Sync wrapper ---
    print("\n  ⏳ Running sync wrapper...")
    sync_results = orchestrator.process_grant_proposal(str(test_doc))
    assert sync_results['status'] == 'completed', f"Sync workflow failed: {sync_results.get('error', 'unknown')}"
    print(f"  ✅ Sync wrapper returned status: {sync_results['status']}")

    print("\n  ✅ SequentialWorkflowOrchestratorFoundry test PASSED")
    return True


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

async def run_all_tests():
    """Run all Foundry agent tests and report results."""
    load_dotenv()
    config = check_environment()

    print_header("FOUNDRY AGENT END-TO-END TEST SUITE", '=', 70)
    print(f"  Endpoint  : {config['project_endpoint'][:60]}...")
    print(f"  Model     : {config['deployment_name']}")
    print(f"  Index     : {config['search_index']}")

    tests = [
        ('SummarizationAgentFoundry', test_summarization_agent),
        ('ComplianceAgentFoundry', test_compliance_agent),
        ('SequentialWorkflowOrchestratorFoundry', test_sequential_workflow_orchestrator),
    ]

    results = {}

    for name, test_fn in tests:
        try:
            passed = await test_fn(config)
            results[name] = 'PASSED' if passed else 'FAILED'
        except Exception as e:
            logger.error(f"{name} failed: {e}")
            traceback.print_exc()
            results[name] = f'FAILED: {e}'

    # Summary
    print_header("TEST RESULTS SUMMARY", '=', 70)
    all_passed = True
    for name, status in results.items():
        emoji = '✅' if status == 'PASSED' else '❌'
        print(f"  {emoji} {name}: {status}")
        if status != 'PASSED':
            all_passed = False

    passed_count = sum(1 for s in results.values() if s == 'PASSED')
    total = len(results)
    print(f"\n  {passed_count}/{total} tests passed")

    if all_passed:
        print("\n  🎉 All Foundry agent tests passed!")
    else:
        print("\n  ⚠️  Some tests failed. Check logs above for details.")

    return all_passed


if __name__ == '__main__':
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest run interrupted.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
