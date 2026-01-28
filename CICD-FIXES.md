# CI/CD Issues and Fixes - January 28, 2026

## 🔍 Issues Identified

### 1. Terraform CI/CD - Duplicate Cluster Creation ❌
**Error**: `failed to create LKE cluster: [400] [label] Label must be unique among your Clusters`

**Root Cause**: 
- Workflow was set to auto-apply on every push to `main` branch
- Infrastructure already exists (clusters deployed manually via Terraform)
- Every push tried to create new clusters with same names

**Impact**: 
- Every commit to IAC repo triggered failed deployment
- Risk of infrastructure drift if partial applies succeeded

**Fix Applied**: ✅
```yaml
# Before: Auto-apply on push
if: |
  (github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop')) ||
  (github.event_name == 'workflow_dispatch' && github.event.inputs.action == 'apply')

# After: Manual apply only
if: github.event_name == 'workflow_dispatch' && github.event.inputs.action == 'apply'
```

**Result**: 
- ✅ Terraform validate and plan still run automatically
- ✅ Apply only runs when manually triggered via `gh workflow run`
- ✅ Prevents accidental infrastructure changes
- ✅ Latest run passed successfully

---

### 2. Application CI/CD - PVC Ownership Conflict ❌
**Error**: 
```
UPGRADE FAILED: Unable to continue with update: PersistentVolumeClaim "postgresql-pvc" 
in namespace "vmshift-production" exists and cannot be imported into the current release: 
invalid ownership metadata; label validation error: missing key "app.kubernetes.io/managed-by": 
must be set to "Helm"
```

**Root Cause**:
- PVCs were created manually using `kubectl apply` during initial setup
- Helm requires resources to have specific labels/annotations to manage them
- PVCs lacked Helm ownership metadata

**Impact**:
- All deployments to production, staging, and dev failed
- Unable to update application via CI/CD
- Manual intervention required for every deployment

**Fix Applied**: ✅

Added Helm ownership metadata to all PVCs in all environments:

```bash
# Production
kubectl annotate pvc postgresql-pvc -n vmshift-production \
  meta.helm.sh/release-name=vmshift \
  meta.helm.sh/release-namespace=vmshift-production \
  --overwrite

kubectl label pvc postgresql-pvc -n vmshift-production \
  app.kubernetes.io/managed-by=Helm \
  --overwrite

# Same for staging and dev environments
```

**Result**:
- ✅ PVCs now recognized as Helm-managed resources
- ✅ Helm can upgrade/manage deployments without conflicts
- ✅ Deployment pipeline testing in progress

---

## 📊 Current Status

### Terraform CI/CD (iac-vmshift)
- **Status**: ✅ PASSING
- **Latest Run**: Fix: Disable auto-apply on push to prevent duplicate cluster creation
- **Plan Job**: ✅ Validates automatically on push
- **Apply Job**: ⚠️ Manual trigger only (safer approach)

**Workflow Behavior**:
| Event | Validate | Plan | Apply |
|-------|----------|------|-------|
| Push to main | ✅ | ✅ | ❌ |
| Push to develop | ✅ | ✅ | ❌ |
| Pull Request | ✅ | ✅ + Comment | ❌ |
| Manual (apply) | ✅ | ✅ | ✅ (with approval) |

### Application CI/CD (vmshift)
- **Status**: 🔄 TESTING (deployment in progress)
- **Latest Run**: test: trigger CI/CD after fixing PVC ownership
- **Fix Applied**: PVC ownership metadata added
- **Expected**: Should deploy successfully now

---

## 🔧 Additional Improvements Made

### 1. Security - Token Rotation
- ✅ Rotated exposed Linode API token
- ✅ Updated secrets in both repositories
- ✅ Old token should be revoked

### 2. Environment Setup
- ✅ Created GitHub environments (dev, staging, production)
- ⚠️ Protection rules need manual configuration
- ⚠️ Branch protection not yet enabled

### 3. Documentation
- ✅ Created comprehensive DevOps improvements roadmap
- ✅ Documented 20 improvements with priorities
- ✅ Added setup scripts for environments

---

## ⚠️ Remaining Issues

### 1. No Environment Protection (CRITICAL)
**Issue**: Production can still be deployed without approval

**Required Actions**:
1. Go to https://github.com/ilearn-code/vmshift/settings/environments/production
2. Enable "Required reviewers" (add 2+ people)
3. Enable "Wait timer" (5 minutes)
4. Set deployment branches to "main" only

### 2. No Branch Protection (CRITICAL)
**Issue**: Can push directly to main branch

**Required Actions**:
1. Go to https://github.com/ilearn-code/vmshift/settings/branches
2. Add branch protection rule for `main`
3. Require pull request reviews (1+ approvals)
4. Require status checks to pass

### 3. No Automated Tests (HIGH)
**Issue**: Code deploys without testing

**Fix**: Add test job to CI/CD workflow
```yaml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Run tests
      run: pytest tests/
```

### 4. No Health Checks (HIGH)
**Issue**: Failed deployments marked as successful

**Fix**: Add post-deployment verification
```yaml
- name: Health Check
  run: |
    curl -f https://vmshift-production.satyamay.tech/health || exit 1
```

### 5. Terraform State in Git (CRITICAL)
**Issue**: State files contain sensitive data and are committed

**Fix**: Migrate to remote backend (Terraform Cloud or S3)

---

## 📝 Summary

### ✅ Fixed Today
1. Terraform CI/CD - Disabled auto-apply to prevent duplicate creation attempts
2. Application CI/CD - Fixed PVC ownership metadata for Helm compatibility
3. Security - Rotated exposed API token
4. Documentation - Created comprehensive improvement roadmap

### 🔄 In Progress
1. Application deployment testing with fixed PVC metadata
2. Environment protection rules configuration

### ⚠️ Action Required (This Week)
1. **Configure environment protection rules** (CRITICAL)
2. **Enable branch protection on main** (CRITICAL)  
3. **Revoke old Linode API token** (SECURITY)
4. **Add health checks to CI/CD** (HIGH)
5. **Set up database backups** (HIGH)

### 📅 Planned (This Month)
1. Add automated tests to CI/CD
2. Migrate Terraform state to remote backend
3. Set up centralized logging (Loki)
4. Configure Prometheus alerting
5. Implement automated rollback on failure

---

## 🎯 Success Criteria

**Terraform CI/CD**:
- ✅ Validate and plan run automatically
- ✅ Apply requires manual approval
- ✅ No failed runs from duplicate infrastructure
- ⏳ State moved to remote backend

**Application CI/CD**:
- ⏳ Deploys successfully to all environments
- ⏳ Health checks verify deployment
- ⏳ Tests run before deployment
- ⏳ Rollback on failure

**Security**:
- ✅ Secrets rotated
- ⏳ Environment protection enabled
- ⏳ Branch protection enabled
- ⏳ No sensitive data in repos

---

**Last Updated**: January 28, 2026, 10:30 AM UTC  
**Status**: Terraform CI/CD Fixed ✅, Application CI/CD Testing 🔄  
**Next Review**: After application deployment completes
All Helm ownership fixed
