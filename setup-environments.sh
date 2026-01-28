#!/bin/bash
# Setup GitHub Environments with protection rules

REPO="ilearn-code/vmshift"
IAC_REPO="ilearn-code/iac-vmshift"

echo "Setting up GitHub Environments..."

# Create environments for application repo
for env in dev staging production; do
  echo "Creating environment: $env in $REPO"
  gh api repos/$REPO/environments/$env -X PUT
done

# Create destroy environment for IAC
gh api repos/$IAC_REPO/environments/production-destroy -X PUT

echo "✅ Environments created!"
echo ""
echo "⚠️  MANUAL STEPS REQUIRED:"
echo "1. Go to: https://github.com/$REPO/settings/environments"
echo "2. Configure 'production' environment:"
echo "   - Required reviewers: Add 2+ people"
echo "   - Wait timer: 5 minutes"
echo "   - Deployment branches: Only 'main'"
echo ""
echo "3. Go to: https://github.com/$IAC_REPO/settings/environments"
echo "4. Configure 'production' and 'production-destroy':"
echo "   - Required reviewers: Add admin/owner"
echo "   - Deployment branches: Only 'main'"
