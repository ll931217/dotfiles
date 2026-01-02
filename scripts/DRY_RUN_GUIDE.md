# Dry Run Mode Guide

The dotfiles installer supports a `--dry-run` flag that allows you to test the installation without making any changes to your system.

## Usage

```bash
cd ~/GitHub/dotfiles/scripts
./install.sh --dry-run
```

## What Dry Run Does

In dry-run mode, the installer:

### ✅ What Happens
- Shows you what packages would be installed
- Displays what symlinks would be created
- Shows what configuration files would be modified
- Detects and reports your system setup (VM, monitors, WM, DM)
- Lists all steps that would be executed
- Logs everything to `/tmp/dotfiles-dryrun.log`

### ❌ What Doesn't Happen
- NO packages are installed
- NO symlinks are created
- NO configuration files are modified
- NO system services are enabled
- NO sudo commands are executed

## Use Cases

### 1. Testing in a VM
Perfect for testing the installer in a virtual machine before running on your main system:
```bash
# In your VM
./install.sh --dry-run
# Review the output
# Run for real when satisfied
./install.sh
```

### 2. Previewing Changes
See exactly what would change on your system:
```bash
./install.sh --dry-run | tee my-preview.txt
# Review the preview file
```

### 3. Validating Environment
Check if your system meets requirements without committing to installation:
```bash
./install.sh --dry-run
# Check for any warnings or errors
```

### 4. Documentation/Debugging
Generate a complete installation plan for documentation purposes:
```bash
./install.sh --dry-run > installation-plan.txt
cat /tmp/dotfiles-dryrun.log
```

## Dry Run Output Format

### Example Output

```
[INFO] Starting dotfiles installation...
[INFO] Installation log: /tmp/dotfiles-dryrun.log
[INFO] Running on bare metal
[SUCCESS] yay is already installed
[INFO] Detecting connected monitors...
[INFO] Found 2 monitor(s):
[INFO]   - DP-0
[INFO]   - HDMI-0

Installation Summary:
  Window Manager: i3
  Display Manager: sddm (Install: true)
  Monitors: 2
  VM: none
  Mode: DRY RUN (no changes will be made)

=========================================
DRY RUN MODE - No changes will be made
=========================================

[INFO] Starting installation process...
[INFO] === Installing core dependencies ===
[INFO] Updating system packages...
[DRY RUN] Would execute: sudo pacman -Syu --noconfirm
[INFO] Installing core utilities...
[DRY RUN] Would install 45 core packages:
[DRY RUN]   - base-devel
[DRY RUN]   - git
[DRY RUN]   - curl
...
```

## Reading the Log

After running dry-run, check the detailed log:
```bash
cat /tmp/dotfiles-dryrun.log
```

The log contains:
- All detected system information
- Complete list of packages to install
- All configuration changes that would be made
- All symlinks that would be created
- All commands that would be executed

## From Dry Run to Real Installation

Once you've reviewed the dry-run output and are satisfied:

### Option 1: Simple Re-run
```bash
# Just remove the flag
./install.sh
```

### Option 2: Review with Help
```bash
# Check what the flag does
./install.sh --help
```

### Option 3: Specific Testing
You can run dry-run multiple times with different configurations:
```bash
# Test with i3
./install.sh --dry-run
# Choose i3 when prompted

# Test with Hyprland
./install.sh --dry-run
# Choose Hyprland when prompted
```

## Dry Run Implementation

The `--dry-run` flag works by:

1. **Setting a global variable**: `DRY_RUN=true` is exported
2. **Passing to sub-scripts**: All sub-scripts inherit this variable
3. **Wrapper functions**: Commands are wrapped in `dry_run_cmd()` which:
   - Checks if `DRY_RUN` is true
   - If yes: logs the command without executing
   - If no: executes the command normally

### Example Implementation

```bash
# In sub-script
[[ -n "$DRY_RUN" ]] || DRY_RUN=false

dry_run_cmd() {
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would execute: $*"
        return 0
    else
        eval "$@"
    fi
}

# Usage
dry_run_cmd "sudo pacman -S --noconfirm neovim"
```

## Limitations

### What Dry Run Cannot Predict
- **Network availability**: Cannot check if downloads will succeed
- **Package availability**: Assumes all packages exist in repos
- **Disk space**: Does not check if you have enough space
- **Permission issues**: Cannot predict sudo password prompts
- **User prompts**: Will still prompt for WM selection, DM choice, etc.

### What Dry Run Can Show
- Exact command syntax that would be used
- Package names and versions
- File paths that would be modified
- Configuration templates that would be applied
- Monitor detection results
- VM detection results

## Troubleshooting Dry Run

### Dry Run Shows Errors
```
[ERROR] Cannot find repository fonts
```
This means the real installation would also fail. Fix the issue before running the real installation.

### Dry Run Doesn't Show Expected Packages
Check that the package names in the scripts are correct for Arch Linux:
```bash
pacman -Ss <package-name>
```

### Dry Run Output Too Long
Pipe to less:
```bash
./install.sh --dry-run | less
```

Or save to a file:
```bash
./install.sh --dry-run > dry-run-output.txt
```

## Best Practices

### 1. Always Dry Run First
```bash
./install.sh --dry-run
# Review output
./install.sh
```

### 2. Save Dry Run Logs
```bash
./install.sh --dry-run
cp /tmp/dotfiles-dryrun.log ~/dotfiles-dryrun-$(date +%Y%m%d).log
```

### 3. Compare Before/After
```bash
# Before installation
pacman -Q | sort > packages-before.txt

./install.sh

# After installation
pacman -Q | sort > packages-after.txt
diff packages-before.txt packages-after.txt
```

### 4. Test Each Script Separately
```bash
# Test just dependency installation
DRY_RUN=true bash 01-dependencies.sh

# Test just font installation
DRY_RUN=true bash 02-fonts.sh
```

## Summary

The `--dry-run` flag is a powerful feature for:
- ✅ Safe testing without risk
- ✅ Previewing all changes
- ✅ Debugging installation logic
- ✅ Creating installation documentation
- ✅ Validating system compatibility

**Remember**: Dry run is safe. It cannot modify your system in any way.

Use it liberally to understand what the installer will do before committing to changes!
