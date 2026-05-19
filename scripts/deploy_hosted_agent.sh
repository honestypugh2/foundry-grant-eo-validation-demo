#!/usr/bin/env bash
# deploy_hosted_agent.sh
#
# Builds, pushes, and deploys the Grant Compliance Agent as a
# Foundry Hosted Agent so it appears in the Foundry portal.
#
# Prerequisites:
#   - az login
#   - Docker installed and running
#   - Azure Container Registry exists (created by this script if needed)
#   - Foundry Project Manager role on the project
#
# Usage:
#   ./scripts/deploy_hosted_agent.sh [--build-only] [--create-acr]

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-grant-eo-dev}"
LOCATION="${LOCATION:-eastus2}"
FOUNDRY_RESOURCE="${FOUNDRY_RESOURCE:-cog-grant-eo-dev}"
FOUNDRY_PROJECT="${FOUNDRY_PROJECT:-grant-eo-project-dev}"
ACR_NAME="${ACR_NAME:-acrgranteodev}"
IMAGE_NAME="grant-compliance-agent"
IMAGE_TAG="${IMAGE_TAG:-v1}"
AGENT_NAME="grant-compliance-agent"
CPU="1"
MEMORY="2Gi"

PROJECT_ENDPOINT="https://${FOUNDRY_RESOURCE}.services.ai.azure.com/api/projects/${FOUNDRY_PROJECT}"

# ── Parse arguments ───────────────────────────────────────────────────────
BUILD_ONLY=false
CREATE_ACR=false
for arg in "$@"; do
  case "$arg" in
    --build-only) BUILD_ONLY=true ;;
    --create-acr) CREATE_ACR=true ;;
  esac
done

echo "============================================================"
echo "  Foundry Hosted Agent Deployment"
echo "============================================================"
echo "  Resource Group:  $RESOURCE_GROUP"
echo "  ACR:             $ACR_NAME"
echo "  Image:           $IMAGE_NAME:$IMAGE_TAG"
echo "  Agent Name:      $AGENT_NAME"
echo "  Project:         $PROJECT_ENDPOINT"
echo "============================================================"

# ── Step 1: Create ACR if requested ───────────────────────────────────────
if $CREATE_ACR; then
  echo ""
  echo ">> Creating Azure Container Registry: $ACR_NAME ..."
  az acr create \
    --name "$ACR_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --sku Basic \
    --admin-enabled true \
    --output table 2>/dev/null || echo "ACR may already exist, continuing..."
fi

# ── Step 2: Build container image ─────────────────────────────────────────
echo ""
echo ">> Building container image: $IMAGE_NAME:$IMAGE_TAG ..."
ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
FULL_IMAGE="${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}"

docker buildx build \
  --platform linux/amd64 \
  --load \
  -t "$FULL_IMAGE" \
  -f src/hosted_agent/Dockerfile \
  . 

echo "✓ Image built: $FULL_IMAGE"

if $BUILD_ONLY; then
  echo ""
  echo "Build-only mode. Skipping push and deploy."
  echo "To test locally: docker run -p 8088:8088 --env-file .env $FULL_IMAGE"
  exit 0
fi

# ── Step 3: Push to ACR ──────────────────────────────────────────────────
echo ""
echo ">> Logging into ACR: $ACR_NAME ..."
az acr login --name "$ACR_NAME"

echo ">> Pushing image to ACR ..."
docker push "$FULL_IMAGE"
echo "✓ Image pushed: $FULL_IMAGE"

# ── Step 4: Grant project identity ACR pull access ───────────────────────
echo ""
echo ">> Configuring ACR permissions for Foundry project ..."

# Get the project's managed identity principal ID
PROJECT_PRINCIPAL_ID=$(az cognitiveservices account show \
  --name "$FOUNDRY_RESOURCE" \
  --resource-group "$RESOURCE_GROUP" \
  --query "identity.principalId" -o tsv 2>/dev/null || echo "")

if [[ -n "$PROJECT_PRINCIPAL_ID" ]]; then
  ACR_ID=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query id -o tsv)
  az role assignment create \
    --assignee "$PROJECT_PRINCIPAL_ID" \
    --role "AcrPull" \
    --scope "$ACR_ID" \
    --output none 2>/dev/null || echo "  ACR pull role may already be assigned."
  echo "✓ ACR pull access granted to project identity"
else
  echo "⚠  Could not find project managed identity. You may need to assign AcrPull manually."
