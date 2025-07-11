# Z-WAIF Update Package Creator

This directory contains scripts to create RAR packages of the Z-WAIF project for easy distribution and updates.

## Available Scripts

### 1. `create_update_package.bat` (Windows Batch)
- **Usage**: Double-click or run from command prompt
- **Requirements**: WinRAR installed and in PATH
- **Output**: `z-waif_update_YYMMDD_HHMM.rar`

### 2. `create_update_package.ps1` (PowerShell)
- **Usage**: Right-click → "Run with PowerShell" or run from PowerShell
- **Requirements**: WinRAR installed and in PATH
- **Features**: 
  - Colored output
  - Progress tracking
  - Optional parameters
  - Auto-open in Explorer

## Prerequisites

1. **WinRAR**: Download and install from [https://www.win-rar.com/](https://www.win-rar.com/)
2. **Ensure WinRAR is in PATH**: The `rar` command should be available from command line

## Usage Examples

### Basic Usage (Batch)
```cmd
create_update_package.bat
```

### PowerShell with Parameters
```powershell
# Basic usage
.\create_update_package.ps1

# Custom output path
.\create_update_package.ps1 -OutputPath "C:\Updates"

# Custom version
.\create_update_package.ps1 -Version "v1.2.3"

# Force overwrite existing file
.\create_update_package.ps1 -Force
```

## What's Included

The package includes:
- ✅ All source code and Python files
- ✅ Configuration files and presets
- ✅ Documentation and guides
- ✅ Character cards and settings
- ✅ API modules and utilities

## What's Excluded

The package excludes:
- ❌ Virtual environments (`venv/`)
- ❌ Log files (`*.log`, `logs/`, `Logs/`)
- ❌ Temporary files (`*.tmp`, `*.pyc`, `__pycache__/`)
- ❌ Git repository (`.git/`, `.gitignore`)
- ❌ Environment files (`.env`, `.envrc`)
- ❌ Test files (`test_*.py`, `*_test.py`)
- ❌ Development tools (`.vscode/`, `.idea/`)
- ❌ CI/CD files (`.github/`, `.gitlab-ci.yml`, etc.)
- ❌ Backup files (`*.bak`, `*.backup`)

## Output Format

The generated RAR file follows this naming convention:
```
z-waif_update_YYMMDD_HHMM.rar
```

Where:
- `YY` = Year (last 2 digits)
- `MM` = Month (2 digits)
- `DD` = Day (2 digits)
- `HH` = Hour (24-hour format)
- `MM` = Minute (2 digits)

Example: `z-waif_update_250709_1430.rar` (July 9, 2025 at 2:30 PM)

## Distribution

The created RAR file is ready for:
- 📦 Distribution to users
- 🔄 Version updates
- 💾 Backup purposes
- 🚀 Release packages

## Troubleshooting

### "WinRAR not found" Error
1. Install WinRAR from the official website
2. Ensure WinRAR is added to your system PATH
3. Restart your command prompt/PowerShell

### "Permission denied" Error
1. Run as Administrator
2. Check write permissions in the output directory
3. Ensure the output file isn't open in another program

### "File already exists" Error
- Use the `-Force` parameter in PowerShell
- Or manually delete the existing file first

## File Size Optimization

The scripts automatically exclude unnecessary files to keep the package size minimal. Typical package sizes:
- **Small project**: 5-15 MB
- **Medium project**: 15-50 MB  
- **Large project**: 50-200 MB

## Security Notes

- The package excludes sensitive files like `.env` and `.envrc`
- No personal data or logs are included
- Test files are excluded to reduce size
- Development artifacts are filtered out 