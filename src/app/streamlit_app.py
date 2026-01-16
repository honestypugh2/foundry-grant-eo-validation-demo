"""
Grant Proposal Compliance Demo - Streamlit Application

Interactive demo for automated grant proposal compliance checking using Azure AI Foundry.
"""

import streamlit as st
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any

# Add src directory to path to import agents
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.orchestrator import AgentOrchestrator

# Page configuration
st.set_page_config(
    page_title="Grant Compliance Automation",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #0078D4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #605E5C;
        margin-bottom: 2rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid;
    }
    .status-low {
        background-color: #DFF6DD;
        border-color: #107C10;
    }
    .status-medium {
        background-color: #FFF4CE;
        border-color: #FFB900;
    }
    .status-high {
        background-color: #FDE7E9;
        border-color: #D13438;
    }
    .metric-card {
        background-color: #F3F2F1;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    .step-complete {
        color: #107C10;
    }
    .step-pending {
        color: #8A8886;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'workflow_results' not in st.session_state:
    st.session_state.workflow_results = None
if 'use_azure' not in st.session_state:
    # Check if Azure Search is configured
    import os
    from dotenv import load_dotenv
    load_dotenv()
    has_azure_search = bool(os.getenv('AZURE_SEARCH_ENDPOINT') and os.getenv('AZURE_SEARCH_API_KEY'))
    st.session_state.use_azure = has_azure_search  # Default to True if Azure Search is configured
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'agent_service' not in st.session_state:
    import os
    st.session_state.agent_service = os.getenv('AGENT_SERVICE', 'agent-framework')
if 'orchestrator_type' not in st.session_state:
    import os
    st.session_state.orchestrator_type = os.getenv('ORCHESTRATOR_TYPE', 'sequential')


def main():
    """Main application entry point."""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Sidebar configuration
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50/0078D4/FFFFFF?text=Azure+AI")
        st.title("Configuration")
        
        # Agent Service Selection
        st.subheader("Agent Service")
        agent_service = st.selectbox(
            "Select Agent Service",
            options=['agent-framework', 'foundry'],
            index=0 if st.session_state.agent_service == 'agent-framework' else 1,
            help="agent-framework: Uses Agent Framework SDK (supports Managed Identity)\nfoundry: Uses Azure AI Foundry Agent Service (requires API keys for local dev)"
        )
        st.session_state.agent_service = agent_service
        
        if agent_service == 'foundry':
            st.caption("⚠️ Foundry service requires USE_MANAGED_IDENTITY=false for local development")
            st.caption("👁️ Agents visible in Azure AI Foundry portal")
        else:
            st.caption("✓ Supports Managed Identity authentication")
            st.caption("🚀 Uses Agent Framework sequential workflows")
        
        # Orchestrator Selection
        st.subheader("Orchestrator Type")
        orchestrator_options = {
            'legacy': 'Original (Manual async)',
            'sequential': 'Sequential Workflow (Agent Framework)',
            'foundry': 'Foundry Orchestrator (azure-ai-projects)'
        }
        orchestrator_type = st.selectbox(
            "Select Orchestrator",
            options=list(orchestrator_options.keys()),
            format_func=lambda x: orchestrator_options[x],
            index=list(orchestrator_options.keys()).index(st.session_state.orchestrator_type) if st.session_state.orchestrator_type in orchestrator_options else 1,
            help="Choose which orchestrator implementation to use for processing"
        )
        st.session_state.orchestrator_type = orchestrator_type
        
        if orchestrator_type == 'legacy':
            st.caption("📌 Original orchestrator - Agent Framework only")
        elif orchestrator_type == 'sequential':
            st.caption("📌 Sequential workflow with event streaming")
        else:
            st.caption("📌 Agents created in Azure AI Foundry")
        
        st.divider()
        
        # Azure configuration
        st.subheader("Azure Services")
        use_azure = st.checkbox(
            "Use Azure Services",
            value=st.session_state.use_azure,
            help="Enable Azure AI Search, Document Intelligence, and OpenAI"
        )
        st.session_state.use_azure = use_azure
        
        if use_azure:
            # Check Azure service configuration
            import os
            azure_services = {
                "Azure OpenAI": bool(os.getenv('AZURE_OPENAI_ENDPOINT') and os.getenv('AZURE_OPENAI_API_KEY')),
                "Document Intelligence": bool(os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT') and os.getenv('AZURE_DOCUMENT_INTELLIGENCE_API_KEY')),
                "AI Search": bool(os.getenv('AZURE_SEARCH_ENDPOINT') and os.getenv('AZURE_SEARCH_API_KEY')),
                "AI Foundry": bool(os.getenv('AZURE_AI_FOUNDRY_ENDPOINT') and os.getenv('AZURE_AI_FOUNDRY_API_KEY'))
            }
            
            configured = sum(azure_services.values())
            total = len(azure_services)
            
            if configured == total:
                st.success(f"✓ All Azure services configured ({configured}/{total})")
            elif configured > 0:
                st.warning(f"⚠️ Partial Azure configuration ({configured}/{total})")
                for service, is_configured in azure_services.items():
                    icon = "✓" if is_configured else "✗"
                    color = "green" if is_configured else "red"
                    st.caption(f":{color}[{icon} {service}]")
                
                # Show info about fallback behavior
                if not azure_services.get("AI Search"):
                    st.info("💡 Local knowledge base will be used for compliance checks")
            else:
                st.error("❌ No Azure services configured")
                st.caption("Configure Azure services in .env file")
                with st.expander("📝 Configuration Help"):
                    st.markdown("""
                    **Required Environment Variables:**
                    
                    ```bash
                    # Azure OpenAI
                    AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
                    AZURE_OPENAI_API_KEY=your_api_key
                    AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
                    
                    # Document Intelligence
                    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
                    AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your_api_key
                    
                    # AI Search
                    AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
                    AZURE_SEARCH_API_KEY=your_api_key
                    AZURE_SEARCH_INDEX_NAME=grant-compliance-index
                    
                    # AI Foundry (optional)
                    AZURE_AI_FOUNDRY_ENDPOINT=https://your-foundry.services.ai.azure.com/api/projects/yourProject
                    AZURE_AI_FOUNDRY_API_KEY=your_api_key
                    ```
                    
                    Copy these to your `.env` file in the project root.
                    """)
        else:
            st.info("🎬 Running in demo mode with local processing")
        
        st.divider()
        
        # Knowledge base info
        st.subheader("Knowledge Base")
        kb_path = Path(__file__).parent.parent / 'knowledge_base'
        eo_dir = kb_path / 'sample_executive_orders'
        eo_count = len(list(eo_dir.glob('*.txt'))) + len(list(eo_dir.glob('*.pdf')))
        st.metric("Executive Orders", eo_count)
        
        # Show search method
        if use_azure:
            import os
            has_search = bool(os.getenv('AZURE_SEARCH_ENDPOINT') and os.getenv('AZURE_SEARCH_API_KEY'))
            if has_search:
                st.caption("🔍 Using Azure AI Search")
            else:
                st.caption("🔍 Using Local Search")
        else:
            st.caption("🔍 Using Local Search")
        
        st.divider()
        
        # Navigation
        st.subheader("Navigation")
        page = st.radio(
            "Go to",
            ["Upload & Analyze", "Results Dashboard", "Knowledge Base", "About"],
            label_visibility="collapsed"
        )
    
    # Main content based on selected page
    if page == "Upload & Analyze":
        show_upload_page()
    elif page == "Results Dashboard":
        show_results_page()
    elif page == "Knowledge Base":
        show_knowledge_base_page()
    else:
        show_about_page()


def show_upload_page():
    """Document upload and analysis page."""
    st.markdown('<div class="main-header">📝 Grant Proposal Upload & Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Upload a grant proposal for automated compliance review</div>', unsafe_allow_html=True)
    
    # Upload section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose a grant proposal file",
            type=['pdf', 'docx', 'txt'],
            help="Upload PDF, Word, or text document"
        )
        
        # Or select from samples
        st.markdown("### Or select a sample proposal")
        sample_dir = Path(__file__).parent.parent / 'knowledge_base' / 'sample_proposals'
        sample_files = list(sample_dir.glob('*.pdf')) + list(sample_dir.glob('*.txt'))
        sample_names = ['-- Select a sample --'] + [f.name for f in sample_files]
        
        selected_sample = st.selectbox("Sample proposals", sample_names)
    
    with col2:
        st.markdown("### Processing Options")
        send_email = st.checkbox(
            "Send email notification",
            value=True,
            help="Send email if risk threshold exceeded"
        )
        
        st.markdown("### Workflow Steps")
        st.markdown("""
        1. 📄 **Document Ingestion** - Extract text
        2. 📋 **Summarization** - Generate summary
        3. ✅ **Compliance Check** - Validate EOs
        4. ⚠️ **Risk Scoring** - Calculate risk
        5. 📧 **Email Notification** - Alert if needed
        """)
    
    # Process button
    file_to_process = None
    if uploaded_file:
        file_to_process = uploaded_file
    elif selected_sample != '-- Select a sample --':
        file_to_process = sample_dir / selected_sample
    
    if file_to_process:
        if st.button("🚀 Analyze for Compliance", type="primary"):
            process_document(file_to_process, send_email)


def process_document(file_input, send_email: bool):
    """Process uploaded document through compliance workflow."""
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Save uploaded file temporarily if needed
        if hasattr(file_input, 'read'):
            temp_path = Path('/tmp') / file_input.name
            with open(temp_path, 'wb') as f:
                f.write(file_input.read())
            file_path = str(temp_path)
        else:
            file_path = str(file_input)
        
        # Initialize orchestrator
        status_text.text("Initializing AI agents...")
        progress_bar.progress(10)
        
        orchestrator = AgentOrchestrator(use_azure=st.session_state.use_azure)
        
        # Process through orchestrator with progress updates (using async method)
        status_text.text("🚀 Processing document through compliance workflow...")
        progress_bar.progress(20)
        
        # Run async method in event loop for better async handling
        results = asyncio.run(
            orchestrator.process_grant_proposal_async(file_path, send_email=send_email)
        )
        
        # Complete
        progress_bar.progress(100)
        status_text.text("✅ Processing complete!")
        
        # Store results in session state
        st.session_state.workflow_results = results
        
        # Show success message
        status_text.empty()
        progress_bar.empty()
        
        st.success("✅ Analysis complete! View results in the Dashboard.")
        
        # Display quick summary
        display_quick_results(results)
        
    except Exception as e:
        st.error(f"❌ Error processing document: {str(e)}")
        st.exception(e)


def display_quick_results(results: Dict[str, Any]):
    """Display quick summary of results."""
    st.markdown("### Quick Results")
    
    risk_report = results['risk_report']
    compliance_report = results['compliance_report']
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        risk_score = risk_report['overall_score']
        risk_level = risk_report['risk_level']
        st.metric(
            "Risk Score",
            f"{risk_score:.1f}%",
            delta=f"{risk_level.upper()}",
            delta_color="inverse"
        )
    
    with col2:
        compliance_score = compliance_report['compliance_score']
        st.metric(
            "Compliance Score",
            f"{compliance_score:.1f}%"
        )
    
    with col3:
        violations = len(compliance_report.get('violations', []))
        st.metric("Violations", violations)
    
    with col4:
        eo_count = len(compliance_report.get('relevant_executive_orders', []))
        st.metric("Relevant EOs", eo_count)
    
    # Status box
    risk_class = "status-high" if risk_level == "high" else ("status-medium" if risk_level in ["medium", "medium-high"] else "status-low")
    st.markdown(f"""
    <div class="status-box {risk_class}">
        <h4>Overall Status: {results['overall_status'].upper().replace('_', ' ')}</h4>
        <p>{'Email notification sent to attorney' if results.get('email_sent') else 'No notification required'}</p>
    </div>
    """, unsafe_allow_html=True)


def show_results_page():
    """Results dashboard page."""
    st.markdown('<div class="main-header">📊 Compliance Results Dashboard</div>', unsafe_allow_html=True)
    
    if not st.session_state.workflow_results:
        st.info("No results yet. Please upload and analyze a document first.")
        return
    
    results = st.session_state.workflow_results
    risk_report = results['risk_report']
    compliance_report = results['compliance_report']
    summary = results['summary']
    metadata = results['metadata']
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "📋 Summary",
        "✅ Compliance",
        "⚠️ Risk Analysis",
        "📧 Email"
    ])
    
    with tab1:
        show_overview_tab(results)
    
    with tab2:
        show_summary_tab(summary, metadata)
    
    with tab3:
        show_compliance_tab(compliance_report)
    
    with tab4:
        show_risk_tab(risk_report, compliance_report)
    
    with tab5:
        show_email_tab(results)


