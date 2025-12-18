# Azure Deployment Checklist

Use this checklist to ensure a successful deployment of the Grant EO Validation Demo.

## Pre-Deployment ✅

- [ ] **Azure Subscription**
  - [ ] Active Azure subscription with sufficient credits
  - [ ] Owner or Contributor role assigned
  - [ ] Quota available for Azure OpenAI (check regional availability)

- [ ] **Tools Installed**
  - [ ] Azure Developer CLI (`azd --version`)
  - [ ] Azure CLI (`az --version`) - optional but recommended
  - [ ] Git (`git --version`)
  - [ ] Python 3.10+ (`python --version`)
  - [ ] Node.js 18+ (`node --version`) - for frontend

- [ ] **Authentication**
  - [ ] Logged in to Azure: `azd auth login`
  - [ ] Correct subscription selected: `az account show`

- [ ] **Repository**
  - [ ] Code cloned: `git clone <repo-url>`
  - [ ] In correct directory: `cd foundry-grant-eo-validation-demo`

## Deployment 🚀

Choose your deployment method:

### Option A: Azure Developer CLI (Recommended)

- [ ] **Initialize**
  ```bash
  azd init
  ```
  - [ ] Environment name entered (e.g., `dev`, `prod`)
  - [ ] Location selected (e.g., `eastus`, `westus`)

- [ ] **Deploy**
  ```bash
  azd up
  ```
  - [ ] Infrastructure provisioned successfully
  - [ ] Backend application deployed
  - [ ] Frontend application deployed

### Option B: Bicep

- [ ] **Set Parameters**
  - [ ] Edit `infra/main.parameters.json` with values
  - [ ] Get principal ID: `az ad signed-in-user show --query id -o tsv`

- [ ] **Deploy**
  ```bash
  cd infra
  az deployment sub create \
    --location eastus \
    --template-file main.bicep \
    --parameters @main.parameters.json
  ```

### Option C: Terraform

- [ ] **Configure**
  ```bash
  cd infra/terraform
  cp terraform.tfvars.example terraform.tfvars
  ```
  - [ ] Edit `terraform.tfvars` with your values

- [ ] **Deploy**
  ```bash
  terraform init
  terraform plan
  terraform apply
  ```

## Post-Deployment Configuration 🔧

- [ ] **Environment Variables**
  - [ ] Create `.env` file: `azd env get-values > .env`
  - [ ] Verify all required variables are set

- [ ] **Knowledge Base**
  - [ ] Executive order PDFs placed in `knowledge_base/executive_orders/`
  - [ ] Python virtual environment activated: `source .venv/bin/activate`
  - [ ] Dependencies installed: `uv sync`
  - [ ] Knowledge base indexed:
    ```bash
    python scripts/index_knowledge_base.py --input knowledge_base/executive_orders/
    ```

- [ ] **Application Verification**
  - [ ] Backend health check: `curl <backend-url>/health`
  - [ ] Frontend accessible in browser
  - [ ] Can upload a document through UI
  - [ ] Compliance analysis runs successfully

## Testing & Validation ✔️

- [ ] **Functionality Tests**
  - [ ] Upload sample grant proposal PDF
  - [ ] View compliance analysis results
  - [ ] Check risk scores and citations
  - [ ] Browse knowledge base
  - [ ] Download analysis report

- [ ] **Integration Tests**
  - [ ] Document Intelligence processing works
  - [ ] Azure AI Search retrieval works
  - [ ] Azure OpenAI generates responses
  - [ ] Storage account stores documents

- [ ] **Security Checks**
  - [ ] Managed identities configured
  - [ ] RBAC roles assigned correctly
  - [ ] No access keys in code or config
  - [ ] HTTPS-only enforcement enabled

## Monitoring & Observability 📊

- [ ] **Azure Portal Checks**
  - [ ] All resources showing as "Running"
  - [ ] No deployment errors in Activity Log
  - [ ] Cost Management tracking enabled

- [ ] **Application Insights** (if configured)
  - [ ] Logs appearing in Application Insights
  - [ ] Performance metrics being collected
  - [ ] Alerts configured for errors

- [ ] **Cost Monitoring**
  - [ ] Budget alert set up
  - [ ] Cost analysis reviewed
  - [ ] Auto-shutdown configured (if applicable)

## Documentation 📚

- [ ] **Team Handoff**
  - [ ] Deployment guide shared with team
  - [ ] Access credentials documented (in secure location)
  - [ ] Architecture diagram reviewed
  - [ ] Runbook created for common operations

- [ ] **Knowledge Transfer**
  - [ ] Agent customization guide reviewed
  - [ ] PDF processing workflow documented
  - [ ] Troubleshooting steps identified

## Optional Enhancements 🌟

- [ ] **SharePoint Integration**
  - [ ] SharePoint library configured
  - [ ] Webhooks set up
  - [ ] Permissions granted

- [ ] **Email Notifications**
  - [ ] SMTP settings configured
  - [ ] Email templates customized
  - [ ] Test email sent successfully

- [ ] **CI/CD Pipeline**
  - [ ] GitHub Actions workflow created
  - [ ] Automated tests configured
  - [ ] Deployment automation set up

- [ ] **Advanced Security**
  - [ ] Private Endpoints enabled
  - [ ] VNet integration configured
  - [ ] Azure Key Vault for secrets
  - [ ] Azure AD authentication

## Cleanup (When Done) 🧹

- [ ] **Remove Resources**
  ```bash
  azd down
  ```
  - [ ] All Azure resources deleted
  - [ ] Resource group removed
  - [ ] Costs stopped accruing

- [ ] **Verify Cleanup**
  - [ ] Check Azure Portal for remaining resources
  - [ ] Review billing to confirm no charges
  - [ ] Archive environment configuration if needed

## Troubleshooting Reference 🔧

Common issues and solutions:

| Issue | Solution |
|-------|----------|
| OpenAI quota exceeded | Try different region or request quota increase |
| Role assignment failed | Ensure you have Owner role on subscription |
| Deployment timeout | Check region capacity, try different location |
| Knowledge base indexing failed | Verify AI Search service is running |
| App not accessible | Check App Service logs in Azure Portal |

## Support Resources 📞

- 📖 [Infrastructure README](../infra/README.md)
- 📖 [Deployment Guide](Deployment.md)
- 📖 [Quick Deploy Guide](QuickDeploy.md)
- 🐛 [GitHub Issues](https://github.com/honestypugh2/foundry-grant-eo-validation-demo/issues)
- 💬 [Azure Support](https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade)

---

**Deployment Date:** ________________  
**Deployed By:** ________________  
**Environment:** ☐ Dev  ☐ Staging  ☐ Production  
**Region:** ________________  
**Resource Group:** ________________
