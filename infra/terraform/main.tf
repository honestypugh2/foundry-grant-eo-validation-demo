# Main Terraform configuration for Grant EO Validation Demo

# Data sources
data "azurerm_client_config" "current" {}

# Generate unique suffix for globally unique resource names
resource "random_string" "unique_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Local variables
locals {
  resource_group_name = "rg-${var.resource_prefix}-${var.environment_name}"
  unique_suffix       = random_string.unique_suffix.result

  common_tags = merge(
    var.tags,
    {
      "azd-env-name" = var.environment_name
      "project"      = "grant-eo-validation"
      "managed-by"   = "terraform"
    }
  )
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = local.resource_group_name
  location = var.location
  tags     = local.common_tags
}

# ============================================================================
# Azure AI Foundry Resource (AIServices account with project management)
# ============================================================================

# Foundry Resource using azapi provider for full control
resource "azapi_resource" "ai_foundry_resource" {
  type      = "Microsoft.CognitiveServices/accounts@2025-06-01"
  name      = "cog-${var.resource_prefix}-${var.environment_name}"
  parent_id = azurerm_resource_group.main.id
  location  = azurerm_resource_group.main.location

  body = jsonencode({
    kind = "AIServices"
    sku = {
      name = "S0"
    }
    identity = {
      type = "SystemAssigned"
    }
    properties = {
      # Required for Foundry resource to support projects
      allowProjectManagement = true
      # Custom subdomain is required for Foundry
      customSubDomainName = "${var.resource_prefix}-${var.environment_name}-${local.unique_suffix}"
      publicNetworkAccess = "Enabled"
      networkAcls = {
        defaultAction = "Allow"
      }
      disableLocalAuth = false # Ensure API key authentication is enabled
    }
  })

  tags = jsonencode(local.common_tags)

  schema_validation_enabled = false
}

# Helper data source to extract resource properties
data "azapi_resource" "ai_foundry_resource_data" {
  type        = "Microsoft.CognitiveServices/accounts@2025-06-01"
  resource_id = azapi_resource.ai_foundry_resource.id

  depends_on = [azapi_resource.ai_foundry_resource]
}

# ============================================================================
# Azure AI Foundry Project
# ============================================================================

resource "azapi_resource" "ai_foundry_project" {
  type      = "Microsoft.CognitiveServices/accounts/projects@2025-06-01"
  name      = "${var.resource_prefix}-project-${var.environment_name}"
  parent_id = azapi_resource.ai_foundry_resource.id
  location  = azurerm_resource_group.main.location

  body = jsonencode({
    identity = {
      type = "SystemAssigned"
    }
    properties = {
      displayName = "Grant EO Validation Project"
      description = "AI Foundry project for grant executive order validation and compliance checking"
    }
  })

  tags = jsonencode(local.common_tags)

  schema_validation_enabled = false

  depends_on = [azapi_resource.ai_foundry_resource]
}

# ============================================================================
# Azure OpenAI Deployment (on Foundry Resource)
# ============================================================================

resource "azapi_resource" "openai_deployment" {
  type      = "Microsoft.CognitiveServices/accounts/deployments@2025-06-01"
  name      = var.openai_deployment_name
  parent_id = azapi_resource.ai_foundry_resource.id

  body = jsonencode({
    sku = {
      name     = "GlobalStandard"
      capacity = 110
    }
    properties = {
      model = {
        format  = "OpenAI"
        name    = var.openai_deployment_name
        version = var.openai_model_version
      }
      versionUpgradeOption = "OnceNewDefaultVersionAvailable"
      raiPolicyName        = "Microsoft.DefaultV2" # System-managed policy
    }
  })

  depends_on = [
    azapi_resource.ai_foundry_resource
  ]
}

# ============================================================================
# RAI (Responsible AI) Policies
# ============================================================================
# Note: Microsoft.Default and Microsoft.DefaultV2 are system-managed policies
# that exist automatically. They cannot be created or updated via templates.
# To use them, simply reference them by name in your deployments.
# For custom RAI policies, create resources with unique names (not Microsoft.*).

