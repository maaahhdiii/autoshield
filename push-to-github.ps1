# AutoShield - GitHub Push Script
# This script initializes git and pushes the project to GitHub
# Repository: https://github.com/maaahhdiii/autoshield

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AutoShield - GitHub Push Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Git is not installed!" -ForegroundColor Red
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

Write-Host "Git version: $(git --version)" -ForegroundColor Green
Write-Host ""

# Navigate to project directory
$projectPath = "d:\autoshild"
Set-Location $projectPath
Write-Host "Working directory: $projectPath" -ForegroundColor Green
Write-Host ""

# Check if .git exists
if (Test-Path ".git") {
    Write-Host "Git repository already initialized" -ForegroundColor Yellow
    $response = Read-Host "Do you want to reinitialize? This will remove existing git history (yes/no)"
    if ($response -eq "yes") {
        Remove-Item -Recurse -Force .git
        Write-Host "Removed existing .git directory" -ForegroundColor Yellow
    } else {
        Write-Host "Keeping existing git repository" -ForegroundColor Green
    }
}

# Initialize git repository if needed
if (-not (Test-Path ".git")) {
    Write-Host "Initializing git repository..." -ForegroundColor Cyan
    git init
    Write-Host "Git repository initialized" -ForegroundColor Green
    Write-Host ""
}

# Configure git user (if not already configured)
$userName = git config user.name
$userEmail = git config user.email

if (-not $userName) {
    Write-Host "Git user not configured" -ForegroundColor Yellow
    $userName = Read-Host "Enter your GitHub username"
    git config user.name "$userName"
    Write-Host "Set git user name: $userName" -ForegroundColor Green
}

if (-not $userEmail) {
    $userEmail = Read-Host "Enter your GitHub email"
    git config user.email "$userEmail"
    Write-Host "Set git user email: $userEmail" -ForegroundColor Green
}

Write-Host ""
Write-Host "Git user: $userName <$userEmail>" -ForegroundColor Green
Write-Host ""

# Add remote if not exists
$remoteUrl = "https://github.com/maaahhdiii/autoshield.git"
$existingRemote = git remote get-url origin 2>$null

if ($existingRemote) {
    Write-Host "Remote 'origin' already exists: $existingRemote" -ForegroundColor Yellow
    if ($existingRemote -ne $remoteUrl) {
        Write-Host "Updating remote URL to: $remoteUrl" -ForegroundColor Cyan
        git remote set-url origin $remoteUrl
    }
} else {
    Write-Host "Adding remote 'origin': $remoteUrl" -ForegroundColor Cyan
    git remote add origin $remoteUrl
}

Write-Host "Remote configured successfully" -ForegroundColor Green
Write-Host ""

# Show status
Write-Host "Current git status:" -ForegroundColor Cyan
git status --short
Write-Host ""

# Add all files
Write-Host "Adding all files to git..." -ForegroundColor Cyan
git add .
Write-Host "Files staged for commit" -ForegroundColor Green
Write-Host ""

# Show what will be committed
Write-Host "Files to be committed:" -ForegroundColor Cyan
git status --short
Write-Host ""

# Commit
$commitMessage = "Initial commit - AutoShield v2.0.0 - Complete Proxmox LXC deployment package"
Write-Host "Creating commit..." -ForegroundColor Cyan
git commit -m "$commitMessage"
Write-Host "Commit created successfully" -ForegroundColor Green
Write-Host ""

# Check if main branch exists on remote
Write-Host "Checking remote repository..." -ForegroundColor Cyan
$remoteBranches = git ls-remote --heads origin 2>$null

if ($remoteBranches) {
    Write-Host "Remote repository exists" -ForegroundColor Green
    Write-Host ""
    Write-Host "WARNING: Repository already has content!" -ForegroundColor Yellow
    Write-Host "This will attempt to merge or force push." -ForegroundColor Yellow
    Write-Host ""
    $pushOption = Read-Host "Choose push method: [1] Normal push (may fail), [2] Force push (overwrites remote), [3] Cancel"
    
    switch ($pushOption) {
        "1" {
            Write-Host "Attempting normal push..." -ForegroundColor Cyan
            git push -u origin main
        }
        "2" {
            Write-Host "Force pushing to remote..." -ForegroundColor Yellow
            Write-Host "WARNING: This will overwrite remote repository!" -ForegroundColor Red
            $confirm = Read-Host "Are you sure? Type 'CONFIRM' to proceed"
            if ($confirm -eq "CONFIRM") {
                git push -u origin main --force
            } else {
                Write-Host "Force push cancelled" -ForegroundColor Yellow
                exit 0
            }
        }
        "3" {
            Write-Host "Push cancelled by user" -ForegroundColor Yellow
            exit 0
        }
        default {
            Write-Host "Invalid option. Exiting." -ForegroundColor Red
            exit 1
        }
    }
} else {
    # New repository - push normally
    Write-Host "Pushing to remote repository..." -ForegroundColor Cyan
    git branch -M main
    git push -u origin main
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "SUCCESS! Project pushed to GitHub" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Repository URL: https://github.com/maaahhdiii/autoshield" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Visit your repository: https://github.com/maaahhdiii/autoshield" -ForegroundColor White
Write-Host "2. Verify all files are present" -ForegroundColor White
Write-Host "3. Add a repository description and topics" -ForegroundColor White
Write-Host "4. Enable Issues and Discussions (Settings)" -ForegroundColor White
Write-Host "5. Add a LICENSE file (MIT recommended)" -ForegroundColor White
Write-Host ""
Write-Host "To clone on another machine:" -ForegroundColor Yellow
Write-Host "  git clone https://github.com/maaahhdiii/autoshield.git" -ForegroundColor White
Write-Host ""
Write-Host "To update the setup script URL in documentation:" -ForegroundColor Yellow
Write-Host "  Update all references from 'your-org' to 'maaahhdiii'" -ForegroundColor White
Write-Host ""
