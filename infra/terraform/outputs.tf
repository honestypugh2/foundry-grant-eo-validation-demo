# Outputs for Grant EO Validation Demo

output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "location" {
  description = "Azure region where resources are deployed"
  value       = azurerm_resource_group.main.location
}

# AI Foundry Outputs
output "azure_openai_endpoint" {
  description = "Endpoint for Azure OpenAI service"
  value       = jsondecode(data.azapi_resource.ai_foundry_resource_data.output).properties.endpoint
}

output "azure_openai_deployment_name" {
  description = "Name of the Azure OpenAI deployment"
  value       = azapi_resource.openai_deployment.name
}

output "ai_foundry_resource_name" {
  description = "Name of the AI Foundry resource"
  value       = azapi_resource.ai_foundry_resource.name
}

output "ai_project_name" {
  description = "Name of the AI Foundry project"
  value       = azapi_resource.ai_foundry_project.name
}

output "document_intelligence_endpoint" {
  description = "Endpoint for Azure Document Intelligence"
  value       = azurerm_cognitive_account.document_intelligence.endpoint
}

# Search Outputs
output "azure_search_endpoint" {
  description = "Endpoint for Azure AI Search"
  value       = "https://${azurerm_search_service.main.name}.search.windows.net"
}

output "azure_search_index_name" {
  description = "Name of the search index"
  value       = var.search_index_name
}

# Storage Outputs
output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.main.name
}

output "storage_container_name" {
  description = "Name of the blob container"
  value       = azurerm_storage_container.documents.name
}

# Key Vault Outputs (Optional - Commented out)
# output "key_vault_name" {
#   description = "Name of the Key Vault"
#   value       = azurerm_key_vault.main.name
# }

# output "key_vault_uri" {
#   description = "URI of the Key Vault"
#   value       = azurerm_key_vault.main.vault_uri
# }

# Monitoring Outputs
output "log_analytics_workspace_id" {
  description = "Resource ID of the Log Analytics Workspace"
  value       = azurerm_log_analytics_workspace.main.id
}

output "application_insights_name" {
  description = "Name of Application Insights"
  value       = azurerm_application_insights.main.name
}

output "application_insights_connection_string" {
  description = "Connection string for Application Insights"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

output "application_insights_instrumentation_key" {
  description = "Instrumentation key for Application Insights"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

# Function App Outputs
output "email_notifier_function_name" {
  description = "Name of the email notifier function app"
  value       = azurerm_linux_function_app.email_notifier.name
}

output "email_notifier_function_url" {
  description = "URL of the email notifier function app"
  value       = "https://${azurerm_linux_function_app.email_notifier.default_hostname}"
}

# App Service Outputs
output "backend_url" {
  description = "URL of the backend app service"
  value       = "https://${azurerm_linux_web_app.backend.default_hostname}"
}

output "frontend_url" {
  description = "URL of the frontend app service"
  value       = "https://${azurerm_linux_web_app.frontend.default_hostname}"
}

# Identity Outputs
output "backend_principal_id" {
  description = "Principal ID of the backend app service managed identity"
  value       = azurerm_linux_web_app.backend.identity[0].principal_id
}

output "frontend_principal_id" {
  description = "Principal ID of the frontend app service managed identity"
  value       = azurerm_linux_web_app.frontend.identity[0].principal_id
}

# Resource IDs
output "ai_foundry_resource_id" {
  description = "Resource ID of the AI Foundry resource"
  value       = azapi_resource.ai_foundry_resource.id
}

output "ai_foundry_project_id" {
  description = "Resource ID of the AI Foundry project"
  value       = azapi_resource.ai_foundry_project.id
}

output "search_service_id" {
  description = "Resource ID of the search service"
  value       = azurerm_search_service.main.id
}

output "storage_account_id" {
  description = "Resource ID of the storage account"
  value       = azurerm_storage_account.main.id
}

# output "key_vault_id" {
#   description = "Resource ID of the Key Vault"
#   value       = azurerm_key_vault.main.id
# }

# Environment Variables for .env file
output "env_file_content" {
  description = "Content for .env file"
  value       = <<-EOT
    # Azure AI Foundry
    AZURE_OPENAI_ENDPOINT=${jsondecode(data.azapi_resource.ai_foundry_resource_data.output).properties.endpoint}
    AZURE_OPENAI_DEPLOYMENT_NAME=${azapi_resource.openai_deployment.name}
    AZURE_OPENAI_API_VERSION=2024-10-01-preview
    AZURE_AI_FOUNDRY_RESOURCE_NAME=${azapi_resource.ai_foundry_resource.name}
    AZURE_AI_PROJECT_NAME=${azapi_resource.ai_foundry_project.name}
    AZURE_AI_FOUNDRY_RESOURCE_ID=${azapi_resource.ai_foundry_resource.id}
    AZURE_AI_FOUNDRY_PROJECT_ID=${azapi_resource.ai_foundry_project.id}
    
    # Azure AI Search
    AZURE_SEARCH_ENDPOINT=https://${azurerm_search_service.main.name}.search.windows.net
    AZURE_SEARCH_INDEX_NAME=${var.search_index_name}
    
    # Azure Document Intelligence
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=${azurerm_cognitive_account.document_intelligence.endpoint}
    
    # Azure Storage
    AZURE_STORAGE_ACCOUNT_NAME=${azurerm_storage_account.main.name}
    AZURE_STORAGE_CONTAINER_NAME=${azurerm_storage_container.documents.name}
    
    # Azure Key Vault (Optional - Commented out)
    # AZURE_KEY_VAULT_NAME=${azurerm_key_vault.main.name}
    # AZURE_KEY_VAULT_URI=${azurerm_key_vault.main.vault_uri}
    
    # Azure Monitor
    APPLICATIONINSIGHTS_CONNECTION_STRING=${azurerm_application_insights.main.connection_string}
    APPLICATIONINSIGHTS_INSTRUMENTATION_KEY=${azurerm_application_insights.main.instrumentation_key}
    
    # Use Managed Identity
    USE_MANAGED_IDENTITY=true
    
    # Backend and Frontend URLs
    BACKEND_URL=https://${azurerm_linux_web_app.backend.default_hostname}
    FRONTEND_URL=https://${azurerm_linux_web_app.frontend.default_hostname}
  EOT
  sensitive   = false
}