# ============================================================================
# Azure Document Intelligence
# ============================================================================

resource "azurerm_cognitive_account" "document_intelligence" {
  name                = "cog-fr-${var.resource_prefix}-${var.environment_name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "FormRecognizer"
  sku_name            = "S0"

  custom_subdomain_name = "di-${var.resource_prefix}-${var.environment_name}-${local.unique_suffix}"

  public_network_access_enabled = true

  identity {
    type = "SystemAssigned"
  }

  tags = local.common_tags
}

# ============================================================================
# Azure AI Search
# ============================================================================

resource "azurerm_search_service" "main" {
  name                = "srch-${var.resource_prefix}-${var.environment_name}-${local.unique_suffix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "basic"

  replica_count   = 1
  partition_count = 1

  public_network_access_enabled = true

  identity {
    type = "SystemAssigned"
  }

  tags = local.common_tags
}

# ============================================================================
# Storage Account
# ============================================================================

resource "azurerm_storage_account" "main" {
  name                     = "st${replace(var.resource_prefix, "-", "")}${local.unique_suffix}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "RAGRS"
  account_kind             = "StorageV2"
  access_tier              = "Hot"

  min_tls_version                  = "TLS1_2"
  https_traffic_only_enabled       = true
  allow_nested_items_to_be_public  = false
  shared_access_key_enabled        = false
  public_network_access_enabled    = false
  cross_tenant_replication_enabled = false

  network_rules {
    default_action             = "Allow"
    bypass                     = ["AzureServices"]
    ip_rules                   = []
    virtual_network_subnet_ids = []
  }

  blob_properties {
    delete_retention_policy {
      days = 7
    }
    container_delete_retention_policy {
      days = 7
    }
  }

  tags = local.common_tags
}

# Blob container
resource "azurerm_storage_container" "documents" {
  name                  = var.storage_container_name
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

# ============================================================================
# Azure Key Vault (Optional - Commented out)
# ============================================================================

# resource "azurerm_key_vault" "main" {
#   name                = "kv-${var.resource_prefix}-${local.unique_suffix}"
#   location            = azurerm_resource_group.main.location
#   resource_group_name = azurerm_resource_group.main.name
#   tenant_id           = data.azurerm_client_config.current.tenant_id
#   sku_name            = "standard"
#   
#   enable_rbac_authorization       = true
#   enabled_for_deployment          = false
#   enabled_for_disk_encryption     = false
#   enabled_for_template_deployment = false
#   public_network_access_enabled   = true
#   soft_delete_retention_days      = 7
#   purge_protection_enabled        = false
#   
#   network_acls {
#     default_action = "Allow"
#     bypass         = "AzureServices"
#   }
#   
#   tags = local.common_tags
# }

# Key Vault Secrets Officer role for user
# resource "azurerm_role_assignment" "user_to_keyvault" {
#   count                = var.principal_id != "" ? 1 : 0
#   scope                = azurerm_key_vault.main.id
#   role_definition_name = "Key Vault Secrets Officer"
#   principal_id         = var.principal_id
# }

# ============================================================================
# Azure Monitor - Log Analytics Workspace & Application Insights
# ============================================================================

resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${var.resource_prefix}-${var.environment_name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = local.common_tags
}

resource "azurerm_application_insights" "main" {
  name                = "appi-${var.resource_prefix}-${var.environment_name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.main.id

  tags = local.common_tags
}

# ============================================================================
# Azure Function App (for email notifications and document processing)
# ============================================================================

# Function App Storage Account (separate from document storage)
resource "azurerm_storage_account" "function" {
  name                     = "stfn${replace(var.resource_prefix, "-", "")}${local.unique_suffix}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  access_tier              = "Hot"

  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true
  allow_nested_items_to_be_public = false

  tags = local.common_tags
}

# Function App Service Plan (Consumption)
resource "azurerm_service_plan" "function" {
  name                = "plan-fn-${var.resource_prefix}-${var.environment_name}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "Y1"

  tags = local.common_tags
}

# Function App (Email Notifier)
resource "azurerm_linux_function_app" "email_notifier" {
  name                = "func-email-${var.resource_prefix}-${var.environment_name}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.function.id

  storage_account_name       = azurerm_storage_account.function.name
  storage_account_access_key = azurerm_storage_account.function.primary_access_key

  https_only = true

  identity {
    type = "SystemAssigned"
  }

  site_config {
    ftps_state          = "Disabled"
    minimum_tls_version = "1.2"

    application_stack {
      python_version = "3.11"
    }

    application_insights_connection_string = azurerm_application_insights.main.connection_string
    application_insights_key               = azurerm_application_insights.main.instrumentation_key
  }

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME"              = "python"
    "USE_MANAGED_IDENTITY"                  = "true"
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = azurerm_application_insights.main.connection_string
  }

  tags = merge(local.common_tags, {
    "azd-service-name" = "email-notifier"
  })
}

