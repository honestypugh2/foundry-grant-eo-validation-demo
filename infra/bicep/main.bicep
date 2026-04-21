// Core resources for Grant EO Validation Demo
@description('Primary location for all resources')
param location string = resourceGroup().location

@description('Environment name')
param environmentName string

@description('Resource naming prefix')
param resourcePrefix string

@description('Principal ID for role assignments')
param principalId string = ''

@description('Tags to apply to all resources')
param tags object = {}

@description('Azure OpenAI deployment name')
param openAIDeploymentName string = 'gpt-4o'

@description('Azure OpenAI model version')
param openAIModelVersion string = '2024-11-20'

@description('Azure Search index name')
param searchIndexName string = 'grant-compliance-index'

@description('Storage container name')
param storageContainerName string = 'documents'

@description('Location for Azure AI Search (override if primary region is out of capacity)')
param searchLocation string = location

// Generate unique suffix for globally unique resources
var uniqueSuffix = uniqueString(resourceGroup().id)
var abbrs = loadJsonContent('abbreviations.json')

// ============================================================================
// Azure AI Foundry Resource (AIServices account)
// ============================================================================

resource aiFoundryResource 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: '${abbrs.cognitiveServicesAccounts}${resourcePrefix}-${environmentName}'
  location: location
  tags: tags
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    // Custom subdomain must match the resource name for new Foundry experience
    customSubDomainName: '${abbrs.cognitiveServicesAccounts}${resourcePrefix}-${environmentName}'
    // CRITICAL: This property is required for the new Foundry experience
    allowProjectManagement: true
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
      bypass: 'AzureServices'
    }
    disableLocalAuth: false
  }
}

// ============================================================================
// Azure AI Foundry Project
// ============================================================================

resource aiFoundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  parent: aiFoundryResource
  name: '${resourcePrefix}-project-${environmentName}'
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: 'Grant EO Validation Project'
    description: 'AI Foundry project for grant executive order validation and compliance checking'
  }
}

// ============================================================================
// RAI (Responsible AI) Policies
// ============================================================================
// Note: Microsoft.Default and Microsoft.DefaultV2 are system-managed policies
// that exist automatically. They cannot be created or updated via templates.
// To use them, simply reference them by name in your deployments.
// For custom RAI policies, create resources with unique names (not Microsoft.*).

// ============================================================================
// Azure OpenAI Deployment (on Foundry Resource)
// ============================================================================

resource openAIDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: aiFoundryResource
  name: openAIDeploymentName
  sku: {
    name: 'GlobalStandard'
    capacity: 110
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: openAIDeploymentName
      version: openAIModelVersion
    }
    raiPolicyName: 'Microsoft.Default'
  }
}

// ============================================================================
// Azure Document Intelligence
// ============================================================================

resource documentIntelligence 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: '${abbrs.cognitiveServicesFormRecognizer}${resourcePrefix}-${environmentName}'
  location: location
  tags: tags
  kind: 'FormRecognizer'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: 'di-${resourcePrefix}-${environmentName}-${uniqueSuffix}'
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false  // Ensure API key authentication is enabled
  }
}

// ============================================================================
// Azure AI Search
// ============================================================================

resource searchService 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: '${abbrs.searchSearchServices}${resourcePrefix}-${environmentName}-${uniqueSuffix}'
  location: searchLocation
  tags: tags
  sku: {
    name: 'basic'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    semanticSearch: 'free'
    disableLocalAuth: false  // Ensure API key authentication is enabled
  }
}

// ============================================================================
// Storage Account
// ============================================================================

resource storageAccount 'Microsoft.Storage/storageAccounts@2025-01-01' = {
  name: '${abbrs.storageStorageAccounts}${replace(resourcePrefix, '-', '')}${uniqueSuffix}'
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_RAGRS'
  }
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    largeFileSharesState: 'Enabled'
    publicNetworkAccess: 'Enabled'
    allowCrossTenantReplication: false
    defaultToOAuthAuthentication: false
    dnsEndpointType: 'Standard'
    networkAcls: {
      bypass: 'AzureServices'
      virtualNetworkRules: []
      ipRules: []
      defaultAction: 'Allow'
    }
  }
}

