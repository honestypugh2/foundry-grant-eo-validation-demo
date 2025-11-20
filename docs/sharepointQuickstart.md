# SharePoint Integration - Quick Start

> **For complete setup instructions and advanced features, see [SharePoint Integration Guide](sharepointIntegration.md)**

## What is This?

**Optional feature** that allows the Grant Compliance System to access documents directly from SharePoint instead of (or in addition to) local file storage.

## Why Use SharePoint?

✅ **Enterprise Document Management** - Centralized storage  
✅ **Version Control** - Track document changes  
✅ **Access Control** - Manage permissions  
✅ **Collaboration** - Multiple users can work together  
✅ **Automatic Sync** - Real-time document updates  

## Do I Need This?

**No, SharePoint is completely optional.**

- ✅ Use SharePoint if: Your organization already uses SharePoint for document management
- ✅ Skip SharePoint if: You prefer local file storage or don't have SharePoint access

The system works perfectly fine without SharePoint!

## Quick Setup (5 Steps)

### 1. Create Azure AD App

```bash
# In Azure Portal:
# 1. Go to Azure Active Directory > App registrations
# 2. Create new registration
# 3. Save Client ID and Tenant ID
# 4. Create client secret, save it immediately
```

### 2. Grant Permissions

```bash
# In your app registration:
# 1. API Permissions > Add permission > Microsoft Graph
# 2. Add: Sites.Read.All, Files.Read.All (Application permissions)
# 3. Grant admin consent
```

### 3. Configure SharePoint

```bash
# 1. Note your SharePoint site URL
# 2. Add your app to site permissions
# 3. Create document libraries: GrantProposals, ExecutiveOrders
```

### 4. Add to .env

```bash
# Copy these to your .env file:
SHAREPOINT_SITE_URL=https://yourtenant.sharepoint.com/sites/yoursite
SHAREPOINT_CLIENT_ID=your_client_id
SHAREPOINT_CLIENT_SECRET=your_client_secret
AZURE_TENANT_ID=your_tenant_id
```

### 5. Test It

```bash
# Run the test script:
python scripts/sharepoint_integration.py

# If successful, you'll see:
# ✅ Configuration validated successfully!
# ✅ Successfully connected to SharePoint!
```

## Using SharePoint in Your Code

### Basic Search

```python
from scripts.sharepoint_integration import SharePointDocumentAccess

sp = SharePointDocumentAccess()

# Search for grant proposals
results = sp.search_sharepoint_documents(
    query="affordable housing grants",
    document_library="GrantProposals"
)

for doc in results:
    print(doc['content'])
```

### Get Document Content

```python
# Retrieve specific document
content = sp.get_document_content(
    "https://tenant.sharepoint.com/sites/site/Documents/proposal.pdf"
)
```

### List Libraries

```python
# See what's available
libraries = sp.list_document_libraries()
print(libraries)  # ['GrantProposals', 'ExecutiveOrders', 'Documents']
```

## Integration with Agents

### Enable SharePoint in Compliance Agent

```python
from agents.compliance_validator_agent import ComplianceValidatorAgent

# Initialize with SharePoint enabled
agent = ComplianceValidatorAgent(
    use_azure=True,
    use_sharepoint=True  # Enable SharePoint access
)

# Agent will now search SharePoint for executive orders
result = agent.validate_compliance(proposal_text)
```

## Troubleshooting

### "Configuration incomplete" Error

**Solution**: Add all required variables to `.env` file

### "Authentication failed" Error

**Solution**: Check Client ID, Secret, and Tenant ID are correct

### "Site not found" Error

**Solution**: Verify SharePoint site URL is complete and accessible

### "No module named 'azure.ai.projects'" Error

**Solution**: Install dependencies
```bash
pip install azure-ai-projects azure-identity
```

## Full Documentation

For detailed setup, advanced features, and automatic document indexing with webhooks, see:
- **[SharePoint Integration Guide](sharepointIntegration.md)** - Complete integration documentation with automatic indexing setup
- **[Complete Guide](docs/SHAREPOINT_INTEGRATION.md)** - Full documentation
- **[Microsoft Docs](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/sharepoint)** - Official reference

## FAQ

**Q: Is SharePoint required?**  
A: No, it's completely optional. The system works with local files.

**Q: Can I use both SharePoint and local files?**  
A: Yes! The system can search both sources.

**Q: Do I need SharePoint Online or on-premises?**  
A: SharePoint Online (Microsoft 365) is required.

**Q: What SharePoint plan do I need?**  
A: Any Microsoft 365 plan with SharePoint Online.

**Q: Can I test without SharePoint?**  
A: Yes, use the demo mode with local files.

---

**Remember**: SharePoint integration is optional. Use it if it fits your needs, skip it if you prefer local storage!
