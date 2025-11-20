# User Guide

## Overview

Welcome to the Grant Proposal Compliance Automation system! This guide will help you understand how to use the application to analyze grant proposals for compliance with executive orders.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Uploading Documents](#uploading-documents)
- [Understanding Results](#understanding-results)
- [Knowledge Base](#knowledge-base)
- [Best Practices](#best-practices)
- [Frequently Asked Questions](#frequently-asked-questions)

---

## Getting Started

### Accessing the Application

**Production URL**: https://your-compliance-app.azurewebsites.net

**Local Development**: http://localhost:3000

### User Roles

1. **Grant Submitters**: Upload and review proposals
2. **Legal Reviewers**: Validate AI-generated compliance reports
3. **Administrators**: Manage knowledge base and system configuration

---

## Uploading Documents

### Step 1: Navigate to Upload Page

Click the **📝 Document Upload** tab in the navigation menu.

### Step 2: Prepare Your Document

**Supported File Types**:
- PDF (.pdf)
- Microsoft Word (.docx)
- Plain Text (.txt)

**File Size Limits**:
- Maximum: 10 MB per file
- Recommended: Under 5 MB for faster processing

**Document Requirements**:
- Grant proposals should include project description, budget, timeline
- Documents must be in English
- Scanned documents will be processed with OCR (may take longer)

### Step 3: Upload Document

1. Click **Choose File** or drag and drop your document
2. Wait for file validation (green checkmark indicates success)
3. Review the document preview (first page shown)
4. Click **🚀 Analyze for Compliance**

### Step 4: Processing

The system will process your document through multiple AI agents:

```
⏳ Document Ingestion (10-30 seconds)
   └─> Extracting text from PDF...

⏳ Summarization (15-30 seconds)
   └─> Generating executive summary...

⏳ Compliance Analysis (30-60 seconds)
   └─> Checking against executive orders...

⏳ Risk Assessment (10-20 seconds)
   └─> Calculating risk scores...

✅ Complete (1-3 minutes total)
```

---

## Understanding Results

### Results Dashboard

After processing, you'll see a comprehensive dashboard with five tabs:

#### 1. Overview Tab

**Key Metrics**:
- **Word Count**: Total words in document
- **Page Count**: Number of pages processed
- **Risk Score**: Overall risk assessment (0-100)
- **Compliance Score**: Alignment with executive orders (0-100)
- **Violations**: Number of compliance issues found

**Score Interpretation Box**:
A blue information box explains what each score means and provides guidance on next steps.

#### 2. Summary Tab

**Executive Summary**:
- AI-generated concise summary of your grant proposal
- Key project objectives and goals
- Funding amount and timeline (if mentioned)

**Key Clauses & Requirements**:
- Important clauses extracted from your document
- Critical requirements and conditions
- Expandable sections for each clause

**Key Topics**:
- Main themes identified in the proposal
- Relevant subject areas (e.g., climate, education, housing)
- Helps identify which executive orders apply

#### 3. Compliance Tab

**Compliance Metrics**:
- **Compliance Score**: 0-100% alignment with executive orders
- **Status**: COMPLIANT, PARTIALLY_COMPLIANT, or NON_COMPLIANT
- **Relevant EOs**: Number of executive orders that apply

**Detailed Analysis**:
Full compliance analysis with inline citations to executive order sections.

**Citation Details**:
Each citation includes:
- **Title**: Name of the executive order
- **URL**: Link to the full document
- **Excerpt**: Relevant text snippet
- **Additional Properties**:
  - EO Number
  - Effective Date
  - Page Number
  - Document Type
- **Text Regions**: Character ranges for precise location

**Relevant Executive Orders**:
List of applicable EOs with:
- Name and relevance score
- Key requirements from each EO
- Expandable sections for details

**Violations**:
- Red boxes highlight compliance violations
- Specific requirement not met
- Executive order reference
- Recommended action

**Warnings**:
- Yellow boxes show potential issues
- Items requiring clarification
- May not be critical but need attention

#### 4. Risk Analysis Tab

**Risk Metrics**:
- **Overall Risk Score**: 0-100 (higher = lower risk)
- **Risk Level**: LOW, MEDIUM, MEDIUM-HIGH, or HIGH
- **Confidence**: How certain the AI is about the analysis
- **Notification Required**: Whether attorney review is needed

**Risk Breakdown**:
Three risk components shown:
- **Compliance Risk (60% weight)**: Legal/regulatory alignment
- **Quality Risk (25% weight)**: Document quality and clarity
- **Completeness Risk (15% weight)**: Required sections present

**Risk Factors**:
- Specific issues increasing risk
- Severity level (🔴 high, 🟡 medium)
- Description of each factor

**Recommendations**:
- Actionable steps to improve the proposal
- Priority level (critical, high, medium)
- Specific guidance for each recommendation

**Referenced Executive Orders**:
- Same EOs from Compliance tab
- Shows which orders were considered in risk calculation
- Key requirements and citations

#### 5. Email Tab

**Notification Status**:
- Whether an email notification was sent
- Email recipient and sender
- Priority level (Normal, High, Critical)
- Timestamp when sent

**Why Email?**:
Emails are automatically sent when:
- Risk Score < 75% (Medium threshold)
- Risk Level is "High" or "Medium-High"
- Attorney review is required

**Email Contents**:
- Document summary
- Risk and compliance scores
- Key violations and warnings
- Link to full results dashboard

---

## Knowledge Base

### Browsing Executive Orders

Click **📚 Knowledge Base** to explore available executive orders and sample proposals.

**Executive Orders Section**:
- List of all indexed executive orders
- Search and filter capabilities
- Document preview
- **Download PDF** button for each document

**Sample Proposals Section**:
- Example grant proposals
- Reference documents
- Templates for your own submissions

### Adding Documents to Knowledge Base

**Administrators Only**:

1. Place PDF files in `knowledge_base/executive_orders/`
2. Run indexing script:
   ```bash
   python scripts/index_knowledge_base.py --input knowledge_base/executive_orders
   ```
3. Documents will be available in 5-10 minutes

---

## Best Practices

### Writing Compliant Proposals

1. **Reference Executive Orders Explicitly**
   - Mention specific EO numbers (e.g., "In compliance with EO 14008...")
   - Quote relevant sections
   - Demonstrate understanding of requirements

2. **Be Specific and Detailed**
   - Provide concrete examples
   - Include measurable goals
   - Document how you'll meet requirements

3. **Include Required Sections**
   - Project description
   - Budget breakdown
   - Timeline and milestones
   - Stakeholder information
   - Impact assessment

4. **Use Clear Language**
   - Avoid jargon and acronyms (or define them)
   - Write in active voice
   - Use headers and bullet points

### Improving Your Scores

**To Improve Compliance Score**:
- Address all violations shown in results
- Add missing information
- Cite relevant executive order sections
- Demonstrate clear alignment

**To Improve Risk Score**:
- Increase document length (aim for 2000+ words)
- Add more detail to key sections
- Include budget and timeline
- Address all warnings

**To Improve Confidence Score**:
- Be more specific and detailed
- Remove ambiguous language
- Provide concrete examples
- Include supporting documentation

### When to Seek Attorney Review

**Always seek review if**:
- Risk Score < 75%
- Compliance violations found
- Confidence Score < 70%
- High-risk label assigned
- Email notification sent

**Good practice to seek review if**:
- First time applying for this type of grant
- Complex legal requirements
- Large funding amount (>$100K)
- Novel project approach

---

## Frequently Asked Questions

### General Questions

**Q: How long does analysis take?**
A: Typically 1-3 minutes per document. Scanned PDFs may take longer due to OCR processing.

**Q: Is my data secure?**
A: Yes. All data is encrypted in transit and at rest. Documents are processed in Microsoft Azure cloud with enterprise-grade security.

**Q: Can I analyze multiple documents at once?**
A: Currently, the system processes one document at a time. Batch processing may be available in future versions.

**Q: What happens to my documents after analysis?**
A: Documents are retained for 30 days for your reference, then automatically deleted. You can download results before deletion.

### Score Interpretation

**Q: What is a "good" compliance score?**
A: 
- 90-100% = Excellent, proceed with confidence
- 70-89% = Good, minor improvements recommended
- 50-69% = Fair, significant revisions needed
- Below 50% = Poor, major rework required

**Q: Why is my confidence score low?**
A: Low confidence means the AI is uncertain about its analysis. Common reasons:
- Ambiguous or unclear language
- Missing information
- Complex legal requirements
- Novel project type not in training data

**Q: How is the risk score calculated?**
A: Risk Score = (Compliance × 60%) + (Quality × 25%) + (Completeness × 15%)

### Compliance Issues

**Q: What if I disagree with a violation?**
A: The AI provides recommendations, but human review is required. If you believe a violation is incorrect:
1. Document your reasoning
2. Cite supporting evidence
3. Request attorney review
4. Include your justification in resubmission

**Q: Can I appeal a compliance finding?**
A: Yes. All AI-generated findings must be validated by a human attorney. The attorney review process allows for appeals and clarifications.

**Q: How often are executive orders updated?**
A: The knowledge base is updated monthly. New executive orders are typically indexed within 1-2 weeks of publication.

### Technical Issues

**Q: Upload failed - what should I do?**
A: Common solutions:
- Check file size (must be under 10 MB)
- Verify file format (PDF, DOCX, TXT only)
- Try converting scanned PDFs to searchable PDFs
- Contact support if issue persists

**Q: Analysis is taking too long**
A: If analysis exceeds 5 minutes:
1. Refresh the page (progress may not have updated)
2. Check your internet connection
3. Try a smaller file
4. Contact support if issue persists

**Q: Results look incorrect**
A: If results seem wrong:
1. Verify your document uploaded correctly
2. Check if text extracted properly (view summary tab)
3. Report issue to support with document ID
4. Seek human attorney review

---

## Getting Help

### Support Channels

**Email**: support@yourdomain.com  
**Documentation**: https://docs.yourdomain.com  
**Status Page**: https://status.yourdomain.com

### Reporting Issues

When reporting issues, please include:
- Document ID (found in email notification)
- Steps to reproduce
- Screenshots of error messages
- Browser and version information

---

## About This Guide

**Version**: 1.0  
**Last Updated**: November 2025  
**Feedback**: Please send suggestions to docs@yourdomain.com

---

## Legal Disclaimer

This system provides AI-generated compliance analysis for informational purposes only. All findings must be validated by a licensed attorney before final submission. The system does not constitute legal advice and should not be relied upon as the sole basis for grant proposal decisions.
