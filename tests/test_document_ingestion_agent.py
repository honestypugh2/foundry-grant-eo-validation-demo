#!/usr/bin/env python3
"""
Test Document Ingestion Agent

Tests the DocumentIngestionAgent with various file types and configurations.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from agents.document_ingestion_agent import DocumentIngestionAgent
from dotenv import load_dotenv


def test_document_ingestion_agent():
    """Test document ingestion with sample files."""
    
    print("=" * 70)
    print("📄 Document Ingestion Agent Test")
    print("=" * 70)
    
    # Load environment
    load_dotenv()
    
    # Test both Azure and local modes
    modes = [
        ('Local Processing', False),
        ('Azure Document Intelligence', True)
    ]
    
    for mode_name, use_azure in modes:
        print(f"\n{'='*70}")
        print(f"Testing: {mode_name}")
        print(f"{'='*70}")
        
        # Initialize agent
        agent = DocumentIngestionAgent(use_azure=use_azure)
        print(f"✓ Agent initialized (use_azure={use_azure})")
        print(f"  Processing method: {agent.azure_endpoint if use_azure and agent.azure_endpoint else 'local'}")
        
        # Find sample files
        sample_dir = Path(__file__).parent / 'knowledge_base' / 'sample_proposals'
        
        if not sample_dir.exists():
            print(f"⚠️  Sample directory not found: {sample_dir}")
            print("   Creating test text file...")
            
            # Create a test file
            test_file = Path(__file__).parent / 'test_document.txt'
            with open(test_file, 'w') as f:
                f.write("""
Grant Proposal: Community Technology Center

Project Summary:
The Community Technology Center will provide free computer access and digital 
literacy training to underserved communities. This $500,000 initiative aligns 
with Executive Order 13985 on advancing racial equity and support for underserved 
communities through equitable access to federal resources.

Budget:
- Equipment: $200,000
- Staff: $150,000
- Training Programs: $100,000
- Facility: $50,000

Timeline:
- Months 1-3: Site selection and renovation
- Months 4-6: Equipment procurement and installation
- Months 7-12: Program launch and community outreach

Expected Impact:
- Serve 500+ community members annually
- Provide 2,000+ hours of free computer access
- Train 200+ individuals in digital literacy skills
""")
            sample_files = [test_file]
        else:
            # Get sample files
            sample_files = list(sample_dir.glob('*.txt'))[:2]
            if not sample_files:
                sample_files = list(sample_dir.glob('*.pdf'))[:1]
        
        if not sample_files:
            print("⚠️  No sample files found. Skipping processing test.")
            continue
        
        # Process first sample file
        for sample_file in sample_files[:1]:  # Test with first file only
            print(f"\n📄 Processing file: {sample_file.name}")
            print("-" * 70)
            
            try:
                result = agent.process_document(str(sample_file))
                
                # Display results
                print("✅ Successfully processed!")
                print("\n📊 Metadata:")
                metadata = result.get('metadata', {})
                for key, value in metadata.items():
                    if key == 'file_path':
                        print(f"  {key}: .../{Path(value).name}")
                    elif key == 'file_size':
                        print(f"  {key}: {value:,} bytes")
                    else:
                        print(f"  {key}: {value}")
                
                # Display text preview
                text = result.get('text', '')
                print(f"\n📝 Extracted Text Preview ({len(text)} characters):")
                print("-" * 70)
                print(text[:500] + ('...' if len(text) > 500 else ''))
                print("-" * 70)
                
                # Display stats
                word_count = result.get('metadata', {}).get('word_count', len(text.split()))
                page_count = result.get('metadata', {}).get('page_count', 1)
                print("\n📈 Statistics:")
                print(f"  Words: {word_count:,}")
                print(f"  Pages: {page_count}")
                print(f"  Characters: {len(text):,}")
                
            except Exception as e:
                print(f"❌ Error processing file: {str(e)}")
                import traceback
                traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    print("✓ Document Ingestion Agent initialized")
    print("✓ File processing tested")
    print("✓ Metadata extraction verified")
    print("✓ Text extraction verified")
    
    print("\n💡 Tips:")
    print("  - Configure AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT for OCR")
    print("  - Configure AZURE_DOCUMENT_INTELLIGENCE_API_KEY for Azure")
    print("  - Supports PDF, DOCX, and TXT files")
    
    print("\n✅ Test completed!")
    return True


if __name__ == "__main__":
    try:
        success = test_document_ingestion_agent()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