# ============================================================================
# App Service Plan
# ============================================================================

resource "azurerm_service_plan" "main" {
  name                = "plan-${var.resource_prefix}-${var.environment_name}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = var.app_service_sku

  tags = local.common_tags
}

# Backend App Service (FastAPI)
resource "azurerm_linux_web_app" "backend" {
  name                = "app-backend-${var.resource_prefix}-${var.environment_name}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.main.id

  https_only = true

  identity {
    type = "SystemAssigned"
  }

  site_config {
    ftps_state          = "Disabled"
    minimum_tls_version = "1.2"

    application_stack {
      python_version = "3.12"
    }

    app_command_line = ""
  }

  app_settings = {
    "AZURE_OPENAI_ENDPOINT"                = jsondecode(data.azapi_resource.ai_foundry_resource_data.output).properties.endpoint
    "AZURE_SEARCH_ENDPOINT"                = "https://${azurerm_search_service.main.name}.search.windows.net"
    "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT" = azurerm_cognitive_account.document_intelligence.endpoint
    "AZURE_STORAGE_ACCOUNT_NAME"           = azurerm_storage_account.main.name
    "USE_MANAGED_IDENTITY"                 = "true"
    "SCM_DO_BUILD_DURING_DEPLOYMENT"       = "true"
  }

  tags = merge(local.common_tags, {
    "azd-service-name" = "backend"
  })
}

# Frontend App Service (React/Vite)
resource "azurerm_linux_web_app" "frontend" {
  name                = "app-frontend-${var.resource_prefix}-${var.environment_name}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.main.id

  https_only = true

  identity {
    type = "SystemAssigned"
  }

  site_config {
    ftps_state          = "Disabled"
    minimum_tls_version = "1.2"

    application_stack {
      node_version = "20-lts"
    }
  }

  app_settings = {
    "VITE_API_URL" = "https://${azurerm_linux_web_app.backend.default_hostname}"
  }

  tags = merge(local.common_tags, {
    "azd-service-name" = "frontend"
  })
}

# ============================================================================
# Role Assignments
# ============================================================================

# Cognitive Services OpenAI User role
resource "azurerm_role_assignment" "user_to_openai" {
  count                = var.principal_id != "" ? 1 : 0
  scope                = azapi_resource.ai_foundry_resource.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = var.principal_id
}

# Search Index Data Contributor role
resource "azurerm_role_assignment" "user_to_search" {
  count                = var.principal_id != "" ? 1 : 0
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Index Data Contributor"
  principal_id         = var.principal_id
}

# Storage Blob Data Contributor role
resource "azurerm_role_assignment" "user_to_storage" {
  count                = var.principal_id != "" ? 1 : 0
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.principal_id
}

# Backend to OpenAI
resource "azurerm_role_assignment" "backend_to_openai" {
  scope                = azapi_resource.ai_foundry_resource.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = azurerm_linux_web_app.backend.identity[0].principal_id
}

# Backend to Search
resource "azurerm_role_assignment" "backend_to_search" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Index Data Contributor"
  principal_id         = azurerm_linux_web_app.backend.identity[0].principal_id
}

# Backend to Storage
resource "azurerm_role_assignment" "backend_to_storage" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_linux_web_app.backend.identity[0].principal_id
}