fi

# ── Step 5: Read environment variable values from current settings ───────
echo ""
echo ">> Reading environment configuration ..."

AZURE_OPENAI_ENDPOINT_VAL=$(az cognitiveservices account show \
  --name "$FOUNDRY_RESOURCE" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.endpoint" -o tsv 2>/dev/null || echo "")

AZURE_SEARCH_ENDPOINT_VAL=$(az functionapp config appsettings list \
  --name "func-compliance-grant-eo-dev" \
  --resource-group "$RESOURCE_GROUP" \
  --query "[?name=='AZURE_SEARCH_ENDPOINT'].value" -o tsv 2>/dev/null || echo "")

AZURE_SEARCH_INDEX_VAL=$(az functionapp config appsettings list \
  --name "func-compliance-grant-eo-dev" \
  --resource-group "$RESOURCE_GROUP" \
  --query "[?name=='AZURE_SEARCH_INDEX_NAME'].value" -o tsv 2>/dev/null || echo "grant-compliance-index")

# ── Step 6: Deploy to Foundry Agent Service ──────────────────────────────
echo ""
echo ">> Deploying agent to Foundry Agent Service ..."

TOKEN=$(az account get-access-token --resource https://ai.azure.com --query accessToken -o tsv)

# Create the hosted agent version via REST API
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  "${PROJECT_ENDPOINT}/agents?api-version=v1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"${AGENT_NAME}\",
    \"definition\": {
      \"kind\": \"hosted\",
      \"image\": \"${FULL_IMAGE}\",
      \"cpu\": \"${CPU}\",
      \"memory\": \"${MEMORY}\",
      \"container_protocol_versions\": [
        {\"protocol\": \"responses\", \"version\": \"1.0.0\"}
      ],
      \"environment_variables\": {
        \"AZURE_OPENAI_ENDPOINT\": \"${AZURE_OPENAI_ENDPOINT_VAL}\",
        \"AZURE_SEARCH_ENDPOINT\": \"${AZURE_SEARCH_ENDPOINT_VAL}\",
        \"AZURE_SEARCH_INDEX_NAME\": \"${AZURE_SEARCH_INDEX_VAL}\",
        \"AI_SEARCH_QUERY_TYPE\": \"semantic\",
        \"AZURE_OPENAI_EMBEDDING_DEPLOYMENT\": \"text-embedding-3-small\"
      }
    }
  }")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [[ "$HTTP_CODE" =~ ^2 ]]; then
  echo "✓ Agent deployed successfully!"
  echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
  echo "✗ Deployment failed (HTTP $HTTP_CODE):"
  echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
  exit 1
fi

# ── Step 7: Poll for active status ───────────────────────────────────────
echo ""
echo ">> Waiting for agent to become active ..."

for i in $(seq 1 24); do
  sleep 5
  VERSION_RESPONSE=$(curl -s \
    "${PROJECT_ENDPOINT}/agents/${AGENT_NAME}/versions/1?api-version=v1" \
    -H "Authorization: Bearer $TOKEN")
  
  STATUS=$(echo "$VERSION_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "unknown")
  echo "  Status: $STATUS (${i}/24)"
  
  if [[ "$STATUS" == "active" ]]; then
    echo ""
    echo "============================================================"
    echo "  ✓ Agent is ACTIVE and visible in the Foundry portal!"
    echo ""
    echo "  Portal: https://ai.azure.com"
    echo "  Endpoint: ${PROJECT_ENDPOINT}/agents/${AGENT_NAME}/endpoint/protocols/openai/responses"
    echo ""
    echo "  Test with:"
    echo "    curl -X POST '${PROJECT_ENDPOINT}/agents/${AGENT_NAME}/endpoint/protocols/openai/responses?api-version=v1' \\"
    echo "      -H 'Authorization: Bearer \$(az account get-access-token --resource https://ai.azure.com --query accessToken -o tsv)' \\"
    echo "      -H 'Content-Type: application/json' \\"
    echo "      -d '{\"input\": \"Check compliance for: County requests 2.5M for bridge rehabilitation with DEI requirements.\"}'"
    echo "============================================================"
    exit 0
  fi
  
  if [[ "$STATUS" == "failed" ]]; then
    echo "✗ Agent provisioning failed:"
    echo "$VERSION_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$VERSION_RESPONSE"
    exit 1
  fi
done

echo "⚠  Agent has not reached active status within 2 minutes. Check the portal."
