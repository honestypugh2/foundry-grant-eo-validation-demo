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
param openAIModelVersion string = '2024-08-06'

@description('Azure Search index name')
param searchIndexName string = 'grant-compliance-index'

@description('Storage container name')
param storageContainerName string = 'documents'

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
    // Required for Foundry resource to support projects
    allowProjectManagement: true
    // Custom subdomain is required for Foundry
    customSubDomainName: '${resourcePrefix}-${environmentName}-${uniqueSuffix}'
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
    disableLocalAuth: false  // Ensure API key authentication is enabled
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
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
    raiPolicyName: 'Microsoft.DefaultV2'  // System-managed policy
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
  location: location
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
    publicNetworkAccess: 'Disabled'
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
// Azure Function App (for email notifications and document processing)
// ============================================================================
// Commented out to avoid quota issues - deploy manually if needed

// Function App Storage Account (separate from document storage)
// resource functionStorageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
//   name: '${abbrs.storageStorageAccounts}fn${replace(resourcePrefix, '-', '')}${uniqueSuffix}'
//   location: location
//   tags: tags
//   kind: 'StorageV2'
//   sku: {
//     name: 'Standard_LRS'
//   }
//   properties: {
//     accessTier: 'Hot'
//     minimumTlsVersion: 'TLS1_2'
//     supportsHttpsTrafficOnly: true
//     allowBlobPublicAccess: false
//   }
// }

// Function App Plan (Consumption)
// resource functionAppPlan 'Microsoft.Web/serverfarms@2023-01-01' = {
//   name: '${abbrs.webServerFarms}fn-${resourcePrefix}-${environmentName}'
//   location: location
//   tags: tags
//   sku: {
//     name: 'Y1'
//     tier: 'Dynamic'
//   }
//   properties: {
//     reserved: true // Linux
//   }
//   kind: 'functionapp,linux'
// }

// Function App (Email Notifier)
// resource emailNotifierFunction 'Microsoft.Web/sites@2023-01-01' = {
//   name: '${abbrs.webSitesFunctions}email-${resourcePrefix}-${environmentName}'
//   location: location
//   tags: union(tags, { 'azd-service-name': 'email-notifier' })
//   kind: 'functionapp,linux'
//   identity: {
//     type: 'SystemAssigned'
//   }
//   properties: {
//     serverFarmId: functionAppPlan.id
//     httpsOnly: true
//     siteConfig: {
//       linuxFxVersion: 'PYTHON|3.11'
//       ftpsState: 'Disabled'
//       minTlsVersion: '1.2'
//       appSettings: [
//         {
//           name: 'AzureWebJobsStorage'
//           value: 'DefaultEndpointsProtocol=https;AccountName=${functionStorageAccount.name};AccountKey=${functionStorageAccount.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'
//         }
//         {
//           name: 'FUNCTIONS_EXTENSION_VERSION'
//           value: '~4'
//         }
//         {
//           name: 'FUNCTIONS_WORKER_RUNTIME'
//           value: 'python'
//         }
//         {
//           name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
//           value: applicationInsights.properties.ConnectionString
//         }
//         {
//           name: 'USE_MANAGED_IDENTITY'
//           value: 'true'
//         }
//       ]
//     }
//   }
// }

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

// Search Index Data Contributor role
var searchIndexDataContributorRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8ebe5a00-799e-43f5-93ac-243d3dce84a7')

resource searchRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  scope: searchService
  name: guid(searchService.id, principalId, searchIndexDataContributorRole)
  properties: {
    roleDefinitionId: searchIndexDataContributorRole
    principalId: principalId
    principalType: 'User'
  }
}

// Storage Blob Data Contributor role
var storageBlobDataContributorRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')

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

// Function App outputs commented out - no function apps deployed due to quota
// output emailNotifierFunctionName string = emailNotifierFunction.name
// output emailNotifierFunctionUri string = 'https://${emailNotifierFunction.properties.defaultHostName}'

// App Service outputs commented out - no app services deployed due to quota
// output backendUri string = 'https://${backendAppService.properties.defaultHostName}'
// output frontendUri string = 'https://${frontendAppService.properties.defaultHostName}'
output backendUri string = 'Run locally: http://localhost:8000'
output frontendUri string = 'Run locally: http://localhost:3000'

output aiFoundryResourceId string = aiFoundryResource.id
output aiFoundryProjectId string = aiFoundryProject.id
output searchServiceId string = searchService.id
output storageAccountId string = storageAccount.id
// output keyVaultId string = keyVault.id