// Blob service with retention policies
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2025-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    deleteRetentionPolicy: {
      allowPermanentDelete: false
      enabled: true
      days: 7
    }
    cors: {
      corsRules: []
    }
  }
}

// File service
resource fileService 'Microsoft.Storage/storageAccounts/fileServices@2025-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    protocolSettings: {
      smb: {}
    }
    cors: {
      corsRules: []
    }
    shareDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}

// Queue service
resource queueService 'Microsoft.Storage/storageAccounts/queueServices@2025-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    cors: {
      corsRules: []
    }
  }
}

// Table service
resource tableService 'Microsoft.Storage/storageAccounts/tableServices@2025-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    cors: {
      corsRules: []
    }
  }
}

// Documents container
resource documentsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2025-01-01' = {
  parent: blobService
  name: storageContainerName
  properties: {
    publicAccess: 'None'
  }
}

// ============================================================================
// Azure Key Vault (Optional - Commented out)
// ============================================================================

// resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
//   name: 'kv-${resourcePrefix}-${take(uniqueSuffix, 8)}'
//   location: location
//   tags: tags
//   properties: {
//     sku: {
//       family: 'A'
//       name: 'standard'
//     }
//     tenantId: subscription().tenantId
//     enableRbacAuthorization: true
//     enabledForDeployment: false
//     enabledForDiskEncryption: false
//     enabledForTemplateDeployment: false
//     publicNetworkAccess: 'Enabled'
//     enableSoftDelete: true
//     softDeleteRetentionInDays: 7
//     networkAcls: {
//       defaultAction: 'Allow'
//       bypass: 'AzureServices'
//     }
//   }
// }

// Key Vault Secrets Officer role for user
// var keyVaultSecretsOfficerRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7')

// resource keyVaultUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
//   scope: keyVault
//   name: guid(keyVault.id, principalId, keyVaultSecretsOfficerRole)
//   properties: {
//     roleDefinitionId: keyVaultSecretsOfficerRole
//     principalId: principalId
//     principalType: 'User'
//   }
// }

// ============================================================================
// Azure Monitor - Log Analytics Workspace
// ============================================================================

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${abbrs.operationalInsightsWorkspaces}${resourcePrefix}-${environmentName}'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Application Insights
resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${abbrs.insightsComponents}${resourcePrefix}-${environmentName}'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// ============================================================================
// Azure Function App — Grant Compliance Host (Flex Consumption + DTS)
// Agent Framework durable agents hosted on serverless compute
// ============================================================================

@description('Deploy Azure Functions for durable agent hosting')
param deployFunctionApps bool = true

// Dedicated storage account for Azure Functions runtime
resource functionStorageAccount 'Microsoft.Storage/storageAccounts@2025-01-01' = if (deployFunctionApps) {
  name: '${abbrs.storageStorageAccounts}fn${replace(resourcePrefix, '-', '')}${take(uniqueSuffix, 6)}'
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
  }
}

// Blob service on function storage account
resource functionBlobService 'Microsoft.Storage/storageAccounts/blobServices@2025-01-01' = if (deployFunctionApps) {
  parent: functionStorageAccount
  name: 'default'
}

// Deployment package container for Flex Consumption
resource deploymentContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2025-01-01' = if (deployFunctionApps) {
  parent: functionBlobService
  name: 'deploymentpackage'
  properties: {
    publicAccess: 'None'
  }
}

// Flex Consumption plan for grant compliance host
resource grantCompliancePlan 'Microsoft.Web/serverfarms@2024-04-01' = if (deployFunctionApps) {
  name: '${abbrs.webServerFarms}compliance-${resourcePrefix}-${environmentName}'
  location: location
  tags: tags
  sku: {
    tier: 'FlexConsumption'
    name: 'FC1'
  }
  kind: 'functionapp,linux'
  properties: {
    reserved: true
  }
}

