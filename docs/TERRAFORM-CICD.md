# Terraform CI/CD Pipeline Documentation

## Overview

The Terraform CI/CD pipeline automates infrastructure provisioning and management across three environments using GitHub Actions. It provides automated validation, planning, and deployment of Linode Kubernetes Engine (LKE) clusters with proper approval workflows.

## Pipeline Architecture

```
┌─────────────────┐
│  Push/PR Event  │
│  or Manual Run  │
└────────┬────────┘
         │
         ▼
┌────────────────────┐
│ Determine Environment │
│ (dev/staging/prod)    │
└─────────┬─────────────┘
          │
          ├──────────────┬──────────────┐
          │              │              │
          ▼              ▼              ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │ Validate│    │  Plan   │    │  Apply  │
    └─────────┘    └─────────┘    └─────────┘
```

## Workflow Triggers

### Automatic Triggers

1. **Push to `main` branch** → Production environment
   - Runs: validate → plan → apply (with approval)
   - Applies infrastructure changes automatically after approval

2. **Push to `develop` branch** → Staging environment
   - Runs: validate → plan → apply (with approval)
   - Applies infrastructure changes to staging

3. **Pull Request** → Review environment
   - Runs: validate → plan
   - Posts plan output as PR comment
   - Does NOT apply changes

### Manual Trigger

Use `workflow_dispatch` for manual operations:

```bash
# Manual plan for specific environment
gh workflow run terraform.yaml \
  -f environment=production \
  -f action=plan

# Manual apply to dev
gh workflow run terraform.yaml \
  -f environment=dev \
  -f action=apply

# Manual destroy (requires approval)
gh workflow run terraform.yaml \
  -f environment=staging \
  -f action=destroy
```

## Environment Mapping