def show_overview_tab(results: Dict[str, Any]):
    """Overview tab content."""
    st.subheader("Document Overview")
    
    metadata = results['metadata']
    risk_report = results['risk_report']
    compliance_report = results['compliance_report']
    
    # Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Word Count", f"{metadata.get('word_count', 0):,}")
    
    with col2:
        st.metric("Page Count", metadata.get('page_count', 0))
    
    with col3:
        st.metric("Risk Score", f"{risk_report['overall_score']:.1f}%")
    
    with col4:
        st.metric("Compliance", f"{compliance_report['compliance_score']:.1f}%")
    
    with col5:
        st.metric("Violations", len(compliance_report.get('violations', [])))
    
    st.divider()
    
    # Overall status
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Overall Assessment")
        st.markdown(f"**Status:** {results['overall_status'].upper().replace('_', ' ')}")
        st.markdown(f"**Risk Level:** {risk_report['risk_level'].upper()}")
        st.markdown(f"**Assessment Certainty:** {risk_report.get('assessment_certainty', risk_report.get('confidence', 0)):.1f}%")
        
        if risk_report.get('requires_notification'):
            st.warning("⚠️ Attorney review required")
        else:
            st.success("✅ No immediate concerns")
    
    with col2:
        st.markdown("### Processing Info")
        st.caption(f"**File:** {metadata.get('file_name', 'Unknown')}")
        st.caption(f"**Processed:** {metadata.get('processing_timestamp', 'N/A')}")
        st.caption(f"**Method:** {'Azure' if st.session_state.use_azure else 'Local'}")
    
    st.divider()
    
    # Score explanations
    st.info("""
    📊 **Understanding Your Scores:**
    
    **Confidence Score:** Measures how certain the AI is about its analysis. 
    90%+ = Very reliable | 70-89% = Reliable | 50-69% = Manual review recommended | <50% = Expert review required
    
    **Compliance Score:** Measures alignment with executive order requirements.
    90%+ = Excellent compliance | 70-89% = Good compliance | 50-69% = Needs attention | <50% = Significant issues
    
    **Risk Score:** Overall risk assessment (higher = lower risk). Calculated as: Compliance (60%) + Quality (25%) + Completeness (15%).
    90%+ = Approve | 75-89% = Approve with minor revisions | 60-74% = Major revisions required | <60% = Recommend rejection
    """)


