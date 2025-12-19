# Variables for Grant EO Validation Demo

variable "environment_name" {
  description = "Name of the environment (e.g., dev, staging, prod)"
  type        = string
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "eastus"
}

variable "resource_prefix" {
  description = "Prefix for resource naming"
  type        = string
  default     = "grant-eo"
}

variable "principal_id" {
  description = "Principal ID for role assignments (user or service principal)"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "openai_deployment_name" {
  description = "Name of the Azure OpenAI deployment"
  type        = string
  default     = "gpt-4o"
}

variable "openai_model_version" {
  description = "Version of the OpenAI model"
  type        = string
  default     = "2024-08-06"
}

variable "search_index_name" {
  description = "Name of the Azure AI Search index"
  type        = string
  default     = "grant-compliance-index"
}

variable "storage_container_name" {
  description = "Name of the blob storage container"
  type        = string
  default     = "documents"
}

variable "app_service_sku" {
  description = "SKU for App Service Plan"
  type        = string
  default     = "F1"
}
