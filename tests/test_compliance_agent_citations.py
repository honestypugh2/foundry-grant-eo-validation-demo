"""
Test Script for Compliance Agent Citations and Knowledge Base Verification

This test verifies:
1. CitationAnnotation functionality in ComplianceAgent responses
2. Knowledge base search returns relevant executive orders
3. Executive orders are properly matched to grant proposal content
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.compliance_agent import ComplianceAgent


async def test_knowledge_base_search(agent: ComplianceAgent):
    """Test direct knowledge base search to verify relevant executive orders are returned."""
    print("\n" + "=" * 80)
    print("TEST 1: Knowledge Base Search - Verify Relevant Executive Orders")
    print("=" * 80)
    
    test_queries = [
        {
            "query": "diversity equity inclusion DEI programs",
            "description": "DEI-related executive orders"
        },
        {
            "query": "climate change green energy environmental sustainability",
            "description": "Environmental/climate executive orders"
        },
        {
            "query": "immigration border security citizenship requirements",
            "description": "Immigration-related executive orders"
        },
        {
            "query": "gender ideology transgender bathroom facilities",
            "description": "Gender-related executive orders"
        }
    ]
    
    for test in test_queries:
        print(f"\n📋 Query: {test['description']}")
        print(f"   Search terms: {test['query']}")
        print("-" * 80)
        
        try:
            # Call the search tool directly
            results = await agent.search_knowledge_base(test['query'])
            
            # Parse and display results
            if "No relevant executive orders found" in results:
                print("   ⚠️  No executive orders found")
            elif "Error searching" in results:
                print(f"   ❌ Error: {results}")
            else:
                # Count documents in results
                import re
                doc_count = results.count("--- Document")
                print(f"   ✅ Found {doc_count} relevant document(s)")
                
                # Extract executive order numbers
                eo_numbers = re.findall(r'Executive Order Number: ([^\n]+)', results)
                if eo_numbers:
                    print(f"   📄 Executive Order Numbers: {', '.join(eo_numbers)}")
                
                # Show first 500 characters of results
                print("\n   Preview of search results:")
                print("   " + "-" * 76)
                preview = results[:800].replace('\n', '\n   ')
                print(f"   {preview}")
                if len(results) > 800:
                    print("   [...more content...]")
                print("   " + "-" * 76)
                
        except Exception as e:
            print(f"   ❌ Search failed: {str(e)}")
            import traceback
            traceback.print_exc()


async def test_proposal_analysis_with_citations(agent: ComplianceAgent):
    """Test full proposal analysis to verify citations are included in output."""
    print("\n" + "=" * 80)
    print("TEST 2: Grant Proposal Analysis - Verify Citations in Output")
    print("=" * 80)
    
    test_proposals = [
        {
            "name": "DEI Training Program",
            "proposal": """
Grant Application for Diversity, Equity, and Inclusion Training

Requesting Department: Human Resources
Project: Comprehensive DEI Training Initiative
Requested Amount: $500,000
Timeline: 12 months

Purpose: Develop and implement organization-wide diversity, equity, and 
inclusion training programs. This initiative will include unconscious bias 
training, cultural competency workshops, and diversity recruitment strategies.

Key Components:
- Mandatory DEI training for all employees
- Creation of diversity hiring quotas
- Establishment of employee resource groups based on identity
- Review of organizational policies through an equity lens
- Annual diversity audits and reporting

Expected Outcomes:
- Increased workplace diversity
- More equitable hiring practices
- Enhanced cultural awareness
- Improved representation across all levels
""",
            "expected_issues": ["DEI programs may conflict with recent executive orders"]
        },
        {
            "name": "Green Energy Grant",
            "proposal": """
Grant Application for Renewable Energy Infrastructure

Requesting Department: Public Utilities
Project: Solar Panel Installation on Government Buildings
Requested Amount: $3,000,000
Timeline: 24 months

Purpose: Install solar panels on 50 government buildings to reduce carbon 
footprint and promote climate action. This project aligns with the green 
new deal initiatives and supports environmental justice goals.

Key Components:
- Solar panel installation on government facilities
- Energy efficiency upgrades
- Climate change mitigation measures
- Green jobs creation
- Carbon neutrality targets

Expected Outcomes:
- Reduced greenhouse gas emissions
- Lower energy costs
- Leadership in climate action
- Support for environmental justice communities
""",
            "expected_issues": ["Climate/green energy initiatives may be affected by executive orders"]
        },
        {
            "name": "Immigration Support Services",
            "proposal": """
Grant Application for Immigrant Community Services

Requesting Department: Social Services
Project: Comprehensive Immigration Support Program
Requested Amount: $750,000
Timeline: 18 months

