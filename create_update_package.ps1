# Z-WAIF Update Package Creator (PowerShell Version)
# This script creates a RAR package of the Z-WAIF project for distribution

param(
    [string]$OutputPath = ".",
    [string]$Version = "",
    [switch]$Force
)

# Set execution policy for this script
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Z-WAIF Update Package Creator" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get current directory
$ProjectDir = Get-Location
$ProjectName = "z-waif"

# Generate version if not provided
if (-not $Version) {
    $Version = Get-Date -Format "yyMMdd_HHmm"
}

# Set output filename
$OutputFile = Join-Path $OutputPath "z-waif_update_$Version.rar"

Write-Host "Creating update package: $OutputFile" -ForegroundColor Yellow
Write-Host ""

# Check if WinRAR is installed
try {
    $null = Get-Command rar -ErrorAction Stop
    Write-Host "✓ WinRAR found" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: WinRAR is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install WinRAR from: https://www.win-rar.com/" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Create exclude patterns
$ExcludePatterns = @(
    "*.pyc",
    "__pycache__",
    ".git",
    ".gitignore",
    ".env",
    ".envrc",
    "venv",
    "logs",
    "Logs",
    "*.log",
    "*.tmp",
    "*.temp",
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    "*.bak",
    "*.backup",
    "test_*.py",
    "*_test.py",
    "update_pip.bat",
    "create_update_package.bat",
    "create_update_package.ps1",
    "test_rvc_connection.py",
    "*.rar",
    "*.zip",
    "*.7z",
    "node_modules",
    ".vscode",
    ".idea",
    "*.swp",
    "*.swo",
    "*~",
    ".pytest_cache",
    ".coverage",
    "htmlcov",
    ".tox",
    ".mypy_cache",
    ".ruff_cache",
    ".black_cache",
    ".isort.cfg",
    ".flake8",
    ".pylintrc",
    ".pre-commit-config.yaml",
    ".github",
    ".gitlab-ci.yml",
    ".travis.yml",
    ".appveyor.yml",
    ".circleci",
    ".azure-pipelines.yml",
    ".jenkins",
    ".drone.yml",
    ".woodpecker.yml",
    ".gitea*"
)

# Create temporary exclude file
$ExcludeFile = Join-Path $env:TEMP "zwaif_exclude_$([System.Guid]::NewGuid().ToString('N')[0..7] -join '').txt"
$ExcludePatterns | Out-File -FilePath $ExcludeFile -Encoding UTF8

Write-Host "✓ Exclude list created" -ForegroundColor Green
Write-Host ""

# Check if output file already exists
if (Test-Path $OutputFile) {
    if (-not $Force) {
        Write-Host "⚠ Warning: Output file already exists: $OutputFile" -ForegroundColor Yellow
        $response = Read-Host "Do you want to overwrite it? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            Write-Host "Operation cancelled." -ForegroundColor Red
            Remove-Item $ExcludeFile -ErrorAction SilentlyContinue
            exit 0
        }
    }
    Remove-Item $OutputFile -Force
}

# Create the RAR file
Write-Host "Creating RAR package..." -ForegroundColor Yellow
Write-Host "This may take a few minutes depending on project size..." -ForegroundColor Yellow
Write-Host ""

try {
    $StartTime = Get-Date
    
    # Build RAR command
    $RarArgs = @(
        "a",                    # Add to archive
        "-r",                   # Recurse subdirectories
        "-x@$ExcludeFile",      # Exclude file
        $OutputFile,            # Output file
        "$ProjectDir\*"         # Source files
    )
    
    # Execute RAR command
    & rar @RarArgs
    
    $EndTime = Get-Date
    $Duration = $EndTime - $StartTime
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "SUCCESS: Update package created!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        
        # Get file info
        $FileInfo = Get-Item $OutputFile
        $SizeMB = [math]::Round($FileInfo.Length / 1MB, 2)
        
        Write-Host "Package: $($FileInfo.Name)" -ForegroundColor White
        Write-Host "Location: $($FileInfo.FullName)" -ForegroundColor White
        Write-Host "Size: $SizeMB MB" -ForegroundColor White
        Write-Host "Duration: $($Duration.ToString('mm\:ss'))" -ForegroundColor White
        Write-Host ""
        
        Write-Host "Package contents:" -ForegroundColor Cyan
        Write-Host "- All source code and configuration files" -ForegroundColor Gray
        Write-Host "- Documentation and guides" -ForegroundColor Gray
        Write-Host "- Preset configurations" -ForegroundColor Gray
        Write-Host "- Excluded: temporary files, logs, virtual environments" -ForegroundColor Gray
        Write-Host ""
        
        Write-Host "✓ Ready for distribution!" -ForegroundColor Green
        
        # Show file in explorer
        $ShowInExplorer = Read-Host "Show file in Explorer? (Y/n)"
        if ($ShowInExplorer -ne "n" -and $ShowInExplorer -ne "N") {
            Start-Process "explorer.exe" -ArgumentList "/select,`"$($FileInfo.FullName)`""
        }
        
    } else {
        Write-Host ""
        Write-Host "✗ ERROR: Failed to create RAR package" -ForegroundColor Red
        Write-Host "Exit code: $LASTEXITCODE" -ForegroundColor Red
        Write-Host "Please check if you have write permissions in the output directory" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host ""
    Write-Host "✗ ERROR: Exception occurred during package creation" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
} finally {
    # Clean up temporary files
    if (Test-Path $ExcludeFile) {
        Remove-Item $ExcludeFile -Force
    }
}

Write-Host ""
Read-Host "Press Enter to exit" 