// Durable Task Scheduler for durable agent state
resource durableTaskScheduler 'Microsoft.DurableTask/schedulers@2025-04-01-preview' = if (deployFunctionApps) {
  name: 'dts-${resourcePrefix}-${environmentName}'
  location: location
  tags: tags
  properties: {
    ipAllowlist: []
    sku: {
      name: 'Consumption'
    }
  }
}

resource durableTaskHub 'Microsoft.DurableTask/schedulers/taskHubs@2025-04-01-preview' = if (deployFunctionApps) {
  parent: durableTaskScheduler
  name: 'default'
}

// Grant Compliance Host function app (durable agents)
resource grantComplianceFunction 'Microsoft.Web/sites@2024-04-01' = if (deployFunctionApps) {
  name: '${abbrs.webSitesFunctions}compliance-${resourcePrefix}-${environmentName}'
  location: location
  tags: union(tags, { 'azd-service-name': 'grant-compliance-host' })
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: grantCompliancePlan.id
    httpsOnly: true
    functionAppConfig: {
      deployment: {
        storage: {
          type: 'blobContainer'
          value: '${functionStorageAccount.properties.primaryEndpoints.blob}deploymentpackage'
          authentication: {
            type: 'SystemAssignedIdentity'
          }
        }
      }
      scaleAndConcurrency: {
        maximumInstanceCount: 100
        instanceMemoryMB: 2048
      }
      runtime: {
        name: 'python'
        version: '3.11'
      }
    }
    siteConfig: {
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appSettings: [
        { name: 'AzureWebJobsStorage__accountName', value: functionStorageAccount.name }
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: applicationInsights.properties.ConnectionString }
        { name: 'AZURE_OPENAI_ENDPOINT', value: aiFoundryResource.properties.endpoint }
        { name: 'AZURE_OPENAI_DEPLOYMENT_NAME', value: openAIDeployment.name }
        { name: 'AZURE_OPENAI_API_VERSION', value: '2024-12-01-preview' }
        { name: 'AZURE_AI_FOUNDRY_PROJECT_ENDPOINT', value: aiFoundryProject.properties.endpoints['AI Foundry API'] }
        { name: 'AZURE_SEARCH_ENDPOINT', value: 'https://${searchService.name}.search.windows.net' }
        { name: 'AZURE_SEARCH_INDEX_NAME', value: searchIndexName }
        { name: 'AI_SEARCH_QUERY_TYPE', value: 'simple' }
        { name: 'USE_AZURE', value: 'true' }
        { name: 'USE_MANAGED_IDENTITY', value: 'true' }
      ]
    }
  }
}

// Email Notifier function app (shares Flex Consumption plan)
resource emailNotifierFunction 'Microsoft.Web/sites@2024-04-01' = if (deployFunctionApps) {
  name: '${abbrs.webSitesFunctions}email-${resourcePrefix}-${environmentName}'
  location: location
  tags: union(tags, { 'azd-service-name': 'email-notifier' })
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: grantCompliancePlan.id
    httpsOnly: true
    functionAppConfig: {
      deployment: {
        storage: {
          type: 'blobContainer'
          value: '${functionStorageAccount.properties.primaryEndpoints.blob}deploymentpackage'
          authentication: {
            type: 'SystemAssignedIdentity'
          }
        }
      }
      scaleAndConcurrency: {
        maximumInstanceCount: 100
        instanceMemoryMB: 2048
      }
      runtime: {
        name: 'python'
        version: '3.11'
      }
    }
    siteConfig: {
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appSettings: [
        { name: 'AzureWebJobsStorage__accountName', value: functionStorageAccount.name }
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: applicationInsights.properties.ConnectionString }
        { name: 'USE_MANAGED_IDENTITY', value: 'true' }
      ]
    }
  }
}

// RBAC: Grant Compliance Function → OpenAI
resource complianceFunctionToOpenAI 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deployFunctionApps) {
  scope: aiFoundryResource
  name: guid(aiFoundryResource.id, grantComplianceFunction.id, cognitiveServicesOpenAIUserRole)
  properties: {
    roleDefinitionId: cognitiveServicesOpenAIUserRole
    principalId: grantComplianceFunction.identity!.principalId
    principalType: 'ServicePrincipal'
  }
}

