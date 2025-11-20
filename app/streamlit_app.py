"""
Grant Proposal Compliance Demo - Streamlit Application

Interactive demo for automated grant proposal compliance checking using Azure AI Foundry.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any
import json

# Page configuration
st.set_page_config(
    page_title="Grant Compliance Automation Demo",
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
    .status-compliant {
        background-color: #DFF6DD;
        color: #107C10;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-weight: bold;
    }
    .status-review {
        background-color: #FFF4CE;
        color: #8A8886;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-weight: bold;
    }
    .status-non-compliant {
        background-color: #FDE7E9;
        color: #A80000;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-weight: bold;
    }
    .metric-card {
        background-color: #F3F2F1;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .citation-box {
        background-color: #F3F2F1;
        border-left: 4px solid #0078D4;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
def init_session_state():
    """Initialize session state variables."""
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'current_proposal' not in st.session_state:
        st.session_state.current_proposal = None
    if 'attorney_validated' not in st.session_state:
        st.session_state.attorney_validated = False
    if 'demo_mode' not in st.session_state:
        st.session_state.demo_mode = True


def load_sample_proposals() -> Dict[str, str]:
    """Load sample grant proposals for demo."""
    samples = {
        "Affordable Housing Initiative": """
        GRANT APPLICATION - AFFORDABLE HOUSING INITIATIVE
        
        Requesting Department: Department of Housing and Urban Development
        Project Lead: Jane Smith, Director of Community Development
        
        PROJECT OVERVIEW:
        We request $2,500,000 in funding to develop 150 units of affordable housing 
        for low-income families in the downtown district. This project aligns with 
        Executive Order 14008 on climate action by incorporating sustainable building 
        practices and renewable energy systems.
        
        BUDGET BREAKDOWN:
        - Land acquisition: $800,000
        - Construction: $1,400,000
        - Renewable energy systems: $200,000
        - Accessibility improvements: $100,000
        
        PROJECT TIMELINE: 24 months
        
        TARGET BENEFICIARIES:
        - 150 low-income families (income at or below 60% AMI)
        - Priority for veterans and persons with disabilities
        - 30% units reserved for extremely low-income households
        
        COMPLIANCE DECLARATIONS:
        - Project meets all local zoning requirements
        - Environmental impact assessment completed
        - Community consultation process conducted
        - Equal opportunity housing provisions included
        
        SUSTAINABILITY FEATURES:
        - Solar panel installation on all units
        - Energy-efficient HVAC systems
        - Water conservation systems
        - Green building certification (LEED Silver minimum)
        
        This project will create jobs, reduce carbon emissions, and provide 
        much-needed affordable housing in our community.
        """,
        
        "Youth Education Program": """
        GRANT APPLICATION - STEM EDUCATION OUTREACH PROGRAM
        
        Requesting Department: Department of Education
        Project Lead: Dr. Robert Johnson, Superintendent
        
        PROJECT OVERVIEW:
        Request for $500,000 to establish a comprehensive STEM education program 
        targeting underserved middle schools in rural areas. Program will provide 
        hands-on learning experiences, technology access, and mentorship.
        
        BUDGET BREAKDOWN:
        - Technology equipment: $200,000
        - Curriculum development: $100,000
        - Teacher training: $80,000
        - Student materials: $70,000
        - Program administration: $50,000
        
        PROJECT TIMELINE: 18 months
        
        TARGET BENEFICIARIES:
        - 500 students in grades 6-8
        - Focus on schools with >70% students on free/reduced lunch
        - Special emphasis on encouraging female and minority participation
        
        PROGRAM COMPONENTS:
        - After-school STEM clubs at 5 schools
        - Summer intensive programs
        - Industry mentorship partnerships
        - College campus visits
        - Robotics and coding competitions
        
        EXPECTED OUTCOMES:
        - Increase STEM course enrollment by 30%
        - Improve standardized test scores in math and science
        - Establish sustainable partnerships with local tech companies
        - Create pathways to STEM careers
        """,
        
        "Emergency Response Infrastructure": """
        GRANT APPLICATION - EMERGENCY RESPONSE MODERNIZATION
        
        Requesting Department: Office of Emergency Management
        Project Lead: Chief Michael Davis
        
        PROJECT OVERVIEW:
        Request for $1,800,000 to upgrade emergency communication systems and 
        disaster response infrastructure. This project addresses critical gaps 
        identified in recent emergency assessments and aligns with federal 
        preparedness requirements.
        
        BUDGET BREAKDOWN:
        - Communication system upgrades: $900,000
        - Emergency operations center renovation: $500,000
        - Equipment and vehicles: $300,000
        - Training and exercises: $100,000
        
        PROJECT TIMELINE: 12 months
        
        JUSTIFICATION:
        Current emergency communication systems are over 15 years old and lack 
        interoperability with federal and neighboring jurisdictions. Recent 
        severe weather events exposed critical vulnerabilities in our response 
        capabilities.
        
        COMPLIANCE CONSIDERATIONS:
        - Meets FEMA National Preparedness System requirements
        - Addresses DHS interoperability mandates
        - Includes cybersecurity protections per Executive Order 14028
        - Accessibility features for persons with disabilities
        
        EXPECTED OUTCOMES:
        - Improved emergency response times by 25%
        - Enhanced coordination with federal and state agencies
        - Better protection of critical infrastructure
        - Increased community resilience to natural disasters
        
        Note: This request includes matching funds commitment of $200,000 
        from local budget reserves.
        """
    }
    return samples


def load_sample_executive_orders() -> Dict[str, Dict[str, str]]:
    """Load sample executive order content for demo."""
    return {
        "EO 14008": {
            "title": "Executive Order 14008 - Tackling the Climate Crisis",
            "content": """This executive order places the climate crisis at the center of 
            United States foreign policy and national security. It requires federal agencies 
            to prioritize climate considerations in their decision-making and establish a 
            government-wide approach to combating climate change. 
            
            Key requirements for grant programs:
            - Projects must assess climate-related risks
            - Preference for projects incorporating renewable energy
            - Requirements for greenhouse gas emission reduction plans
            - Mandatory climate risk disclosures
            - Integration of climate adaptation strategies"""
        },
        "EO 14028": {
            "title": "Executive Order 14028 - Improving Cybersecurity",
            "content": """This executive order aims to improve the nation's cybersecurity 
            posture. It establishes new requirements for federal agencies and vendors 
            regarding software security, incident reporting, and data protection.
            
            Key requirements for grant programs:
            - Cybersecurity measures for digital infrastructure projects
            - Incident response and reporting protocols
            - Supply chain security assessments
            - Zero-trust architecture principles
            - Multi-factor authentication requirements"""
        },
        "EO 13985": {
            "title": "Executive Order 13985 - Advancing Racial Equity",
            "content": """This executive order advances equity for underserved communities 
            and directs federal agencies to assess whether their programs and policies 
            perpetuate systemic barriers to opportunities.
            
            Key requirements for grant programs:
            - Equity impact assessments required
            - Outreach to underserved communities
            - Data collection on program beneficiaries
            - Removal of barriers to program access
            - Equitable distribution of benefits"""
        }
    }


def simulate_ai_analysis(proposal_text: str) -> Dict[str, Any]:
    """
    Simulate AI analysis for demo purposes.
    In production, this would call the actual Azure AI agent.
    """
    import time
    
    # Simulate processing time
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    steps = [
        "Extracting document metadata...",
        "Searching knowledge base for relevant executive orders...",
        "Analyzing compliance requirements...",
        "Cross-referencing proposal against regulations...",
        "Generating compliance summary...",
        "Calculating confidence scores..."
    ]
    
    for i, step in enumerate(steps):
        status_text.text(step)
        progress_bar.progress((i + 1) / len(steps))
        time.sleep(0.5)
    
    status_text.empty()
    progress_bar.empty()
    
    # Determine mock compliance status based on proposal content
    text_lower = proposal_text.lower()
    
    if "affordable housing" in text_lower:
        status = "Compliant"
        confidence = 92
        findings = [
            "Project aligns with Executive Order 14008 climate requirements",
            "Renewable energy integration clearly specified",
            "Target beneficiary criteria meet equity standards (EO 13985)",
            "Budget allocation appears reasonable and detailed",
            "Accessibility requirements properly addressed"
        ]
        concerns = [
            "Verify LEED certification timeline aligns with project completion",
            "Confirm land acquisition complies with local environmental regulations"
        ]
        recommendations = [
            "Approve with minor documentation clarifications",
            "Request LEED certification commitment letter",
            "Verify community consultation records"
        ]
        exec_orders = [
            "EO 14008: Climate action and renewable energy requirements - COMPLIANT",
            "EO 13985: Racial equity and underserved community focus - COMPLIANT",
            "Fair Housing Act requirements - COMPLIANT"
        ]
    elif "emergency" in text_lower or "infrastructure" in text_lower:
        status = "Requires Review"
        confidence = 75
        findings = [
            "Project addresses critical infrastructure needs",
            "Includes cybersecurity provisions per EO 14028",
            "Interoperability requirements properly documented",
            "Budget appears comprehensive"
        ]
        concerns = [
            "Matching funds commitment needs verification",
            "Cybersecurity framework details are limited",
            "Environmental impact assessment not mentioned",
            "Unclear if project includes equity considerations"
        ]
        recommendations = [
            "Request detailed cybersecurity implementation plan",
            "Require proof of matching funds availability",
            "Attorney review recommended for federal compliance verification",
            "Request equity impact assessment"
        ]
        exec_orders = [
            "EO 14028: Cybersecurity requirements - PARTIALLY COMPLIANT (needs detail)",
            "EO 13985: Equity considerations - INSUFFICIENT INFORMATION",
            "FEMA National Preparedness System - COMPLIANT"
        ]
    else:
        status = "Compliant"
        confidence = 88
        findings = [
            "Project objectives clearly defined and measurable",
            "Target population properly identified",
            "Budget breakdown is detailed and justified",
            "Timeline appears realistic"
        ]
        concerns = [
            "Sustainability plan beyond grant period should be clarified",
            "Partnership agreements should be documented"
        ]
        recommendations = [
            "Approve with request for sustainability plan",
            "Document industry partnership commitments"
        ]
        exec_orders = [
            "EO 13985: Focus on underserved populations - COMPLIANT",
            "General grant compliance requirements - COMPLIANT"
        ]
    
    # Convert string format to structured format to match real API output
    structured_exec_orders = []
    for eo_string in exec_orders:
        # Parse the string format: "EO 14008: Title - STATUS"
        parts = eo_string.split(":")
        if len(parts) >= 2:
            eo_num = parts[0].replace("EO", "").strip()
            title_status = parts[1].strip() if len(parts) > 1 else ""
            title = title_status.split(" - ")[0].strip() if " - " in title_status else title_status
            
            structured_exec_orders.append({
                'name': f"EO {eo_num}",
                'number': eo_num,
                'title': title,
                'relevance': 85.0,
                'key_requirements': [f"{eo_string}"]
            })
        else:
            structured_exec_orders.append({
                'name': eo_string,
                'title': eo_string,
                'relevance': 80.0,
                'key_requirements': [eo_string]
            })
    
    return {
        "status": status,
        "confidence_score": confidence,
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "findings": findings,
        "concerns": concerns,
        "recommendations": recommendations,
        "executive_orders": structured_exec_orders,  # Now using structured format
        "full_analysis": f"""
