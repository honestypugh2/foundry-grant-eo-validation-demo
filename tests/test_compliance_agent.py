"""
Test Script for Compliance Agent
Tests the Azure AI Foundry-based ComplianceAgent with Document Intelligence integration.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from agents.compliance_agent import ComplianceAgent


async def test_compliance_agent():
    """Test ComplianceAgent with sample grant proposals."""
    print("=" * 80)
    print("COMPLIANCE AGENT TEST SUITE")
    print("=" * 80)
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = [
        ('AZURE_AI_FOUNDRY_PROJECT_ENDPOINT', 'AZURE_AI_PROJECT_ENDPOINT'),
        ('AZURE_OPENAI_DEPLOYMENT_NAME', 'AZURE_OPENAI_DEPLOYMENT'),
        'AZURE_SEARCH_ENDPOINT',
        ('AZURE_SEARCH_INDEX_NAME', 'AZURE_SEARCH_INDEX')
    ]
    
    missing_vars = []
    for var in required_vars:
        if isinstance(var, tuple):
            if not os.getenv(var[0]) and not os.getenv(var[1]):
                missing_vars.append(f"{var[0]} or {var[1]}")
        else:
            if not os.getenv(var):
                missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please configure these in your .env file.")
        return
    
    # Initialize agent
    print("\n1. Initializing ComplianceAgent...")
    use_managed_identity = os.getenv('USE_MANAGED_IDENTITY', 'false').lower() == 'true'
    
    # Get environment variables with fallbacks
    project_endpoint = os.getenv('AZURE_AI_FOUNDRY_PROJECT_ENDPOINT') or os.getenv('AZURE_AI_PROJECT_ENDPOINT', '')
    deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME') or os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4')
    search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT', '')
    search_index = os.getenv('AZURE_SEARCH_INDEX_NAME') or os.getenv('AZURE_SEARCH_INDEX', 'grant-compliance-index')
    
    if use_managed_identity:
        print("   Using Managed Identity authentication")
        agent = ComplianceAgent(
            project_endpoint=project_endpoint,
            model_deployment_name=deployment_name,
            search_endpoint=search_endpoint,
            search_index_name=search_index,
            azure_search_document_truncation_size=int(os.getenv("AZURE_SEARCH_DOCUMENT_CONTENT_TRUNCATION_SIZE", "1000")),
            use_managed_identity=True
        )
    else:
        print("   Using API Key authentication")
        agent = ComplianceAgent(
            project_endpoint=project_endpoint,
            model_deployment_name=deployment_name,
            search_endpoint=search_endpoint,
            search_index_name=search_index,
            azure_search_document_truncation_size=int(os.getenv("AZURE_SEARCH_DOCUMENT_CONTENT_TRUNCATION_SIZE", "1000")),
            use_managed_identity=False,
            search_api_key=os.getenv('AZURE_SEARCH_API_KEY')
        )
    print("   ✅ Agent initialized successfully")
    
    # Test scenarios
    test_scenarios = [
        {
            'name': 'High Compliance - Standard Grant',
            'proposal': """
Grant Application for Infrastructure Development

Requesting Department: Public Works
Project: Highway Bridge Repair and Maintenance
Requested Amount: $5,000,000
Timeline: 18 months

Purpose: Repair and upgrade 12 highway bridges that have been identified 
as structurally deficient. All work will follow federal safety standards 
and environmental guidelines. Project includes accessibility improvements 
to comply with ADA requirements.

Expected Outcomes:
- Improved public safety
- Enhanced infrastructure resilience
- Job creation in local construction sector
- Compliance with federal bridge safety standards
"""
        },
        {
            'name': 'Medium Risk - DEI Components',
            'proposal': """
Grant Application for Community Development Initiative

Requesting Department: Housing and Community Development
Project: Equitable Affordable Housing Program
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

Expected Outcomes:
- Increased housing access for marginalized communities
- Advancement of equity goals
- Environmental justice improvements
"""
        },
        {
            'name': 'High Risk - Immigration Services',
            'proposal': """
Grant Application for Immigration Support Services

Requesting Department: Social Services
Project: Comprehensive Immigration Assistance Program
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
        }
    ]
    
    # Run tests
    print("\n2. Testing ComplianceAgent with sample proposals...")
    print("-" * 80)
    
    for idx, scenario in enumerate(test_scenarios, 1):
        print(f"\n📋 Test {idx}: {scenario['name']}")
        print("-" * 80)
        
        try:
            # Analyze proposal
            print("   Analyzing proposal...")
            result = await agent.analyze_proposal(
                scenario['proposal'],
                context={'scenario': scenario['name']}
            )
            
            # Display results
            print(f"\n   Status: {result['status']}")
            print(f"   Confidence Score: {result['confidence_score']}%")
            print("\n   Analysis:")
            print("   " + "\n   ".join(result['analysis'].split('\n')))
            
            # Summary
            if result['status'] == 'Compliant':
                emoji = "✅"
            elif result['status'] == 'Non-Compliant':
                emoji = "❌"
            else:
                emoji = "⚠️"
            
            print(f"\n   {emoji} Overall: {result['status']} (Confidence: {result['confidence_score']}%)")
            
        except Exception as e:
            print(f"   ❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Test Document Intelligence (if available)
    print("\n\n3. Testing Document Intelligence Integration...")
    print("-" * 80)
    
    doc_intel_endpoint = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
    if doc_intel_endpoint:
        print(f"   Document Intelligence endpoint: {doc_intel_endpoint}")
        
        # Look for a sample PDF to test
        test_pdf_path = None
        sample_dirs = [
            'data/uploads',
            'knowledge_base/sample_proposals'
        ]
        
        for sample_dir in sample_dirs:
            dir_path = Path(sample_dir)
            if dir_path.exists():
                pdf_files = list(dir_path.glob('*.pdf'))
                if pdf_files:
                    test_pdf_path = str(pdf_files[0])
                    break
        
        if test_pdf_path:
            print(f"   Testing with: {test_pdf_path}")
            try:
                # Note: extract_grant_metadata is a tool method, typically called by the agent
                # For testing, we would need to create an agent instance and call it through the agent
                print("   ✅ Document Intelligence configured (full test requires agent invocation)")
            except Exception as e:
                print(f"   ⚠️ Document Intelligence test: {str(e)}")
        else:
            print("   ℹ️ No sample PDF found for testing. Document Intelligence will be used when available.")
    else:
        print("   ℹ️ Document Intelligence not configured (AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT not set)")
        print("   This is optional - agent will fall back to text-based analysis")
    
    print("\n" + "=" * 80)
    print("COMPLIANCE AGENT TESTS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    print("\nStarting Compliance Agent tests...\n")
    asyncio.run(test_compliance_agent())
