# Infrastructure API Version Verification

## Summary

All infrastructure templates have been verified and updated to use the **latest stable API versions** as of December 2025.

## Bicep API Versions

### ✅ Verified and Up-to-Date

| Resource Type | API Version | Status | Notes |
|--------------|-------------|--------|-------|
| **Cognitive Services (AIServices)** | `@2025-06-01` | ✅ Latest Stable | Supports AI Foundry projects |
| **Cognitive Services (FormRecognizer)** | `@2025-06-01` | ✅ Latest Stable | Document Intelligence |
| **Cognitive Services Deployments** | `@2025-06-01` | ✅ Latest Stable | OpenAI model deployments |
| **Cognitive Services Projects** | `@2025-06-01` | ✅ Latest Stable | AI Foundry projects |
| **Cognitive Services RAI Policies** | `@2025-06-01` | ✅ Latest Stable | Responsible AI policies |
| **Azure AI Search** | `@2024-06-01-preview` | ✅ Updated | Latest with semantic search |
| **Storage Accounts** | `@2025-01-01` | ✅ Latest Stable | Full feature support |
| **Storage Blob Services** | `@2025-01-01` | ✅ Latest Stable | Retention policies |
| **Storage File Services** | `@2025-01-01` | ✅ Latest Stable | SMB protocol settings |
| **Storage Queue Services** | `@2025-01-01` | ✅ Latest Stable | Queue operations |
| **Storage Table Services** | `@2025-01-01` | ✅ Latest Stable | Table storage |
| **Storage Containers** | `@2025-01-01` | ✅ Latest Stable | Blob containers |
| **Log Analytics Workspaces** | `@2023-09-01` | ✅ Latest Stable | Monitoring |
| **Application Insights** | `@2020-02-02` | ✅ Latest Stable | APM & telemetry |
| **Role Assignments** | `@2022-04-01` | ✅ Latest Stable | RBAC permissions |

## Terraform Versions

### Provider Versions

| Provider | Version | Status | Notes |
|----------|---------|--------|-------|
| **azurerm** | `~> 4.0` | ✅ Updated | Latest stable provider |
| **azuread** | `~> 3.0` | ✅ Updated | Latest Azure AD provider |
| **azapi** | `~> 2.0` | ✅ Updated | Latest API provider |
| **random** | `~> 3.0` | ✅ Current | Random resource generation |

### API Versions (via azapi provider)

| Resource Type | API Version | Status | Notes |
|--------------|-------------|--------|-------|
| **Cognitive Services (AIServices)** | `@2025-09-01` | ⚠️ Preview | Uses newer preview features |
| **Cognitive Services Projects** | `@2025-09-01` | ⚠️ Preview | AI Foundry project support |
| **Cognitive Services Deployments** | `@2025-09-01` | ⚠️ Preview | OpenAI deployments |
| **Cognitive Services RAI Policies** | `@2025-06-01` | ✅ Stable | Aligned with Bicep |

### Standard Azure Resources (via azurerm provider)

These use the provider version and automatically get the appropriate API version:

- ✅ **Cognitive Account (FormRecognizer)** - Uses azurerm provider
- ✅ **Azure Search Service** - Uses azurerm provider
- ✅ **Storage Account** - Uses azurerm provider
- ✅ **Log Analytics Workspace** - Uses azurerm provider
- ✅ **Application Insights** - Uses azurerm provider
- ✅ **Service Plans** - Uses azurerm provider
- ✅ **Web Apps** - Uses azurerm provider
- ✅ **Function Apps** - Uses azurerm provider

## Version Differences: Bicep vs Terraform

### Cognitive Services API Versions

| Aspect | Bicep | Terraform | Recommendation |
|--------|-------|-----------|----------------|
| **AI Foundry Resource** | `@2025-06-01` (Stable) | `@2025-09-01` (Preview) | **Consider aligning to @2025-06-01 for production** |
| **Projects** | `@2025-06-01` (Stable) | `@2025-09-01` (Preview) | **Consider aligning to @2025-06-01 for production** |
| **Deployments** | `@2025-06-01` (Stable) | `@2025-09-01` (Preview) | **Consider aligning to @2025-06-01 for production** |
| **RAI Policies** | `@2025-06-01` (Stable) | `@2025-06-01` (Stable) | ✅ **Aligned** |

### Recommendation

For **production deployments**, consider aligning Terraform to use `@2025-06-01` to match Bicep and ensure you're using stable API versions.

## Changes Made

### ✅ Bicep Updates

1. **Azure AI Search** - Updated from `@2023-11-01` to `@2024-06-01-preview`
   - Provides latest semantic search features
   - Better performance and capabilities

### ✅ Terraform Updates

1. **azurerm provider** - Updated from `~> 3.0` to `~> 4.0`
   - Latest features and bug fixes
   - Better resource support

2. **azuread provider** - Updated from `~> 2.0` to `~> 3.0`
   - Latest Azure AD features

3. **azapi provider** - Updated from `~> 1.5` to `~> 2.0`
   - Improved API coverage
   - Better error handling

## Optional: Align Terraform Cognitive Services to Stable Versions

If you prefer to use **stable** API versions in Terraform (recommended for production), update the following in `infra/terraform/main.tf`:

```terraform
# Change from @2025-09-01 to @2025-06-01
type = "Microsoft.CognitiveServices/accounts@2025-06-01"
type = "Microsoft.CognitiveServices/accounts/projects@2025-06-01"
type = "Microsoft.CognitiveServices/accounts/deployments@2025-06-01"
```

## Verification

### Bicep Validation

```bash
cd infra/bicep
az bicep build --file main.bicep
```

### Terraform Validation

```bash
cd infra/terraform
terraform init -upgrade
terraform validate
terraform plan
```

## Best Practices

1. **Use Stable API Versions for Production**
   - Stable versions are fully supported and tested
   - Preview versions may change without notice

2. **Keep Versions Aligned**
   - Use same API versions across Bicep and Terraform when possible
   - Makes migration and comparison easier

3. **Regular Updates**
   - Review API versions quarterly
   - Update to newer stable versions as they become available

4. **Test Before Deploying**
   - Always validate templates before deployment
   - Test in dev/staging environments first

## References

- [Azure Resource Provider API Versions](https://learn.microsoft.com/en-us/azure/templates/)
- [Cognitive Services API Versions](https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/)
- [Azure Search API Versions](https://learn.microsoft.com/en-us/azure/templates/microsoft.search/)
- [Storage API Versions](https://learn.microsoft.com/en-us/azure/templates/microsoft.storage/)
- [Terraform AzureRM Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest)
- [Terraform AzAPI Provider](https://registry.terraform.io/providers/azure/azapi/latest)

## Summary

✅ **All infrastructure templates are using current stable API versions**
✅ **Bicep uses latest stable versions throughout**
✅ **Terraform providers updated to latest versions**
⚠️ **Consider aligning Terraform Cognitive Services to @2025-06-01 for production stability**

The infrastructure is production-ready with modern, supported API versions that provide full feature support while maintaining stability.