// RBAC: Grant Compliance Function → AI Search
resource complianceFunctionToSearch 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deployFunctionApps) {
  scope: searchService
  name: guid(searchService.id, grantComplianceFunction.id, searchIndexDataContributorRole)
  properties: {
    roleDefinitionId: searchIndexDataContributorRole
    principalId: grantComplianceFunction.identity!.principalId
    principalType: 'ServicePrincipal'
  }
}

// RBAC: Grant Compliance Function → Function Storage (Blob Data Owner)
resource complianceFunctionToStorage 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deployFunctionApps) {
  scope: functionStorageAccount
  name: guid(functionStorageAccount.id, grantComplianceFunction.id, storageBlobDataOwnerRole)
  properties: {
    roleDefinitionId: storageBlobDataOwnerRole
    principalId: grantComplianceFunction.identity!.principalId
    principalType: 'ServicePrincipal'
  }
}

// RBAC: Email Notifier Function → Function Storage (Blob Data Owner)
resource emailFunctionToStorage 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deployFunctionApps) {
  scope: functionStorageAccount
  name: guid(functionStorageAccount.id, emailNotifierFunction.id, storageBlobDataOwnerRole)
  properties: {
    roleDefinitionId: storageBlobDataOwnerRole
    principalId: emailNotifierFunction.identity!.principalId
    principalType: 'ServicePrincipal'
  }
}

// RBAC: Grant Compliance Function → Function Storage (Queue Data Contributor)
resource complianceFunctionToQueue 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deployFunctionApps) {
  scope: functionStorageAccount
  name: guid(functionStorageAccount.id, grantComplianceFunction.id, storageQueueDataContributorRole)
  properties: {
    roleDefinitionId: storageQueueDataContributorRole
    principalId: grantComplianceFunction.identity!.principalId
    principalType: 'ServicePrincipal'
  }
}

// RBAC: Email Notifier Function → Function Storage (Queue Data Contributor)
resource emailFunctionToQueue 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deployFunctionApps) {
  scope: functionStorageAccount
  name: guid(functionStorageAccount.id, emailNotifierFunction.id, storageQueueDataContributorRole)
  properties: {
    roleDefinitionId: storageQueueDataContributorRole
    principalId: emailNotifierFunction.identity!.principalId
    principalType: 'ServicePrincipal'
  }
}

// RBAC: Grant Compliance Function → Function Storage (Table Data Contributor)
resource complianceFunctionToTable 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deployFunctionApps) {
  scope: functionStorageAccount
  name: guid(functionStorageAccount.id, grantComplianceFunction.id, storageTableDataContributorRole)
  properties: {
    roleDefinitionId: storageTableDataContributorRole
    principalId: grantComplianceFunction.identity!.principalId
    principalType: 'ServicePrincipal'
  }
}

// RBAC: Email Notifier Function → Function Storage (Table Data Contributor)
resource emailFunctionToTable 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deployFunctionApps) {
  scope: functionStorageAccount
  name: guid(functionStorageAccount.id, emailNotifierFunction.id, storageTableDataContributorRole)
  properties: {
    roleDefinitionId: storageTableDataContributorRole
    principalId: emailNotifierFunction.identity!.principalId
    principalType: 'ServicePrincipal'
  }
}

// ============================================================================
// App Service Plan (for optional web hosting)
// ============================================================================

// Commented out to avoid quota issues - deploy manually if needed
// resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
//   name: '${abbrs.webServerFarms}${resourcePrefix}-${environmentName}'
//   location: location
//   tags: tags
//   sku: {
//     name: 'F1'
//     tier: 'Free'
//   }
//   properties: {
//     reserved: true // Linux
//   }
//   kind: 'linux'
// }

