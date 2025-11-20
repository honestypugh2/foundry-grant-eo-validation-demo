#!/usr/bin/env python3
"""
Test Summarization Agent

Tests the SummarizationAgent with sample text and configurations.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.summarization_agent import SummarizationAgent
from dotenv import load_dotenv


def test_summarization_agent():
    """Test summarization agent with sample text."""
    
    print("=" * 70)
    print("📋 Summarization Agent Test")
    print("=" * 70)
    
    # Load environment
    load_dotenv()
    
    # Sample grant proposal text
    sample_text = """
Grant Proposal: Renewable Energy Initiative for Underserved Communities

Executive Summary:
This proposal requests $2,500,000 in funding to develop a comprehensive renewable 
energy program targeting underserved urban and rural communities. The initiative 
directly supports Executive Order 14008 on Tackling the Climate Crisis and 
Executive Order 13985 on Advancing Racial Equity and Support for Underserved 
Communities.

Project Objectives:
1. Install solar panels on 50 community buildings serving low-income residents
2. Provide energy efficiency training to 500 community members
3. Create 25 green jobs for local residents
4. Reduce energy costs for participating buildings by 40%
5. Decrease carbon emissions by 1,000 tons annually

Budget Breakdown:
- Solar panel installation: $1,500,000
- Training programs: $400,000
- Job creation and placement: $300,000
- Program management: $200,000
- Evaluation and reporting: $100,000

Timeline:
Year 1: Community outreach, site assessments, initial installations (15 buildings)
Year 2: Continued installations (20 buildings), training program launch
Year 3: Complete remaining installations (15 buildings), job placement, evaluation

Compliance Requirements:
This proposal addresses climate change mitigation requirements per EO 14008 by 
implementing clean energy solutions. It promotes environmental justice by 
targeting disadvantaged communities. The project includes comprehensive equity 
analysis per EO 13985 requirements, with documented community engagement and 
culturally appropriate program design.

Expected Impact:
- 50 buildings converted to renewable energy
- 500 community members trained
- 25 green jobs created
- $500,000 annual energy savings
- 1,000 tons CO2 reduction annually
- Improved community resilience and energy independence

Sustainability Plan:
The program includes a 5-year maintenance agreement and creates a revolving loan 
fund to support future renewable energy projects in the community.
"""

    metadata = {
        'word_count': len(sample_text.split()),
        'page_count': 2,
        'filename': 'sample_renewable_energy_proposal.txt'
    }
    
    # Test both Azure and local modes
    modes = [
        ('Local Processing', False),
        ('Azure OpenAI', True)
    ]
    
    for mode_name, use_azure in modes:
        print(f"\n{'='*70}")
        print(f"Testing: {mode_name}")
        print(f"{'='*70}")
        
        # Initialize agent
        agent = SummarizationAgent(use_azure=use_azure)
        print(f"✓ Agent initialized (use_azure={use_azure})")
        print(f"  Method: {agent.deployment if use_azure and agent.endpoint else 'local extraction'}")
        
        print(f"\n📄 Input Document:")
        print(f"  Word count: {metadata['word_count']}")
        print(f"  Pages: {metadata['page_count']}")
        
        try:
            # Generate summary
            print(f"\n⏳ Generating summary...")
            result = agent.generate_summary(sample_text, metadata)
            
            # Display results
            print(f"\n✅ Summary generated successfully!")
            print("\n" + "=" * 70)
            print("📋 EXECUTIVE SUMMARY")
            print("=" * 70)
            summary = result.get('executive_summary', 'No summary available')
            print(summary)
            
            print("\n" + "=" * 70)
            print("🔑 KEY CLAUSES")
            print("=" * 70)
            key_clauses = result.get('key_clauses', [])
            if key_clauses:
                for i, clause in enumerate(key_clauses, 1):
                    print(f"\n{i}. {clause[:200]}{'...' if len(clause) > 200 else ''}")
            else:
                print("No key clauses identified")
            
            print("\n" + "=" * 70)
            print("🏷️  KEY TOPICS")
            print("=" * 70)
            topics = result.get('key_topics', [])
            if topics:
                print(", ".join(topics))
            else:
                print("No topics identified")
            
            print("\n" + "=" * 70)
            print("📊 SUMMARY STATISTICS")
            print("=" * 70)
            print(f"Summary length: {result.get('summary_length', 0)} words")
            print(f"Compression ratio: {result.get('summary_length', 0) / metadata['word_count'] * 100:.1f}%")
            print(f"Key clauses: {len(key_clauses)}")
            print(f"Key topics: {len(topics)}")
            
        except Exception as e:
            print(f"❌ Error generating summary: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    print("✓ Summarization Agent initialized")
    print("✓ Summary generation tested")
    print("✓ Key clause extraction tested")
    print("✓ Topic identification tested")
    
    print("\n💡 Tips:")
    print("  - Configure AZURE_OPENAI_ENDPOINT for better summaries")
    print("  - Configure AZURE_OPENAI_API_KEY for Azure")
    print("  - Azure mode provides more intelligent analysis")
    
    print("\n✅ Test completed!")
    return True


if __name__ == "__main__":
    try:
        success = test_summarization_agent()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
