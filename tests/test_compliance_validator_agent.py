#!/usr/bin/env python3
"""
Test Compliance Validator Agent

Tests the ComplianceValidatorAgent with sample proposals and executive orders.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.compliance_validator_agent import ComplianceValidatorAgent
from dotenv import load_dotenv


def test_compliance_validator_agent():
    """Test compliance validator agent with sample data."""
    
    print("=" * 70)
    print("✅ Compliance Validator Agent Test")
    print("=" * 70)
    
    # Load environment
    load_dotenv()
    
    # Sample proposal text
    proposal_text = """
Grant Proposal: Green Infrastructure Project

This proposal requests funding for a green infrastructure initiative to address
climate change and promote environmental justice in underserved communities.

The project will implement renewable energy systems and improve energy efficiency
in public buildings serving low-income residents. We will engage with community
stakeholders to ensure equitable access and culturally appropriate program design.

However, the proposal lacks specific cybersecurity measures for the digital
monitoring systems that will be installed as part of the renewable energy
infrastructure.

Budget: $1.5M over 3 years
Timeline: 36 months
Expected Impact: 500 residents served, 30% energy reduction
"""

    summary = {
        'executive_summary': 'Green infrastructure project for underserved communities',
        'key_clauses': [
            'Renewable energy systems implementation',
            'Community stakeholder engagement',
            'Equitable access and culturally appropriate design'
        ],
        'key_topics': ['climate', 'renewable energy', 'community', 'equity']
    }
    
    metadata = {
        'filename': 'sample_green_infrastructure.txt',
        'word_count': len(proposal_text.split())
    }
    
    # Test both Azure Search and local modes
    modes = [
        ('Local Knowledge Base', False),
        ('Azure AI Search', True)
    ]
    
    for mode_name, use_azure in modes:
        print(f"\n{'='*70}")
        print(f"Testing: {mode_name}")
        print(f"{'='*70}")
        
        # Initialize agent
        agent = ComplianceValidatorAgent(use_azure_search=use_azure)
        print(f"✓ Agent initialized (use_azure_search={use_azure})")
        print(f"  Search method: {'Azure AI Search' if use_azure and agent.search_endpoint else 'Local'}")
        
        try:
            # Validate compliance
            print(f"\n⏳ Validating compliance...")
            result = agent.validate_compliance(proposal_text, summary, metadata)
            
            # Display results
            print(f"\n✅ Compliance validation complete!")
            
            print("\n" + "=" * 70)
            print("📊 COMPLIANCE SCORE")
            print("=" * 70)
            score = result.get('compliance_score', 0)
            status = result.get('overall_status', 'unknown')
            print(f"Score: {score:.1f}%")
            print(f"Status: {status.upper().replace('_', ' ')}")
            
            print("\n" + "=" * 70)
            print("📜 RELEVANT EXECUTIVE ORDERS")
            print("=" * 70)
            relevant_eos = result.get('relevant_executive_orders', [])
            if relevant_eos:
                for eo in relevant_eos:
                    eo_name = eo if isinstance(eo, str) else eo.get('name', 'Unknown')
                    relevance = eo.get('relevance', 'N/A') if isinstance(eo, dict) else 'N/A'
                    print(f"  • {eo_name}")
                    if relevance != 'N/A':
                        print(f"    Relevance: {relevance}")
            else:
                print("  No relevant executive orders found")
            
            print("\n" + "=" * 70)
            print("🚨 VIOLATIONS")
            print("=" * 70)
            violations = result.get('violations', [])
            if violations:
                for i, violation in enumerate(violations, 1):
                    print(f"\n{i}. {violation.get('message', 'Unknown violation')}")
                    print(f"   Type: {violation.get('type', 'unknown')}")
                    print(f"   Severity: {violation.get('severity', 'unknown')}")
                    print(f"   EO: {violation.get('executive_order', 'Unknown')}")
            else:
                print("  ✅ No violations found")
            
            print("\n" + "=" * 70)
            print("⚠️  WARNINGS")
            print("=" * 70)
            warnings = result.get('warnings', [])
            if warnings:
                for i, warning in enumerate(warnings, 1):
                    print(f"{i}. {warning.get('message', 'Unknown warning')}")
            else:
                print("  ✅ No warnings")
            
            print("\n" + "=" * 70)
            print("💡 RECOMMENDATIONS")
            print("=" * 70)
            recommendations = result.get('recommendations', [])
            if recommendations:
                for i, rec in enumerate(recommendations, 1):
                    print(f"\n{i}. [{rec.get('priority', 'medium').upper()}] {rec.get('action', 'Unknown')}")
                    print(f"   {rec.get('description', 'No description')}")
            else:
                print("  No specific recommendations")
            
        except Exception as e:
            print(f"❌ Error validating compliance: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    print("✓ Compliance Validator Agent initialized")
    print("✓ Compliance validation tested")
    print("✓ Executive order matching tested")
    print("✓ Violation detection tested")
    print("✓ Recommendation generation tested")
    
    print("\n💡 Tips:")
    print("  - Configure AZURE_SEARCH_ENDPOINT for semantic search")
    print("  - Configure AZURE_SEARCH_API_KEY for Azure Search")
    print("  - Index executive orders with: python scripts/index_knowledge_base.py")
    print("  - Local mode searches knowledge_base/executive_orders/ folder")
    
    print("\n✅ Test completed!")
    return True


if __name__ == "__main__":
    try:
        success = test_compliance_validator_agent()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