def show_summary_tab(summary: Dict[str, Any], metadata: Dict[str, Any]):
    """Summary tab content."""
    st.subheader("Document Summary")
    
    # Executive summary
    st.markdown("### Executive Summary")
    st.write(summary.get('executive_summary', 'No summary available'))
    
    st.divider()
    
    # Key clauses
    st.markdown("### Key Clauses & Requirements")
    key_clauses = summary.get('key_clauses', [])
    
    if key_clauses:
        for i, clause in enumerate(key_clauses, 1):
            with st.expander(f"Clause {i}", expanded=(i == 1)):
                st.write(clause)
    else:
        st.info("No key clauses identified")
    
    st.divider()
    
    # Key topics
    st.markdown("### Key Topics Identified")
    topics = summary.get('key_topics', [])
    
    if topics:
        cols = st.columns(4)
        for i, topic in enumerate(topics):
            with cols[i % 4]:
                st.markdown(f"🏷️ **{topic.title()}**")
    else:
        st.info("No topics identified")


def show_compliance_tab(compliance_report: Dict[str, Any]):
    """Compliance tab content."""
    st.subheader("Compliance Validation Results")
    
    # Overall compliance
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score = compliance_report['compliance_score']
        st.metric("Compliance Score", f"{score:.1f}%")
    
    with col2:
        status = compliance_report['overall_status']
        st.metric("Status", status.replace('_', ' ').title())
    
    with col3:
        eo_count = len(compliance_report.get('relevant_executive_orders', []))
        st.metric("Relevant EOs", eo_count)
    
    st.divider()
    
    # Relevant Executive Orders
    st.markdown("### Relevant Executive Orders")
    relevant_eos = compliance_report.get('relevant_executive_orders', [])
    
    if relevant_eos:
        for eo in relevant_eos:
            with st.expander(f"📜 {eo['name']}", expanded=False):
                st.markdown(f"**Relevance Score:** {eo.get('relevance', 0):.1f}")
                
                requirements = eo.get('key_requirements', [])
                if requirements:
                    st.markdown("**Key Requirements:**")
                    for req in requirements[:3]:
                        st.caption(f"• {req[:200]}...")
    else:
        st.warning("No relevant executive orders found")
    
    st.divider()
    
    # Detailed Analysis with Citations
    if compliance_report.get('analysis'):
        st.markdown("### 📄 Detailed Compliance Analysis")
        st.text_area("Analysis", compliance_report['analysis'], height=200, disabled=True)
        st.caption("* Analysis includes citations to specific sections of executive orders from the knowledge base")
        
        # Citation Details Section
        citations = compliance_report.get('citations', [])
        if citations:
            st.markdown("#### 📎 Citation Details")
            for idx, citation in enumerate(citations, 1):
                with st.expander(f"Citation {idx}: {citation.get('title', 'Untitled')}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Title:** {citation.get('title', 'N/A')}")
                        if citation.get('url'):
                            st.markdown(f"**URL:** [{citation['url']}]({citation['url']})")
                        if citation.get('file_id'):
                            st.caption(f"File ID: {citation['file_id']}")
                    
                    with col2:
                        if citation.get('tool_name'):
                            st.caption(f"Tool: {citation['tool_name']}")
                    
                    # Snippet
                    if citation.get('snippet'):
                        st.markdown("**Excerpt:**")
                        st.info(f'"{citation["snippet"]}"')
                    
                    # Additional Properties
                    if citation.get('additional_properties'):
                        st.markdown("**Additional Properties:**")
                        props = citation['additional_properties']
                        if props.get('executive_order_number'):
                            st.caption(f"• EO Number: {props['executive_order_number']}")
                        if props.get('effective_date'):
                            st.caption(f"• Effective Date: {props['effective_date']}")
                        if props.get('page_number'):
                            st.caption(f"• Page: {props['page_number']}")
                        if props.get('document_type'):
                            st.caption(f"• Document Type: {props['document_type']}")
                    
                    # Annotated Regions (Text Regions)
                    if citation.get('annotated_regions'):
                        st.markdown("**Text Regions:**")
                        for i, region in enumerate(citation['annotated_regions'], 1):
                            st.caption(f"Region {i}: Index {region.get('start_index', 0)} - {region.get('end_index', 0)}")
        
        st.divider()
    
    # Violations
    st.markdown("### Compliance Violations")
    violations = compliance_report.get('violations', [])
    
    if violations:
        for i, violation in enumerate(violations, 1):
            st.error(f"**Violation {i}:** {violation.get('message', 'Unknown')}")
            st.caption(f"EO: {violation.get('executive_order', 'Unknown')}")
            st.caption(f"Requirement: {violation.get('requirement', 'Unknown')[:150]}...")
            st.divider()
    else:
        st.success("✅ No compliance violations found")
    
    # Warnings
    st.markdown("### Warnings")
    warnings = compliance_report.get('warnings', [])
    
    if warnings:
        for i, warning in enumerate(warnings, 1):
            st.warning(f"**Warning {i}:** {warning.get('message', 'Unknown')}")
            st.caption(f"EO: {warning.get('executive_order', 'Unknown')}")
    else:
        st.info("No warnings")