| Branch/Trigger | Environment | Workspace | tfvars File |
|----------------|-------------|-----------|-------------|
| `main` branch | production | production | terraform.tfvars.prod |
| `develop` branch | staging | staging | terraform.tfvars.staging |
| feature/* branch | dev | dev | terraform.tfvars.dev |
| Manual dispatch | (selected) | (selected) | terraform.tfvars.(env) |

## Pipeline Jobs

### 1. Determine Environment
- **Purpose**: Identifies target environment based on branch or manual input
- **Outputs**: environment name, workspace name, tfvars filename
- **Logic**:
  - Manual: Uses selected environment
  - main branch → production
  - develop branch → staging
  - Other branches → dev

### 2. Validate
- **Purpose**: Ensures Terraform code is syntactically correct
- **Steps**:
  - Format check (`terraform fmt`)
  - Initialization without backend
  - Configuration validation
- **Runs on**: All events (push, PR, manual)

### 3. Plan
- **Purpose**: Shows what changes will be applied to infrastructure
- **Steps**:
  - Initialize with backend (uses local state + workspaces)
  - Select or create workspace
  - Generate plan with environment-specific tfvars
  - Upload plan artifact
  - Comment plan on PR (if applicable)
- **Runs on**: All events
- **Output**: Plan saved as artifact for apply job

### 4. Apply
- **Purpose**: Applies infrastructure changes
- **Steps**:
  - Download plan artifact from previous job
  - Apply plan with auto-approve
  - Update kubeconfig secrets in GitHub
  - Display infrastructure outputs
- **Runs on**: Push to main/develop, or manual apply
- **Protection**: Requires environment approval for production

### 5. Destroy
- **Purpose**: Tears down infrastructure (manual only)
- **Steps**:
  - Select workspace
  - Destroy all resources
  - Delete workspace
- **Runs on**: Manual dispatch with action=destroy
- **Protection**: Requires separate environment approval

## GitHub Secrets Required

| Secret Name | Description | Where to Get |
|-------------|-------------|--------------|
| `LINODE_TOKEN` | Linode API token for provisioning | Already configured |
| `GITHUB_TOKEN` | Auto-provided by GitHub Actions | Automatic |

**Note**: Kubeconfig secrets (KUBECONFIG_DEV, etc.) are automatically updated after each apply job.

## GitHub Environments Setup

Configure these environments in GitHub Settings → Environments:

### 1. dev
- **Protection rules**: None (auto-deploy)
- **Reviewers**: None required
- **Branch restrictions**: None

### 2. staging  
- **Protection rules**: Optional approval
- **Reviewers**: 1-2 team members (recommended)
- **Branch restrictions**: develop branch only

### 3. production
- **Protection rules**: Required approval ✅
- **Reviewers**: 2+ senior engineers (required)
- **Branch restrictions**: main branch only
- **Deployment protection**: Wait timer (5 minutes recommended)

### 4. production-destroy
- **Protection rules**: Required approval ✅
- **Reviewers**: Admin/Owner only
- **Purpose**: Extra safety for destruction operations

### Setup Command

```bash
# Configure environments via GitHub CLI
gh api repos/ilearn-code/vmshift/environments/production -X PUT \
  --field protection_rules[0][type]=required_reviewers \
  --field protection_rules[0][reviewers][0][type]=User \
  --field protection_rules[0][reviewers][0][id]=YOUR_USER_ID
```

Or configure manually at:
https://github.com/ilearn-code/vmshift/settings/environments

## Usage Examples

### Scenario 1: Update Dev Infrastructure

```bash
# 1. Create feature branch
git checkout -b feature/update-node-count

# 2. Modify terraform/terraform.tfvars.dev
# Change node_count or other settings

# 3. Commit and push
git add terraform/terraform.tfvars.dev
git commit -m "Increase dev node count to 3"
git push origin feature/update-node-count

# 4. Create PR to develop branch
gh pr create --base develop --title "Update dev infrastructure"

# 5. Review plan in PR comments
# 6. Merge PR → automatic apply to dev
```

### Scenario 2: Production Infrastructure Update

```bash
# 1. Update production tfvars
vim terraform/terraform.tfvars.prod

# 2. Commit to main branch (or PR to main)
git add terraform/terraform.tfvars.prod
git commit -m "Update production node type to g6-standard-4"
git push origin main

# 3. Pipeline runs automatically
# 4. Review plan output in Actions
# 5. Approve deployment in GitHub UI
# 6. Infrastructure updates automatically
```

### Scenario 3: Manual Staging Deployment

```bash
# Trigger workflow manually
gh workflow run terraform.yaml \
  -f environment=staging \
  -f action=apply

# Monitor progress
gh run watch

# Check outputs
gh run view --log
```

### Scenario 4: Emergency Rollback

```bash
# 1. Revert commit
git revert HEAD
git push origin main

# 2. Pipeline automatically applies previous state
# Or manually trigger with previous tfvars:

gh workflow run terraform.yaml \
  -f environment=production \
  -f action=apply
```

### Scenario 5: Destroy Dev Environment

```bash
# Manual destroy (requires approval)
gh workflow run terraform.yaml \
  -f environment=dev \
  -f action=destroy

# Go to Actions UI and approve destruction
# https://github.com/ilearn-code/vmshift/actions
```

## State Management

### Current Setup
- **Backend**: Local state files with Terraform workspaces
- **Location**: `terraform/terraform.tfstate.d/{environment}/`
- **Version Control**: State files committed to repository

### State File Structure
```
terraform/
├── terraform.tfstate          # Default workspace
└── terraform.tfstate.d/
    ├── dev/
    │   └── terraform.tfstate
    ├── staging/
    │   ├── terraform.tfstate
    │   └── terraform.tfstate.backup
    └── production/
        └── terraform.tfstate
```

### Workspace Commands

```bash
# List workspaces
cd terraform && terraform workspace list

# Switch workspace
terraform workspace select staging

# Show current workspace
terraform workspace show

# Create new workspace
terraform workspace new dev
```

## Monitoring & Troubleshooting

### View Workflow Runs

```bash
# List recent runs
gh run list --workflow=terraform.yaml

# Watch current run
gh run watch

# View specific run
gh run view RUN_ID --log

# Download artifacts
gh run download RUN_ID
```

### Check Plan Output

```bash
# View plan from PR comment or Actions logs
gh run view --log | grep "Terraform will perform"

# Download plan artifact
gh run download RUN_ID -n tfplan-production
```

### Validate Locally

```bash
cd terraform

# Format check
terraform fmt -check -recursive

# Initialize
terraform init

# Select environment
terraform workspace select dev

# Plan
terraform plan -var-file=terraform.tfvars.dev

# Apply manually
terraform apply -var-file=terraform.tfvars.dev
```

### Common Issues

#### Issue 1: Workspace Not Found
```
Error: workspace "dev" doesn't exist
```

**Solution**: Create workspace first
```bash
cd terraform
terraform workspace new dev
```

#### Issue 2: State Lock
```
Error: Error acquiring the state lock
```

**Solution**: Local backend doesn't lock, but if migrating to remote:
```bash
terraform force-unlock LOCK_ID
```

#### Issue 3: Kubeconfig Not Updated
```
Error: kubeconfig-production.yaml not found
```

**Solution**: Check terraform outputs and regenerate:
```bash
terraform output -raw kubeconfig_production > kubeconfig-production.yaml
gh secret set KUBECONFIG_PRODUCTION < kubeconfig-production.yaml
```

#### Issue 4: Plan/Apply Mismatch
```
Error: Plan doesn't match expected changes
```

**Solution**: Re-run plan or check workspace:
```bash
terraform workspace show
terraform plan -var-file=terraform.tfvars.prod -out=tfplan
terraform show tfplan
```

## Best Practices

### 1. Always Plan Before Apply
- Review plan output carefully
- Check resource counts and changes
- Verify environment targeting

### 2. Use Pull Requests for Production
- Never push directly to main for infrastructure changes
- Require code review on Terraform changes
- Use PR comments to discuss plan output

### 3. Small, Incremental Changes
- Change one thing at a time
- Test in dev first, then staging, then production
- Commit frequently with descriptive messages

### 4. Document Infrastructure Changes
```bash
git commit -m "terraform: increase production nodes to 5

- Updated terraform.tfvars.prod
- Reason: Handling increased traffic
- Cost impact: +$72/month
- Approved by: @manager"
```

### 5. Backup State Files
```bash
# Manual backup before major changes
cp -r terraform/terraform.tfstate.d/ ~/backups/terraform-$(date +%Y%m%d)
```

### 6. Test Destroy in Dev First
- Always test destroy operations in dev environment
- Verify all resources are properly cleaned up
- Document destruction procedures

## Security Considerations

### 1. Secret Management
- ✅ LINODE_TOKEN stored as GitHub secret
- ✅ Kubeconfig files auto-updated after apply
- ✅ Database passwords already configured
- ❌ Consider using HashiCorp Vault for sensitive values

### 2. State File Security
- ⚠️ State files contain sensitive data
- ⚠️ Currently committed to repository
- 🔒 Recommendation: Migrate to remote backend (Terraform Cloud/S3)

### 3. Access Control
- ✅ Production requires approval
- ✅ Destroy requires separate approval
- ✅ GitHub environment protection enabled
- 🔒 Recommendation: Enable branch protection on main

### 4. Audit Trail
- ✅ All changes tracked in Git history
- ✅ GitHub Actions logs retained
- ✅ Terraform state includes change history
- 🔒 Recommendation: Enable AWS CloudTrail for Linode API calls

## Future Improvements

### 1. Remote State Backend
```hcl
# Add to terraform/main.tf
terraform {
  backend "s3" {
    bucket = "vmshift-terraform-state"
    key    = "infrastructure/terraform.tfstate"
    region = "us-east-1"
    encrypt = true
    dynamodb_table = "terraform-locks"
  }
}
```

### 2. Cost Estimation
- Integrate Infracost to estimate changes
- Add cost checks to PR comments
- Alert on significant cost increases

### 3. Drift Detection
- Schedule daily drift checks
- Alert when infrastructure differs from state
- Auto-create PRs to fix drift

### 4. Automated Testing
- Add Terratest for infrastructure tests
- Validate after apply
- Integration tests for deployed clusters

### 5. Policy as Code
- Implement Open Policy Agent (OPA)
- Enforce security policies
- Validate compliance before apply

## References

- [Terraform GitHub Actions](https://github.com/hashicorp/setup-terraform)
- [GitHub Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [Terraform Workspaces](https://developer.hashicorp.com/terraform/language/state/workspaces)
- [Linode Kubernetes Engine](https://www.linode.com/docs/guides/deploy-and-manage-a-cluster-with-linode-kubernetes-engine-a-tutorial/)

## Support

For issues or questions:
1. Check GitHub Actions logs
2. Review this documentation
3. Check Terraform state files
4. Contact DevOps team

---

**Last Updated**: January 28, 2026  
**Maintained By**: DevOps Team  
**Version**: 1.0.0