# Compliance Analysis Summary

## Overall Assessment
The grant proposal has been analyzed against relevant executive orders and compliance requirements.

**Status**: {status}
**Confidence Score**: {confidence}%

## Key Findings
{chr(10).join(['- ' + f for f in findings])}

## Areas of Concern
{chr(10).join(['- ' + c for c in concerns])}

## Applicable Executive Orders
{chr(10).join(['- ' + e for e in exec_orders])}

## Recommendations
{chr(10).join(['- ' + r for r in recommendations])}

---
*Analysis performed by Azure AI Foundry Compliance Agent*
*Attorney review and validation required before final determination*
"""
    }


def render_header():
    """Render page header."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown('<div class="main-header">🏛️ Grant Proposal Compliance Automation</div>', 
                   unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Automated compliance review with Azure AI Foundry</div>', 
                   unsafe_allow_html=True)
    
    with col2:
        if st.session_state.demo_mode:
            st.info("🎬 Demo Mode")


def render_sidebar():
    """Render sidebar with navigation and info."""
    with st.sidebar:
        st.title("Navigation")
        
        page = st.radio(
            "Select a page:",
            ["📝 Document Upload", "📊 Analysis Dashboard", "👨‍⚖️ Attorney Review", "📚 Knowledge Base", "ℹ️ About"]
        )
        
        st.divider()
        
        st.subheader("Workflow Status")
        
        # Workflow progress
        if st.session_state.current_proposal:
            st.success("✅ Document Uploaded")
        else:
            st.info("⏳ Awaiting Document")
        
        if st.session_state.analysis_results:
            st.success("✅ AI Analysis Complete")
        else:
            st.info("⏳ Analysis Pending")
        
        if st.session_state.attorney_validated:
            st.success("✅ Attorney Validated")
        else:
            st.info("⏳ Validation Pending")
        
        st.divider()
        
        if st.button("🔄 Reset Demo"):
            st.session_state.clear()
            init_session_state()
            st.rerun()
        
        return page