// Backend App Service (FastAPI)
// resource backendAppService 'Microsoft.Web/sites@2023-01-01' = {
//   name: '${abbrs.webSitesAppService}backend-${resourcePrefix}-${environmentName}'
//   location: location
//   tags: union(tags, { 'azd-service-name': 'backend' })
//   kind: 'app,linux'
//   identity: {
//     type: 'SystemAssigned'
//   }
//   properties: {
//     serverFarmId: appServicePlan.id
//     httpsOnly: true
//     siteConfig: {
//       linuxFxVersion: 'PYTHON|3.12'
//       ftpsState: 'Disabled'
//       minTlsVersion: '1.2'
//       appSettings: [
//         {
//           name: 'AZURE_OPENAI_ENDPOINT'
//           value: aiFoundryResource.properties.endpoint
//         }
//         {
//           name: 'AZURE_SEARCH_ENDPOINT'
//           value: 'https://${searchService.name}.search.windows.net'
//         }
//         {
//           name: 'AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT'
//           value: documentIntelligence.properties.endpoint
//         }
//         {
//           name: 'AZURE_STORAGE_ACCOUNT_NAME'
//           value: storageAccount.name
//         }
//         {
//           name: 'USE_MANAGED_IDENTITY'
//           value: 'true'
//         }
//       ]
//     }
//   }
// }

// Frontend App Service (React/Vite)
// resource frontendAppService 'Microsoft.Web/sites@2023-01-01' = {
//   name: '${abbrs.webSitesAppService}frontend-${resourcePrefix}-${environmentName}'
//   location: location
//   tags: union(tags, { 'azd-service-name': 'frontend' })
//   kind: 'app,linux'
//   identity: {
//     type: 'SystemAssigned'
//   }
//   properties: {
//     serverFarmId: appServicePlan.id
//     httpsOnly: true
//     siteConfig: {
//       linuxFxVersion: 'NODE|20-lts'
//       ftpsState: 'Disabled'
//       minTlsVersion: '1.2'
//       appSettings: [
//         {
//           name: 'VITE_API_URL'
//           value: 'https://${backendAppService.properties.defaultHostName}'
//         }
//       ]
//     }
//   }
// }

// ============================================================================
// Role Assignments (if principalId provided)
// ============================================================================

// Azure AI User role - Required for new Foundry experience
var azureAIUserRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '53ca6127-db72-4b80-b1b0-d745d6d5456d')

resource aiUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  scope: aiFoundryResource
  name: guid(aiFoundryResource.id, principalId, azureAIUserRole)
  properties: {
    roleDefinitionId: azureAIUserRole
    principalId: principalId
    principalType: 'User'
  }
}

// Azure AI Developer role - Required for new Foundry experience
var azureAIDeveloperRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '64702f94-c441-49e6-a78b-ef80e0188fee')

resource aiDeveloperRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  scope: aiFoundryResource
  name: guid(aiFoundryResource.id, principalId, azureAIDeveloperRole)
  properties: {
    roleDefinitionId: azureAIDeveloperRole
    principalId: principalId
    principalType: 'User'
  }
}

// Cognitive Services OpenAI User role
var cognitiveServicesOpenAIUserRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')

resource openAIRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  scope: aiFoundryResource
  name: guid(aiFoundryResource.id, principalId, cognitiveServicesOpenAIUserRole)
  properties: {
    roleDefinitionId: cognitiveServicesOpenAIUserRole
    principalId: principalId
    principalType: 'User'
  }
}

// Search Index Data Contributor role - Required for reading/writing index data
var searchIndexDataContributorRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8ebe5a00-799e-43f5-93ac-243d3dce84a7')

resource searchDataRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  scope: searchService
  name: guid(searchService.id, principalId, searchIndexDataContributorRole)
  properties: {
    roleDefinitionId: searchIndexDataContributorRole
    principalId: principalId
    principalType: 'User'
  }
}

// Search Service Contributor role - Required for creating/managing indexes
var searchServiceContributorRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7ca78c08-252a-4471-8644-bb5ff32d4ba0')

resource searchServiceRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  scope: searchService
  name: guid(searchService.id, principalId, searchServiceContributorRole)
  properties: {
    roleDefinitionId: searchServiceContributorRole
    principalId: principalId
    principalType: 'User'
  }
}