def show_risk_tab(risk_report: Dict[str, Any], compliance_report: Dict[str, Any] = None):
    """Risk analysis tab content."""
    st.subheader("Risk Assessment")
    
    # Risk metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score = risk_report['overall_score']
        level = risk_report['risk_level']
        st.metric("Overall Risk Score", f"{score:.1f}%", delta=level.upper())
    
    with col2:
        certainty = risk_report.get('assessment_certainty', risk_report.get('confidence', 0))
        st.metric("Assessment Certainty", f"{certainty:.1f}%")
    
    with col3:
        required = "Yes" if risk_report.get('requires_notification') else "No"
        st.metric("Notification Required", required)
    
    st.divider()
    
    # Risk Score Breakdown (like React app)
    st.markdown("### 📊 Risk Score Breakdown")
    st.caption("Formula: Risk = (Confidence-Weighted Compliance × 60%) + (Quality × 25%) + (Completeness × 15%)")
    
    breakdown = risk_report.get('risk_breakdown', {})
    compliance_risk = breakdown.get('compliance_risk', {})
    quality_risk = breakdown.get('quality_risk', {})
    completeness_risk = breakdown.get('completeness_risk', {})
    
    # Get raw compliance score and confidence for transparency
    raw_compliance_score = compliance_report.get('compliance_score', 0) if compliance_report else 0
    ai_confidence = compliance_report.get('confidence_score', 70) if compliance_report else 70
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Compliance (60%)")
        st.metric("Weighted Score", f"{compliance_risk.get('score', 0):.1f}%")
        st.caption(f"= {raw_compliance_score:.0f}% × {ai_confidence:.0f}% confidence")
    
    with col2:
        st.markdown("#### Quality (25%)")
        st.metric("Score", f"{quality_risk.get('score', 0):.1f}%")
        st.caption("Document structure & clarity")
    
    with col3:
        st.markdown("#### Completeness (15%)")
        st.metric("Score", f"{completeness_risk.get('score', 0):.1f}%")
        st.caption("Required sections present")
    
    # Explanation note
    st.info(f"""
    💡 **Note:** The Compliance Score from the Compliance tab ({raw_compliance_score:.1f}%) 
    is multiplied by AI Confidence ({ai_confidence:.1f}%) to produce the risk-weighted value ({compliance_risk.get('score', 0):.1f}%). 
    Lower AI confidence reduces the weighted score to account for analysis uncertainty.
    """)
    
    st.divider()
    
    # Risk breakdown details
    st.markdown("### Risk Component Details")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Compliance Risk")
        st.caption(f"Violations: {compliance_risk.get('violations_count', 0)}")
        st.caption(f"Warnings: {compliance_risk.get('warnings_count', 0)}")
    
    with col2:
        st.markdown("#### Quality Risk")
        st.caption(f"Words: {quality_risk.get('word_count', 0)}")
        st.caption(f"Pages: {quality_risk.get('page_count', 0)}")
    
    with col3:
        st.markdown("#### Completeness Risk")
        st.caption(f"Score: {completeness_risk.get('score', 0):.1f}%")
    
    st.divider()
    
    # Risk factors
    st.markdown("### Risk Factors")
    risk_factors = risk_report.get('risk_factors', [])
    
    if risk_factors:
        for factor in risk_factors:
            severity = factor.get('severity', 'medium')
            icon = "🔴" if severity == "high" else "🟡"
            st.markdown(f"{icon} **{factor.get('factor', 'Unknown')}** ({severity})")
            st.caption(factor.get('description', 'No description'))
    else:
        st.success("No significant risk factors identified")
    
    st.divider()
    
    # Recommendations
    st.markdown("### Recommendations")
    recommendations = risk_report.get('recommendations', [])
    
    if recommendations:
        for rec in recommendations:
            priority = rec.get('priority', 'medium')
            if priority == 'critical' or priority == 'high':
                st.error(f"**{rec.get('action', 'Unknown')}**")
            else:
                st.info(f"**{rec.get('action', 'Unknown')}**")
            st.caption(rec.get('description', 'No description'))
    else:
        st.info("No specific recommendations")
    
    st.divider()
    
    # Referenced Executive Orders
    st.markdown("### 📜 Referenced Executive Orders")
    relevant_eos = risk_report.get('relevant_executive_orders', [])
    
    if relevant_eos:
        for eo in relevant_eos:
            eo_name = eo.get('name', f'Executive Order {eo.get("number", "Unknown")}')
            with st.expander(f"📜 {eo_name}", expanded=False):
                st.markdown(f"**Relevance Score:** {eo.get('relevance', 0):.1f}%")
                
                if eo.get('number'):
                    st.caption(f"EO Number: {eo.get('number')}")
                
                if eo.get('title') and eo.get('title') != eo.get('name'):
                    st.markdown(f"**Title:** {eo.get('title')}")
                
                requirements = eo.get('key_requirements', [])
                if requirements:
                    st.markdown("**Key Requirements & Citations:**")
                    for req in requirements[:5]:
                        st.caption(f"• {req[:300]}{'...' if len(req) > 300 else ''}")
    else:
        st.info("No relevant executive orders found in risk report")


