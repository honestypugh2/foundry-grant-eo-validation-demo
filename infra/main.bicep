// Main Bicep template for Grant EO Validation Demo
targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment (e.g., dev, staging, prod)')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Resource naming prefix')
param resourcePrefix string = 'grant-eo'

@description('Id of the user or app to assign application roles')
param principalId string = ''

@description('Location for Azure AI Search (override if primary region is out of capacity)')
param searchLocation string = location

// Tags for all resources
var tags = {
  'azd-env-name': environmentName
  'project': 'grant-eo-validation'
  'managed-by': 'azd'
}

// Resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: 'rg-${resourcePrefix}-${environmentName}'
  location: location
  tags: tags
}

// Deploy core infrastructure
module resources './bicep/main.bicep' = {
  name: 'resources'
  scope: rg
  params: {
    location: location
    environmentName: environmentName
    resourcePrefix: resourcePrefix
    principalId: principalId
    searchLocation: searchLocation
    tags: tags
  }
}

// Outputs
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = rg.name

// AI Foundry
output AZURE_OPENAI_ENDPOINT string = resources.outputs.openAIEndpoint
output AZURE_OPENAI_DEPLOYMENT_NAME string = resources.outputs.openAIDeploymentName
output AZURE_AI_FOUNDRY_RESOURCE_NAME string = resources.outputs.aiFoundryResourceName
output AZURE_AI_PROJECT_NAME string = resources.outputs.aiProjectName
output AZURE_AI_PROJECT_ENDPOINT string = resources.outputs.projectEndpoint
output AZURE_AI_FOUNDRY_RESOURCE_ID string = resources.outputs.aiFoundryResourceId
output AZURE_AI_FOUNDRY_PROJECT_ID string = resources.outputs.aiFoundryProjectId

// Search
output AZURE_SEARCH_ENDPOINT string = resources.outputs.searchEndpoint
output AZURE_SEARCH_INDEX_NAME string = resources.outputs.searchIndexName

// Document Intelligence
output AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT string = resources.outputs.documentIntelligenceEndpoint

// Storage
output AZURE_STORAGE_ACCOUNT_NAME string = resources.outputs.storageAccountName
output AZURE_STORAGE_CONTAINER_NAME string = resources.outputs.storageContainerName

// Azure Functions
output GRANT_COMPLIANCE_FUNCTION_NAME string = resources.outputs.grantComplianceFunctionName
output GRANT_COMPLIANCE_FUNCTION_URI string = resources.outputs.grantComplianceFunctionUri
output EMAIL_NOTIFIER_FUNCTION_NAME string = resources.outputs.emailNotifierFunctionName
output EMAIL_NOTIFIER_FUNCTION_URI string = resources.outputs.emailNotifierFunctionUri

// App Services (run locally)
output BACKEND_URI string = resources.outputs.backendUri
output FRONTEND_URI string = resources.outputs.frontendUri