Purpose: Provide comprehensive support services to immigrant communities 
regardless of immigration status. Services include legal aid, housing 
assistance, and access to government benefits.

Key Components:
- Legal representation for undocumented immigrants
- Sanctuary city coordination and support
- Immigration status navigation assistance
- Access to benefits regardless of citizenship status
- Community outreach to undocumented populations

Expected Outcomes:
- Enhanced immigrant community support
- Increased access to services
- Protection for vulnerable populations
- Sanctuary city implementation
""",
            "expected_issues": ["Immigration policies may conflict with executive orders"]
        }
    ]
    
    for idx, scenario in enumerate(test_proposals, 1):
        print(f"\n📋 Test {idx}: {scenario['name']}")
        print("=" * 80)
        
        try:
            # Analyze proposal
            print("   🔍 Analyzing proposal for compliance...")
            result = await agent.analyze_proposal(
                scenario['proposal'],
                context={
                    'scenario': scenario['name'],
                    'metadata': {
                        'file_name': f"{scenario['name'].replace(' ', '_')}.pdf",
                        'page_count': 5,
                        'word_count': len(scenario['proposal'].split())
                    },
                    'summary': {
                        'executive_summary': scenario['proposal'][:200] + "...",
                        'key_topics': ['compliance', 'grant', 'funding']
                    }
                }
            )
            
            # Display results
            print("\n   📊 Results:")
            print(f"   Status: {result['status']}")
            print(f"   Confidence Score: {result['confidence_score']}%")
            
            # Check for citations in the analysis
            analysis_text = result['analysis']
            
            print("\n   📝 Analysis Output:")
            print("   " + "-" * 76)
            # Display analysis in chunks
            lines = analysis_text.split('\n')
            for line in lines[:30]:  # Show first 30 lines
                print(f"   {line}")
            if len(lines) > 30:
                print(f"   ... ({len(lines) - 30} more lines)")
            print("   " + "-" * 76)
            
            # Verify executive orders are referenced
            print("\n   🔍 Verification Checks:")
            
            has_executive_orders = any([
                "executive order" in analysis_text.lower(),
                "e.o." in analysis_text.lower(),
                "executive order number" in analysis_text.lower()
            ])
            
            has_specific_eo_numbers = bool(
                __import__('re').findall(r'(?:Executive Order|E\.O\.|EO)\s*#?\s*\d+', analysis_text, __import__('re').IGNORECASE)
            )
            
            has_citations = any([
                "relevant executive orders:" in analysis_text.lower(),
                "cited:" in analysis_text.lower(),
                "reference:" in analysis_text.lower(),
                "document" in analysis_text.lower() and "---" in analysis_text
            ])
            
            has_compliance_issues = any([
                issue_text.lower() in analysis_text.lower() 
                for issue_text in scenario['expected_issues']
            ])
            
            print(f"   {'✅' if has_executive_orders else '❌'} References Executive Orders: {has_executive_orders}")
            print(f"   {'✅' if has_specific_eo_numbers else '⚠️ '} Includes Specific EO Numbers: {has_specific_eo_numbers}")
            print(f"   {'✅' if has_citations else '⚠️ '} Contains Citations: {has_citations}")
            print(f"   {'✅' if has_compliance_issues else '⚠️ '} Identifies Expected Issues: {has_compliance_issues}")
            
            # Extract specific executive order references
            import re
            eo_refs = re.findall(
                r'(?:Executive Order|E\.O\.|EO)\s*#?\s*(\d+(?:-\d+)?)',
                analysis_text,
                re.IGNORECASE
            )
            if eo_refs:
                print(f"   📋 Referenced EO Numbers: {', '.join(set(eo_refs))}")
            
            # Overall assessment
            all_checks = [has_executive_orders, has_citations]
            passed_checks = sum(all_checks)
            
            if passed_checks == len(all_checks):
                emoji = "✅"
                status_msg = "All verification checks passed"
            elif passed_checks > 0:
                emoji = "⚠️"
                status_msg = f"{passed_checks}/{len(all_checks)} verification checks passed"
            else:
                emoji = "❌"
                status_msg = "Verification checks failed"
            
            print(f"\n   {emoji} {status_msg}")
            
        except Exception as e:
            print(f"   ❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()


async def test_citation_structure(agent: ComplianceAgent):
    """Test the citation creation method directly."""
    print("\n" + "=" * 80)
    print("TEST 3: Citation Structure - Verify CitationAnnotation Format")
    print("=" * 80)
    
    # Test citation creation with sample data
    print("\n   Creating sample citation...")
    
    try:
        sample_doc_info = {
            'title': 'Executive Order on Ending Illegal Discrimination',
            'file_path': '/knowledge_base/executive_orders/eo_14151.pdf',
            'page_number': 3,
            'id': 'eo-14151',
            'exec_order_number': '14151',
            'date': '2025-01-20'
        }
        
        sample_text = "All agencies shall terminate DEI programs and offices"
        
        citation = agent.create_citation_for_document(
            doc_info=sample_doc_info,
            text_snippet=sample_text,
            start_index=100,
            end_index=100 + len(sample_text)
        )
        
        print("   ✅ Citation created successfully")
        print("\n   Citation Details:")
        print(f"   Title: {citation.title}")
        print(f"   URL: {citation.url}")
        print(f"   Tool: {citation.tool_name}")
        print(f"   Snippet: {citation.snippet}")
        print(f"   File ID: {citation.file_id}")
        
        if hasattr(citation, 'additional_properties') and citation.additional_properties:
            print("   Additional Properties:")
            for key, value in citation.additional_properties.items():
                print(f"      - {key}: {value}")
        
        if hasattr(citation, 'annotated_regions') and citation.annotated_regions:
            print(f"   Text Regions: {len(citation.annotated_regions)} region(s)")
            for region in citation.annotated_regions:
                print(f"      - Start: {region.start_index}, End: {region.end_index}")
        
        print("\n   ✅ Citation structure is properly formatted")
        
    except Exception as e:
        print(f"   ❌ Citation creation failed: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all verification tests."""
    print("=" * 80)
    print("COMPLIANCE AGENT CITATION & KNOWLEDGE BASE VERIFICATION")
    print("=" * 80)
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = {
        'project_endpoint': ('AZURE_AI_FOUNDRY_PROJECT_ENDPOINT', 'AZURE_AI_PROJECT_ENDPOINT'),
        'deployment_name': ('AZURE_OPENAI_DEPLOYMENT_NAME', 'AZURE_OPENAI_DEPLOYMENT'),
        'search_endpoint': 'AZURE_SEARCH_ENDPOINT',
        'search_index': ('AZURE_SEARCH_INDEX_NAME', 'AZURE_SEARCH_INDEX')
    }
    
    config = {}
    missing_vars = []
    
    for key, var_names in required_vars.items():
        if isinstance(var_names, tuple):
            value = os.getenv(var_names[0]) or os.getenv(var_names[1])
            if not value:
                missing_vars.append(f"{var_names[0]} or {var_names[1]}")
        else:
            value = os.getenv(var_names)
            if not value:
                missing_vars.append(var_names)
        config[key] = value
    
    if missing_vars:
        print("\n❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease configure these in your .env file.")
        return
    
    # Initialize agent
    print("\n🚀 Initializing ComplianceAgent...")
    use_managed_identity = os.getenv('USE_MANAGED_IDENTITY', 'false').lower() == 'true'
    
    try:
        if use_managed_identity:
            print("   Authentication: Managed Identity")
            agent = ComplianceAgent(
                project_endpoint=config['project_endpoint'],
                model_deployment_name=config['deployment_name'] or 'gpt-4',
                search_endpoint=config['search_endpoint'],
                search_index_name=config['search_index'] or 'grant-compliance-index',
                azure_search_document_truncation_size=int(os.getenv('AZURE_SEARCH_DOCUMENT_CONTENT_TRUNCATION_SIZE', '2000')),
                use_managed_identity=True
            )
        else:
            print("   Authentication: API Key")
            agent = ComplianceAgent(
                project_endpoint=config['project_endpoint'],
                model_deployment_name=config['deployment_name'] or 'gpt-4',
                search_endpoint=config['search_endpoint'],
                search_index_name=config['search_index'] or 'grant-compliance-index',
                azure_search_document_truncation_size=int(os.getenv('AZURE_SEARCH_DOCUMENT_CONTENT_TRUNCATION_SIZE', '2000')),
                use_managed_identity=False,
                api_key=os.getenv('AZURE_OPENAI_API_KEY') or os.getenv('AZURE_AI_FOUNDRY_API_KEY'),
                search_api_key=os.getenv('AZURE_SEARCH_API_KEY')
            )
        print("   ✅ Agent initialized successfully\n")
        
        # Run tests
        try:
            await test_knowledge_base_search(agent)
            await test_citation_structure(agent)
            await test_proposal_analysis_with_citations(agent)
            
        finally:
            # Cleanup
            print("\n" + "=" * 80)
            print("🧹 Cleaning up resources...")
            await agent.cleanup()
            print("   ✅ Cleanup complete")
        
        print("\n" + "=" * 80)
        print("✅ ALL VERIFICATION TESTS COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Failed to initialize agent: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🔍 Starting Compliance Agent Citation & Knowledge Base Verification...\n")
    asyncio.run(main())