def show_email_tab(results: Dict[str, Any]):
    """Email notification tab content."""
    st.subheader("Email Notification")
    
    if not results.get('email_sent'):
        st.info("Email notification was not sent for this proposal.")
        
        risk_report = results['risk_report']
        if not risk_report.get('requires_notification'):
            st.success("✅ Risk level does not require attorney notification")
        else:
            st.warning("⚠️ Email sending was disabled for this analysis")
        
        return
    
    # Email details
    notification_step = results['steps'].get('notification', {})
    email_data = notification_step.get('email_data', {})
    send_result = notification_step.get('send_result', {})
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Email Details")
        st.markdown(f"**To:** {email_data.get('to', 'Unknown')}")
        st.markdown(f"**From:** {email_data.get('from', 'Unknown')}")
        st.markdown(f"**Priority:** {email_data.get('priority', 'normal').upper()}")
        st.markdown(f"**Status:** {send_result.get('status', 'unknown').upper()}")
        st.markdown(f"**Sent:** {send_result.get('sent_at', 'Unknown')}")
    
    with col2:
        st.markdown("### Send Method")
        method = send_result.get('method', 'unknown')
        if method == 'graph_api':
            st.success("✓ Sent via Microsoft Graph API")
        else:
            st.info("🔧 Simulated (Demo Mode)")
    
    st.divider()
    
    # Email subject
    st.markdown("### Subject")
    st.code(email_data.get('subject', 'No subject'), language=None)
    
    st.divider()
    
    # Email body
    st.markdown("### Email Body (Plain Text)")
    with st.expander("View full email content", expanded=False):
        st.text(email_data.get('body_text', 'No content'))