def render_upload_page():
    """Render document upload page."""
    st.header("📝 Submit Grant Proposal for Review")
    
    tab1, tab2 = st.tabs(["📤 Upload Document", "📋 Sample Proposals"])
    
    with tab1:
        st.write("Upload a grant proposal document for automated compliance analysis.")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['txt', 'pdf', 'docx'],
            help="Supported formats: TXT, PDF, DOCX"
        )
        
        if uploaded_file:
            # Read file content
            if uploaded_file.type == "text/plain":
                proposal_text = uploaded_file.read().decode('utf-8')
            else:
                st.warning("PDF and DOCX processing would use Azure Document Intelligence in production")
                proposal_text = "Sample extracted text from document..."
            
            st.text_area("Document Preview", proposal_text, height=200)
            
            if st.button("🚀 Analyze for Compliance", type="primary"):
                st.session_state.current_proposal = proposal_text
                with st.spinner("Analyzing document..."):
                    st.session_state.analysis_results = simulate_ai_analysis(proposal_text)
                st.success("✅ Analysis complete! Go to 'Analysis Dashboard' to view results.")
                st.balloons()
    
    with tab2:
        st.write("Try the demo with pre-loaded sample grant proposals.")
        
        samples = load_sample_proposals()
        
        selected_sample = st.selectbox("Select a sample proposal:", list(samples.keys()))
        
        if selected_sample:
            st.text_area("Sample Proposal Content", samples[selected_sample], height=300)
            
            if st.button("🚀 Analyze This Sample", type="primary"):
                st.session_state.current_proposal = samples[selected_sample]
                with st.spinner("Analyzing document..."):
                    st.session_state.analysis_results = simulate_ai_analysis(samples[selected_sample])
                st.success("✅ Analysis complete! Go to 'Analysis Dashboard' to view results.")
                st.balloons()


