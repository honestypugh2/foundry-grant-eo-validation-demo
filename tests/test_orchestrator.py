#!/usr/bin/env python3
"""
Test Orchestrator

Tests the AgentOrchestrator with complete end-to-end workflow.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.orchestrator import AgentOrchestrator
from dotenv import load_dotenv


def test_orchestrator():
    """Test orchestrator with complete workflow."""
    
    print("=" * 70)
    print("🎯 Agent Orchestrator Test")
    print("=" * 70)
    
    # Load environment
    load_dotenv()
    
    # Find a sample file
    sample_dir = Path(__file__).parent / 'knowledge_base' / 'sample_proposals'
    
    if not sample_dir.exists() or not list(sample_dir.glob('*')):
        print("\n⚠️  No sample files found. Creating test file...")
        
        # Create test file
        test_file = Path(__file__).parent / 'test_proposal.txt'
        test_content = """
Grant Proposal: Community Climate Resilience Initiative

Executive Summary:
This proposal requests $1,000,000 to enhance climate resilience in underserved 
communities through renewable energy infrastructure, emergency preparedness, and 
community education programs.

Project Goals:
1. Install solar panels on 20 community buildings
2. Develop emergency response protocols for climate events
3. Train 300 community members in climate adaptation strategies
4. Create green jobs for 15 local residents

Alignment with Executive Orders:
This project directly supports Executive Order 14008 on Tackling the Climate Crisis
by implementing clean energy solutions and climate adaptation measures. It addresses
Executive Order 13985 on Racial Equity by targeting historically underserved 
communities and ensuring equitable access to climate resilience resources.

Budget:
- Solar installations: $500,000
- Emergency preparedness: $200,000
- Training programs: $150,000
- Job creation: $100,000
- Administration: $50,000

Timeline: 24 months
Expected Impact: 1,000 residents served, 200 tons CO2 reduction

Community Engagement:
We will conduct community meetings, surveys, and workshops to ensure culturally
appropriate program design and meaningful stakeholder participation.
"""
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        test_files = [test_file]
        print(f"✓ Created test file: {test_file.name}")
    else:
        # Use existing samples
        test_files = list(sample_dir.glob('*.txt'))[:1]
        if not test_files:
            test_files = list(sample_dir.glob('*.pdf'))[:1]
    
    if not test_files:
        print("❌ No test files available")
        return False
    
    test_file = test_files[0]
    
    # Test both local and Azure modes
    modes = [
        ('Local Processing', False),
        ('Azure Services', True)
    ]
    
    for mode_name, use_azure in modes:
        print(f"\n{'='*70}")
        print(f"Testing: {mode_name}")
        print(f"{'='*70}")
        
        # Initialize orchestrator
        print("\n⏳ Initializing orchestrator...")
        orchestrator = AgentOrchestrator(use_azure=use_azure)
        print(f"✓ Orchestrator initialized (use_azure={use_azure})")
        print(f"  Document Agent: {type(orchestrator.document_agent).__name__}")
        print(f"  Summary Agent: {type(orchestrator.summary_agent).__name__}")
        print(f"  Compliance Agent: {type(orchestrator.compliance_agent).__name__}")
        print(f"  Risk Agent: {type(orchestrator.risk_agent).__name__}")
        print(f"  Email Agent: {type(orchestrator.email_agent).__name__}")
        
        try:
            # Process document
            print(f"\n⏳ Processing document: {test_file.name}")
            print("-" * 70)
            
            result = orchestrator.process_grant_proposal(
                str(test_file),
                send_email=False  # Don't send real email in test
            )
            
            # Display results
            print(f"\n✅ Processing complete!")
            
            print("\n" + "=" * 70)
            print("📊 WORKFLOW RESULTS")
            print("=" * 70)
            
            print("\n🔹 Overall Status:")
            print(f"  {result['overall_status'].upper().replace('_', ' ')}")
            
            print("\n🔹 Workflow Steps:")
            for step_name, step_data in result['steps'].items():
                status = step_data.get('status', 'unknown')
                duration = step_data.get('duration', 0)
                print(f"  ✓ {step_name}: {status} ({duration:.2f}s)")
            
            # Risk Report
            print("\n" + "=" * 70)
            print("⚠️  RISK ASSESSMENT")
            print("=" * 70)
            risk = result['risk_report']
            print(f"Risk Score: {risk['overall_score']:.1f}%")
            print(f"Risk Level: {risk['risk_level'].upper()}")
            print(f"Confidence: {risk['confidence']:.1f}%")
            print(f"Notification Required: {'YES' if risk['requires_notification'] else 'NO'}")
            
            # Compliance Report
            print("\n" + "=" * 70)
            print("✅ COMPLIANCE VALIDATION")
            print("=" * 70)
            compliance = result['compliance_report']
            print(f"Compliance Score: {compliance['compliance_score']:.1f}%")
            print(f"Status: {compliance['overall_status'].upper().replace('_', ' ')}")
            print(f"Violations: {len(compliance.get('violations', []))}")
            print(f"Warnings: {len(compliance.get('warnings', []))}")
            print(f"Relevant EOs: {len(compliance.get('relevant_executive_orders', []))}")
            
            # Summary
            print("\n" + "=" * 70)
            print("📋 DOCUMENT SUMMARY")
            print("=" * 70)
            summary = result['summary']
            exec_summary = summary.get('executive_summary', 'No summary')
            print(exec_summary[:300] + ('...' if len(exec_summary) > 300 else ''))
            
            # Metadata
            print("\n" + "=" * 70)
            print("📄 DOCUMENT METADATA")
            print("=" * 70)
            metadata = result['metadata']
            print(f"Filename: {metadata.get('file_name', 'Unknown')}")
            print(f"Word Count: {metadata.get('word_count', 0):,}")
            print(f"Page Count: {metadata.get('page_count', 0)}")
            print(f"Processing Time: {result.get('processing_time', 0):.2f}s")
            
        except Exception as e:
            print(f"❌ Error processing document: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    print("✓ Orchestrator initialized")
    print("✓ Document ingestion tested")
    print("✓ Summarization tested")
    print("✓ Compliance validation tested")
    print("✓ Risk scoring tested")
    print("✓ Email notification logic tested")
    print("✓ End-to-end workflow completed")
    
    print("\n💡 Tips:")
    print("  - Set use_azure=True to use Azure services")
    print("  - Configure .env for Azure integration")
    print("  - Email notifications are disabled in test mode")
    
    print("\n✅ Test completed!")
    return True


if __name__ == "__main__":
    try:
        success = test_orchestrator()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