// Storage Blob Data Contributor role
var storageBlobDataContributorRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')

// Storage Blob Data Owner role (required for Functions managed identity storage access)
var storageBlobDataOwnerRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b')

// Storage Queue Data Contributor role (required for Functions triggers/bindings)
var storageQueueDataContributorRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '974c5e8b-45b9-4653-ba55-5f855dd0fb88')

// Storage Table Data Contributor role (required for Functions durable task state)
var storageTableDataContributorRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3')

resource storageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  scope: storageAccount
  name: guid(storageAccount.id, principalId, storageBlobDataContributorRole)
  properties: {
    roleDefinitionId: storageBlobDataContributorRole
    principalId: principalId
    principalType: 'User'
  }
}

// Backend App Service role assignments (commented out - no app services deployed)
// resource backendToOpenAI 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
//   scope: aiFoundryResource
//   name: guid(aiFoundryResource.id, backendAppService.id, cognitiveServicesOpenAIUserRole)
//   properties: {
//     roleDefinitionId: cognitiveServicesOpenAIUserRole
//     principalId: backendAppService.identity.principalId
//     principalType: 'ServicePrincipal'
//   }
// }

// resource backendToSearch 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
//   scope: searchService
//   name: guid(searchService.id, backendAppService.id, searchIndexDataContributorRole)
//   properties: {
//     roleDefinitionId: searchIndexDataContributorRole
//     principalId: backendAppService.identity.principalId
//     principalType: 'ServicePrincipal'
//   }
// }

// resource backendToStorage 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
//   scope: storageAccount
//   name: guid(storageAccount.id, backendAppService.id, storageBlobDataContributorRole)
//   properties: {
//     roleDefinitionId: storageBlobDataContributorRole
//     principalId: backendAppService.identity.principalId
//     principalType: 'ServicePrincipal'
//   }
// }

// ============================================================================
// Outputs
// ============================================================================

output openAIEndpoint string = aiFoundryResource.properties.endpoint
output openAIDeploymentName string = openAIDeployment.name
output aiFoundryResourceName string = aiFoundryResource.name
output aiProjectName string = aiFoundryProject.name
// Use AI Foundry API endpoint for new Foundry experience
output projectEndpoint string = aiFoundryProject.properties.endpoints['AI Foundry API']

output documentIntelligenceEndpoint string = documentIntelligence.properties.endpoint

output searchEndpoint string = 'https://${searchService.name}.search.windows.net'
output searchIndexName string = searchIndexName

output storageAccountName string = storageAccount.name
output storageContainerName string = storageContainerName

// output keyVaultName string = keyVault.name
// output keyVaultUri string = keyVault.properties.vaultUri

output logAnalyticsWorkspaceId string = logAnalyticsWorkspace.id
output applicationInsightsName string = applicationInsights.name
output applicationInsightsConnectionString string = applicationInsights.properties.ConnectionString
output applicationInsightsInstrumentationKey string = applicationInsights.properties.InstrumentationKey

// Function App outputs
output grantComplianceFunctionName string = deployFunctionApps ? grantComplianceFunction.name : ''
output grantComplianceFunctionUri string = deployFunctionApps ? 'https://${grantComplianceFunction.properties.defaultHostName}' : ''
output emailNotifierFunctionName string = deployFunctionApps ? emailNotifierFunction.name : ''
output emailNotifierFunctionUri string = deployFunctionApps ? 'https://${emailNotifierFunction.properties.defaultHostName}' : ''
output durableTaskSchedulerName string = deployFunctionApps ? durableTaskScheduler.name : ''

// App Service outputs (not deployed — run locally)
output backendUri string = 'Run locally: http://localhost:8000'
output frontendUri string = 'Run locally: http://localhost:3000'

output aiFoundryResourceId string = aiFoundryResource.id
output aiFoundryProjectId string = aiFoundryProject.id
output searchServiceId string = searchService.id
output storageAccountId string = storageAccount.id
// output keyVaultId string = keyVault.id