def render_status_badge(status: str):
    """Render colored status badge."""
    if status == "Compliant":
        css_class = "status-compliant"
    elif status == "Non-Compliant":
        css_class = "status-non-compliant"
    else:
        css_class = "status-review"
    
    st.markdown(f'<div class="{css_class}">{status}</div>', unsafe_allow_html=True)


def render_analysis_dashboard():
    """Render analysis results dashboard."""
    st.header("📊 Compliance Analysis Dashboard")
    
    if not st.session_state.analysis_results:
        st.warning("No analysis results available. Please upload and analyze a document first.")
        return
    
    results = st.session_state.analysis_results
    
    # Top metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Compliance Status", results['status'])
    
    with col2:
        st.metric("Confidence Score", f"{results['confidence_score']}%")
    
    with col3:
        st.metric("Analysis Date", results['analysis_date'].split()[0])
    
    # Score Explanations
    st.info("""
    **📊 Understanding Your Scores:**
    
    - **Confidence Score**: Measures how certain the AI is about its analysis
      - 90-100%: Very reliable → proceed with standard review
      - 70-89%: Reliable → generally good
      - 50-69%: Manual review strongly recommended
      - <50%: Expert review required
    
    - **Compliance Score**: Measures alignment with executive order requirements  
      - 90-100%: Excellent compliance
      - 70-89%: Good compliance
      - 50-69%: Needs attention
      - <50%: Significant issues
    
    - **Risk Score**: Overall risk assessment (higher = lower risk)  
      - Formula: Compliance (60%) + Quality (25%) + Completeness (15%)
      - 90-100%: Approve
      - 75-89%: Minor revisions
      - 60-74%: Major revisions
      - <60%: Reject/rework
    
    See `docs/SCORING_SYSTEM.md` for complete documentation.
    """)
    
    st.divider()
    
    # Detailed results in tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Summary", "🔍 Findings", "⚠️ Concerns", "📜 Executive Orders"])
    
    with tab1:
        st.subheader("Analysis Summary")
        render_status_badge(results['status'])
        st.markdown(results['full_analysis'])
    
    with tab2:
        st.subheader("Key Findings")
        for finding in results['findings']:
            st.success(f"✅ {finding}")
    
    with tab3:
        st.subheader("Areas of Concern")
        if results['concerns']:
            for concern in results['concerns']:
                st.warning(f"⚠️ {concern}")
        else:
            st.info("No major concerns identified")
    
    with tab4:
        st.subheader("📜 Referenced Executive Orders & Citations")
        
        # Display executive orders with citation details
        if 'executive_orders' in results:
            for eo in results['executive_orders']:
                # Check if it's a string (old format) or dict (new format)
                if isinstance(eo, str):
                    st.markdown(f'<div class="citation-box">{eo}</div>', unsafe_allow_html=True)
                elif isinstance(eo, dict):
                    # New structured format with full citation details
                    with st.container():
                        st.markdown(f'<div class="citation-box">', unsafe_allow_html=True)
                        st.markdown(f"**{eo.get('name', 'Executive Order')}**")
                        if eo.get('title'):
                            st.markdown(f"*{eo['title']}*")
                        if eo.get('number'):
                            st.caption(f"EO Number: {eo['number']}")
                        if eo.get('relevance'):
                            st.metric("Relevance Score", f"{eo['relevance']:.1f}%")
                        if eo.get('key_requirements'):
                            st.markdown("**Key Requirements & Citations:**")
                            for req in eo['key_requirements']:
                                st.markdown(f"> {req}")
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.markdown("---")
    
    st.divider()
    
    # Recommendations
    st.subheader("📌 Recommendations")
    for rec in results['recommendations']:
        st.info(f"💡 {rec}")
    
    # Download results
    if st.button("📥 Download Analysis Report"):
        st.download_button(
            "Download as JSON",
            data=json.dumps(results, indent=2),
            file_name=f"compliance_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )


def render_attorney_review():
    """Render attorney review interface."""
    st.header("👨‍⚖️ Attorney Review & Validation")
    
    if not st.session_state.analysis_results:
        st.warning("No analysis results available for review.")
        return
    
    results = st.session_state.analysis_results
    
    st.info("🔍 As an attorney, please review the AI-generated analysis and provide your validation.")
    
    # Display summary
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("AI Analysis Summary")
        st.write(f"**Status**: {results['status']}")
        st.write(f"**Confidence**: {results['confidence_score']}%")
    
    with col2:
        render_status_badge(results['status'])
    
    st.divider()
    
    # Attorney decision
    st.subheader("Your Review Decision")
    
    decision = st.radio(
        "Select your decision:",
        ["✅ Approve (Agree with AI assessment)",
         "📝 Approve with Modifications",
         "❌ Reject (Disagree with AI assessment)",
         "🔄 Request More Information"]
    )
    
    attorney_notes = st.text_area(
        "Attorney Notes & Comments",
        placeholder="Enter your professional assessment, any modifications needed, or additional requirements...",
        height=150
    )
    
    if st.button("Submit Review", type="primary"):
        if attorney_notes:
            st.session_state.attorney_validated = True
            st.session_state.attorney_decision = decision
            st.session_state.attorney_notes = attorney_notes
            st.success("✅ Review submitted successfully!")
            st.balloons()
            
            # Show notification simulation
            st.info("📧 Email notification sent to client with your decision.")
        else:
            st.error("Please provide attorney notes before submitting.")


def render_knowledge_base():
    """Render knowledge base explorer."""
    st.header("📚 Knowledge Base Explorer")
    
    st.write("Browse executive orders and compliance documents used for analysis.")
    
    exec_orders = load_sample_executive_orders()
    
    for eo_id, eo_data in exec_orders.items():
        with st.expander(f"**{eo_id}**: {eo_data['title']}"):
            st.markdown(eo_data['content'])
    
    st.divider()
    
    st.subheader("📁 Document Categories")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Executive Orders", "15")
        st.caption("Federal executive orders")
    
    with col2:
        st.metric("Grant Policies", "23")
        st.caption("Department policies")
    
    with col3:
        st.metric("Compliance Rules", "42")
        st.caption("Regulatory guidelines")


def render_about():
    """Render about page."""
    st.header("ℹ️ About This Solution")
    
    st.markdown("""
    ### Grant Proposal Compliance Automation
    
    This demo showcases an AI-powered system for automating grant proposal compliance reviews
    using **Azure AI Foundry** and related Azure services.
    
    #### Key Features
    
    - **🤖 AI-Powered Analysis**: Automated document analysis using Azure AI agents
    - **📚 Knowledge Base Integration**: Semantic search across executive orders and policies
    - **👨‍⚖️ Human-in-the-Loop**: Attorney review and validation workflow
    - **📊 Confidence Scoring**: Transparent confidence metrics for AI decisions
    - **🔔 Automated Notifications**: Email alerts via Azure Function Apps
    
    #### Technologies Used
    
    - **Azure AI Foundry**: Agent orchestration and management
    - **Azure Document Intelligence**: Document OCR and extraction
    - **Azure AI Search**: Semantic search and knowledge base indexing
    - **Azure Function Apps**: Serverless workflow automation
    - **Microsoft Agent Framework**: Agent development and deployment
    - **Streamlit**: Interactive demo interface
    
    #### Workflow
    
    1. **Document Submission**: Grant proposals uploaded via email or web form
    2. **AI Processing**: Automated extraction, indexing, and compliance analysis
    3. **Knowledge Base Query**: Semantic search for relevant executive orders
    4. **Compliance Report**: AI generates structured summary with citations
    5. **Attorney Review**: Human validation and final decision
    6. **Client Notification**: Automated email with results
    
    #### Benefits
    
    - ✅ **Reduced Review Time**: From days to hours
    - ✅ **Consistent Analysis**: Standardized compliance checks
    - ✅ **Better Documentation**: Structured reports with citations
    - ✅ **Attorney Efficiency**: Focus on complex cases requiring expertise
    - ✅ **Audit Trail**: Complete tracking of analysis and decisions
    
    ---
    
    **Note**: This is a demonstration system. Production deployment would require:
    - Proper Azure resource provisioning
    - SharePoint integration for document management
    - Email system integration via Azure Function Apps
    - Security and compliance certifications
    - User authentication and authorization
    """)


def main():
    """Main application entry point."""
    init_session_state()
    
    # Render sidebar and get selected page
    page = render_sidebar()
    
    # Render selected page
    if "Upload" in page:
        render_upload_page()
    elif "Dashboard" in page:
        render_analysis_dashboard()
    elif "Attorney" in page:
        render_attorney_review()
    elif "Knowledge" in page:
        render_knowledge_base()
    elif "About" in page:
        render_about()


if __name__ == "__main__":
    main()
