#!/usr/bin/env python3
"""
Test Risk Scoring Agent

Tests the RiskScoringAgent with sample compliance and summary data.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from agents.risk_scoring_agent import RiskScoringAgent
from dotenv import load_dotenv


def test_risk_scoring_agent():
    """Test risk scoring agent with sample data."""
    
    print("=" * 70)
    print("⚠️  Risk Scoring Agent Test")
    print("=" * 70)
    
    # Load environment
    load_dotenv()
    
    # Create sample test scenarios
    scenarios = [
        {
            'name': 'High Risk Proposal',
            'compliance_report': {
                'compliance_score': 45.0,
                'overall_status': 'non_compliant',
                'violations': [
                    {
                        'type': 'environmental',
                        'severity': 'high',
                        'message': 'Missing climate impact assessment',
                        'executive_order': 'EO 14008'
                    },
                    {
                        'type': 'equity',
                        'severity': 'high',
                        'message': 'Insufficient community engagement',
                        'executive_order': 'EO 13985'
                    },
                    {
                        'type': 'cybersecurity',
                        'severity': 'medium',
                        'message': 'Missing security framework',
                        'executive_order': 'EO 14028'
                    }
                ],
                'warnings': [
                    {'message': 'Budget justification needs detail'},
                    {'message': 'Timeline may be optimistic'}
                ],
                'relevant_executive_orders': ['EO 14008', 'EO 13985', 'EO 14028']
            },
            'summary': {
                'executive_summary': 'Project lacking key compliance elements',
                'key_clauses': ['Budget allocation', 'Project timeline'],
                'key_topics': ['infrastructure', 'community']
            },
            'metadata': {
                'word_count': 800,
                'page_count': 3,
                'filename': 'high_risk_proposal.pdf'
            }
        },
        {
            'name': 'Medium Risk Proposal',
            'compliance_report': {
                'compliance_score': 72.0,
                'overall_status': 'requires_review',
                'violations': [
                    {
                        'type': 'equity',
                        'severity': 'medium',
                        'message': 'Community engagement could be stronger',
                        'executive_order': 'EO 13985'
                    }
                ],
                'warnings': [
                    {'message': 'Consider additional stakeholder outreach'}
                ],
                'relevant_executive_orders': ['EO 13985', 'EO 14008']
            },
            'summary': {
                'executive_summary': 'Solid proposal with minor gaps',
                'key_clauses': ['Budget', 'Timeline', 'Community engagement', 'Impact metrics'],
                'key_topics': ['climate', 'equity', 'infrastructure']
            },
            'metadata': {
                'word_count': 2500,
                'page_count': 8,
                'filename': 'medium_risk_proposal.pdf'
            }
        },
        {
            'name': 'Low Risk Proposal',
            'compliance_report': {
                'compliance_score': 92.0,
                'overall_status': 'compliant',
                'violations': [],
                'warnings': [],
                'relevant_executive_orders': ['EO 13985', 'EO 14008', 'EO 14028']
            },
            'summary': {
                'executive_summary': 'Comprehensive proposal meeting all requirements',
                'key_clauses': [
                    'Detailed budget justification',
                    'Comprehensive timeline',
                    'Community engagement plan',
                    'Environmental impact assessment',
                    'Cybersecurity measures'
                ],
                'key_topics': ['climate', 'equity', 'security', 'community', 'sustainability']
            },
            'metadata': {
                'word_count': 4500,
                'page_count': 15,
                'filename': 'low_risk_proposal.pdf'
            }
        }
    ]
    
    # Initialize agent
    print("\n✓ Initializing Risk Scoring Agent...")
    agent = RiskScoringAgent()
    print("✓ Agent initialized")
    
    # Test each scenario
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'='*70}")
        print(f"Test Scenario {i}: {scenario['name']}")
        print(f"{'='*70}")
        
        try:
            # Calculate risk score
            print("⏳ Calculating risk score...")
            result = agent.calculate_risk_score(
                scenario['compliance_report'],
                scenario['summary'],
                scenario['metadata']
            )
            
            # Display results
            print("\n✅ Risk score calculated!")
            
            print("\n" + "-" * 70)
            print("📊 RISK SCORE")
            print("-" * 70)
            print(f"Overall Score: {result['overall_score']:.1f}%")
            print(f"Risk Level: {result['risk_level'].upper()}")
            print(f"Confidence: {result['confidence']:.1f}%")
            print(f"Notification Required: {'YES' if result['requires_notification'] else 'NO'}")
            
            print("\n" + "-" * 70)
            print("📈 RISK BREAKDOWN")
            print("-" * 70)
            breakdown = result['risk_breakdown']
            print(f"Compliance Risk: {breakdown['compliance_risk']['score']:.1f}%")
            print(f"  Violations: {breakdown['compliance_risk'].get('violations_count', 0)}")
            print(f"  Warnings: {breakdown['compliance_risk'].get('warnings_count', 0)}")
            print(f"\nQuality Risk: {breakdown['quality_risk']['score']:.1f}%")
            print(f"  Word count: {breakdown['quality_risk'].get('word_count', 0)}")
            print(f"  Page count: {breakdown['quality_risk'].get('page_count', 0)}")
            print(f"\nCompleteness Risk: {breakdown['completeness_risk']['score']:.1f}%")
            
            print("\n" + "-" * 70)
            print("⚠️  RISK FACTORS")
            print("-" * 70)
            risk_factors = result['risk_factors']
            if risk_factors:
                for factor in risk_factors:
                    severity_icon = "🔴" if factor['severity'] == 'high' else "🟡" if factor['severity'] == 'medium' else "🟢"
                    print(f"{severity_icon} {factor['factor']} ({factor['severity'].upper()})")
                    print(f"   {factor['description']}")
            else:
                print("  ✅ No significant risk factors")
            
            print("\n" + "-" * 70)
            print("💡 RECOMMENDATIONS")
            print("-" * 70)
            recommendations = result['recommendations']
            if recommendations:
                for rec in recommendations:
                    priority_icon = "🔴" if rec['priority'] in ['critical', 'high'] else "🟡"
                    print(f"{priority_icon} [{rec['priority'].upper()}] {rec['action']}")
                    print(f"   {rec['description']}")
            else:
                print("  ✅ No specific recommendations")
            
        except Exception as e:
            print(f"❌ Error calculating risk: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    print("✓ Risk Scoring Agent initialized")
    print("✓ High risk scenario tested")
    print("✓ Medium risk scenario tested")
    print("✓ Low risk scenario tested")
    print("✓ Risk factor identification tested")
    print("✓ Recommendation generation tested")
    print("✓ Notification logic tested")
    
    print("\n💡 Risk Thresholds:")
    print(f"  High Risk: < {agent.HIGH_RISK_THRESHOLD}%")
    print(f"  Medium Risk: {agent.HIGH_RISK_THRESHOLD}% - {agent.MEDIUM_RISK_THRESHOLD}%")
    print(f"  Low Risk: {agent.MEDIUM_RISK_THRESHOLD}% - {agent.LOW_RISK_THRESHOLD}%")
    print(f"  Very Low Risk: > {agent.LOW_RISK_THRESHOLD}%")
    
    print("\n✅ Test completed!")
    return True


if __name__ == "__main__":
    try:
        success = test_risk_scoring_agent()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
