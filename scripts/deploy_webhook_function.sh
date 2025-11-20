#!/bin/bash
# Deploy SharePoint Webhook Handler Azure Function

set -e

echo "========================================="
echo "Deploying SharePoint Webhook Handler"
echo "========================================="

# Configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-grant-compliance-rg}"
LOCATION="${LOCATION:-eastus}"
STORAGE_ACCOUNT="${STORAGE_ACCOUNT:-grantcompliancestor}"
FUNCTION_APP_NAME="${FUNCTION_APP_NAME:-grant-compliance-webhook-handler}"

echo ""
echo "Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  Function App: $FUNCTION_APP_NAME"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install it first."
    exit 1
fi

# Check if logged in
echo "Checking Azure CLI login..."
if ! az account show &> /dev/null; then
    echo "Not logged in. Running az login..."
    az login
fi

# Create resource group if it doesn't exist
echo ""
echo "Creating resource group..."
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output table

# Create storage account if it doesn't exist
echo ""
echo "Creating storage account..."
az storage account create \
    --name "$STORAGE_ACCOUNT" \
    --location "$LOCATION" \
    --resource-group "$RESOURCE_GROUP" \
    --sku Standard_LRS \
    --output table || echo "Storage account already exists"

# Create Function App
echo ""
echo "Creating Function App..."
az functionapp create \
    --resource-group "$RESOURCE_GROUP" \
    --consumption-plan-location "$LOCATION" \
    --runtime python \
    --runtime-version 3.11 \
    --functions-version 4 \
    --name "$FUNCTION_APP_NAME" \
    --storage-account "$STORAGE_ACCOUNT" \
    --os-type Linux \
    --output table || echo "Function App already exists"

# Configure app settings
echo ""
echo "Configuring app settings..."
az functionapp config appsettings set \
    --name "$FUNCTION_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --settings \
        SHAREPOINT_CLIENT_ID="$SHAREPOINT_CLIENT_ID" \
        SHAREPOINT_CLIENT_SECRET="$SHAREPOINT_CLIENT_SECRET" \
        AZURE_TENANT_ID="$AZURE_TENANT_ID" \
        WEBHOOK_CLIENT_STATE="$WEBHOOK_CLIENT_STATE" \
        AZURE_SEARCH_ENDPOINT="$AZURE_SEARCH_ENDPOINT" \
        AZURE_SEARCH_API_KEY="$AZURE_SEARCH_API_KEY" \
        AZURE_SEARCH_INDEX_NAME="$AZURE_SEARCH_INDEX_NAME" \
        AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="$AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT" \
        AZURE_DOCUMENT_INTELLIGENCE_API_KEY="$AZURE_DOCUMENT_INTELLIGENCE_API_KEY" \
    --output table

# Deploy function code
echo ""
echo "Deploying function code..."
cd functions/sharepoint_webhook_handler
func azure functionapp publish "$FUNCTION_APP_NAME" --python

echo ""
echo "========================================="
echo "✓ Deployment complete!"
echo "========================================="
echo ""
echo "Function URL:"
echo "  https://$FUNCTION_APP_NAME.azurewebsites.net/api/SharePointWebhookHandler"
echo ""
echo "Next steps:"
echo "  1. Note the Function URL above"
echo "  2. Run: python scripts/setup_sharepoint_webhooks.py setup"
echo "  3. Monitor logs: az functionapp log tail --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