def show_knowledge_base_page():
    """Knowledge base explorer page."""
    st.markdown('<div class="main-header">📚 Knowledge Base Explorer</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Browse executive orders and compliance guidelines</div>', unsafe_allow_html=True)
    
    kb_path = Path(__file__).parent.parent / 'knowledge_base'
    
    # Executive Orders
    st.markdown("### Executive Orders")
    eo_path = kb_path / 'sample_executive_orders'
    eo_files = list(eo_path.glob('*.txt')) + list(eo_path.glob('*.pdf'))
    
    if eo_files:
        selected_eo = st.selectbox("Select an executive order", [f.stem for f in eo_files])
        
        if selected_eo:
            # Find the actual file (could be .txt or .pdf)
            eo_file = None
            for f in eo_files:
                if f.stem == selected_eo:
                    eo_file = f
                    break
            
            if eo_file:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"#### {selected_eo.replace('_', ' ')}")
                
                # Check if it's a text file or PDF
                if eo_file.suffix == '.txt':
                    try:
                        with open(eo_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        with col2:
                            st.metric("Length", f"{len(content.split())} words")
                        
                        with st.expander("View content", expanded=False):
                            st.text_area("Executive Order Content", content, height=400, label_visibility="collapsed")
                    except Exception as e:
                        st.error(f"Error reading file: {str(e)}")
                else:
                    # It's a PDF file
                    with col2:
                        st.metric("Type", "PDF")
                    
                    st.info("📄 PDF file - Download to view the full content")
                    
                    try:
                        with open(eo_file, 'rb') as f:
                            pdf_bytes = f.read()
                        
                        st.download_button(
                            label="📥 Download PDF",
                            data=pdf_bytes,
                            file_name=eo_file.name,
                            mime="application/pdf"
                        )
                    except Exception as e:
                        st.error(f"Error loading PDF: {str(e)}")
    else:
        st.warning("No executive orders found in knowledge base")
    
    st.divider()
    
    # Sample Proposals
    st.markdown("### Sample Grant Proposals")
    sample_path = kb_path / 'sample_proposals'
    sample_files = list(sample_path.glob('*.pdf')) + list(sample_path.glob('*.txt'))
    
    if sample_files:
        st.markdown(f"Found {len(sample_files)} sample proposals")
        for sample in sample_files:
            st.markdown(f"📄 **{sample.name}**")
    else:
        st.info("No sample proposals found")


def show_about_page():
    """About page."""
    st.markdown('<div class="main-header">ℹ️ About This Demo</div>', unsafe_allow_html=True)
    
    st.markdown("""
    ## Grant Proposal Compliance Automation
    
    This solution accelerator demonstrates how to automate the review of grant proposals 
    for compliance with executive orders using the **Azure AI Agent Framework** and Azure AI services. 
    The system leverages specialized AI agents in a multi-agent orchestration pattern to provide 
    end-to-end automation from document ingestion through risk assessment and notification.
    
    ### ⚠️ Preview Features & SDK Versions
    
    This project uses **Azure AI Foundry Portal (preview)** and several **beta/preview SDK packages**:
    
    | Package | Version | Status |
    |---------|---------|--------|
    | `agent-framework` | 1.0.0b260114 | Beta |
    | `azure-ai-projects` | 2.0.0b3 | Beta |
    | `azure-ai-agents` | 1.2.0b5 | Beta |
    | `azure-search-documents` | 11.7.0b2 | Beta |
    
    > **Note**: Preview features may not be suitable for production workloads.
    
    ### Features
    
    - **📄 Document Processing**: Automatic text extraction from PDF, Word, and text files
    - **📋 AI Summarization**: Generate executive summaries and identify key clauses
    - **✅ Compliance Validation**: Cross-check proposals against executive orders with citations
    - **⚠️ Risk Assessment**: Calculate risk scores using weighted formula (Compliance 60% + Quality 25% + Completeness 15%)
    - **📊 Score Explanations**: Confidence, Compliance, and Risk scores with interpretations
    - **📧 Email Notifications**: Automatic attorney notifications for high-risk proposals
    - **👨‍⚖️ Human-in-the-Loop**: Attorney validation workflow
    
    ### Orchestrator Options
    
    This demo supports **three orchestrator implementations**:
    
    1. **Original Orchestrator** (`legacy`)
       - Manual async coordination
       - Agent Framework only (`AGENT_SERVICE=agent-framework`)
    
    2. **Sequential Workflow Orchestrator** (`sequential`)
       - Agent Framework sequential workflows with event streaming
       - Clear separation of concerns with Executor classes
    
    3. **Foundry Orchestrator** (`foundry`)
       - Uses Azure AI Projects SDK (`azure-ai-projects`)
       - Agents visible in Azure AI Foundry portal
       - Requires `AGENT_SERVICE=foundry`
    
    ### Technology Stack
    
    - **Azure AI Agent Framework**: Multi-agent orchestration & coordination (v1.0.0b260114)
    - **Azure AI Foundry**: Agent deployment & management (preview)
    - **Azure AI Projects SDK**: Foundry agent service (v2.0.0b3)
    - **Azure OpenAI**: GPT-4 LLM analysis
    - **Azure AI Search**: Semantic search & RAG (v11.7.0b2)
    - **Azure Document Intelligence**: OCR and document processing
    - **Azure Function Apps**: Email notifications and workflows
    - **React 19.2.3 + TypeScript 5.7.3**: Modern UI framework (production)
    - **FastAPI**: REST backend API
    - **Streamlit**: Interactive demo interface (legacy)
    
    ### Environment Variables
    
    Key configuration options:
    
    ```bash
    # Agent Service Selection
    AGENT_SERVICE=agent-framework  # or 'foundry'
    
    # Authentication (depends on AGENT_SERVICE)
    # agent-framework → USE_MANAGED_IDENTITY=true (recommended)
    # foundry → USE_MANAGED_IDENTITY=false (required for local dev)
    USE_MANAGED_IDENTITY=true
    
    # Orchestrator Type
    ORCHESTRATOR_TYPE=sequential  # or 'legacy' or 'foundry'
    
    # Foundry Agent Persistence (when AGENT_SERVICE=foundry)
    PERSIST_FOUNDRY_AGENTS=false  # true to keep agents in portal
    
    # Demo Mode
    DEMO_MODE=true  # false for production with Azure services
    KNOWLEDGE_BASE_SOURCE=local  # or 'azure'
    ```
    
    ### Workflow
    
    1. **Upload Proposal** → Document Ingestion Agent extracts text
    2. **Summarization** → Creates executive summary
    3. **Compliance Check** → Validates against executive orders with citations
    4. **Risk Scoring** → Calculates weighted risk score
    5. **Email Notification** → Alerts attorney if needed
    6. **Human Review** → Attorney validates and approves
    
    ### Architecture
    
    This demo uses a multi-agent architecture with:
    
    - **Document Ingestion Agent**: OCR and text extraction
    - **Summarization Agent**: Content analysis
    - **Compliance Validator Agent**: Executive order matching with citations
    - **Risk Scoring Agent**: Weighted risk assessment
    - **Email Trigger Agent**: Notification management
    
    ### Sidebar Configuration
    
    Use the sidebar to configure:
    
    - **Agent Service**: Select `agent-framework` or `foundry`
    - **Orchestrator Type**: Choose from `legacy`, `sequential`, or `foundry`
    - **Azure Services**: Toggle Azure integration on/off
    
    ### Setting Up Azure AI Search
    
    Azure AI Search provides semantic search capabilities but is **optional**. 
    The app will automatically use local knowledge base search if Azure Search is unavailable.
    
    To set up Azure AI Search:
    
    1. Configure environment variables in `.env`:
       ```bash
       AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
       AZURE_SEARCH_API_KEY=your_api_key
       AZURE_SEARCH_INDEX_NAME=grant-compliance-index
       ```
    
    2. Create and populate the search index:
       ```bash
       python scripts/index_knowledge_base.py
       ```
    
    See [docs/uploadPdfsToAzureSearch.md](../docs/uploadPdfsToAzureSearch.md) for detailed instructions.
    
    ### Learn More
    
    - [Azure AI Agent Framework](https://learn.microsoft.com/azure/ai-services/agents/)
    - [Azure AI Foundry](https://learn.microsoft.com/azure/ai-foundry/)
    - [Project Documentation](../docs/)
    - [Scoring System](../docs/ScoringSystem.md)
    - [Sequential Workflow Orchestrator](../docs/SequentialWorkflowOrchestrator.md)
    """)


if __name__ == "__main__":
    main()
