# MistHelper Repository Migration Guide

## Overview
This guide walks through migrating MistHelper from the `Code` repository to its own standalone repository at `https://github.com/jmorrison-juniper/MistHelper`.

## Prerequisites
- Git installed and configured
- GitHub account with access to create repositories
- GitHub CLI (gh) installed (optional but recommended)

## Migration Steps

### Step 1: Create New GitHub Repository

**Option A: Using GitHub CLI (Recommended)**
```powershell
# Navigate to MistHelper directory
cd "C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper"

# Create new repository on GitHub
gh repo create jmorrison-juniper/MistHelper --public --description "Network operations tool for Juniper Mist cloud infrastructure management and monitoring" --clone=false
```

**Option B: Using GitHub Web Interface**
1. Go to https://github.com/new
2. Repository name: `MistHelper`
3. Description: `Network operations tool for Juniper Mist cloud infrastructure management and monitoring`
4. Public repository
5. Do NOT initialize with README, .gitignore, or license (we have these)
6. Click "Create repository"

### Step 2: Initialize Git in MistHelper Directory

```powershell
# Navigate to MistHelper directory
cd "C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper"

# Initialize new Git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: MistHelper v2.1.0 - Standalone repository migration"
```

### Step 3: Connect to GitHub Remote

```powershell
# Add GitHub remote
git remote add origin https://github.com/jmorrison-juniper/MistHelper.git

# Verify remote
git remote -v

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 4: Verify Migration

1. Visit https://github.com/jmorrison-juniper/MistHelper
2. Verify all files are present
3. Check that README.md displays correctly
4. Verify LICENSE file is recognized by GitHub

### Step 5: Update Local Git Configuration (Optional)

If you want to keep the old Code repository for other projects:

```powershell
# Navigate back to Code repository root
cd "C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code"

# Remove MistHelper from Code repository tracking
git rm -r --cached MistHelper

# Add MistHelper to .gitignore in Code repo
echo "MistHelper/" >> .gitignore

# Commit the removal
git add .gitignore
git commit -m "Remove MistHelper (moved to standalone repository)"
git push
```

### Step 6: Configure GitHub Repository Settings

1. Go to repository Settings
2. Enable branch protection for `main`:
   - Require pull request reviews before merging
   - Require status checks to pass before merging
3. Add topics: `juniper`, `mist`, `network-automation`, `python`, `api-client`
4. Set repository image/social preview

### Step 7: Container Registry Setup

```powershell
# Authenticate to GitHub Container Registry
echo $env:GITHUB_TOKEN | docker login ghcr.io -u jmorrison-juniper --password-stdin

# Or with Podman
echo $env:GITHUB_TOKEN | podman login ghcr.io -u jmorrison-juniper --password-stdin

# Build container
podman build -f Containerfile -t ghcr.io/jmorrison-juniper/misthelper:latest .
podman build -f Containerfile -t ghcr.io/jmorrison-juniper/misthelper:2.1.0 .

# Push to GitHub Container Registry
podman push ghcr.io/jmorrison-juniper/misthelper:latest
podman push ghcr.io/jmorrison-juniper/misthelper:2.1.0
```

## Post-Migration Checklist

- [ ] Repository created on GitHub
- [ ] All files pushed successfully
- [ ] LICENSE file recognized by GitHub
- [ ] README.md renders correctly
- [ ] Branch protection enabled
- [ ] Topics/tags added
- [ ] Container images published to GHCR
- [ ] Documentation updated with new URLs
- [ ] Old Code repository cleaned up (optional)

## Rollback Plan

If you need to rollback:

```powershell
# Delete the new repository on GitHub (via web interface or CLI)
gh repo delete jmorrison-juniper/MistHelper

# Remove local .git directory in MistHelper folder
cd "C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper"
Remove-Item -Recurse -Force .git
```

## Notes

- The migration preserves all current files but starts a new Git history
- If you want to preserve commit history from the Code repo, use `git filter-branch` or `git subtree` instead
- SSH credentials in Containerfile should be changed for production deployments
- Update any CI/CD pipelines to point to new repository
