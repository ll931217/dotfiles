# Installation Scripts Changelog

## [2026-01-02] - Dry Run Mode Added

### New Features

#### Dry Run Mode (`--dry-run`)
- Added `--dry-run` flag to `install.sh`
- Safe testing without making any system changes
- Perfect for testing in VMs before real installation

#### Dry Run Implementation
All scripts now support dry-run mode:
- `install.sh` - Main orchestrator with dry-run flag parsing
- `01-dependencies.sh` - Shows packages without installing
- `02-fonts.sh` - Shows font operations without downloading
- `03-create-symlinks.sh` - Shows symlinks without creating
- `04-install-wm.sh` - Shows WM/DM installation without executing
- `05-configure-wm.sh` - Shows config changes without modifying
- `06-neovim.sh` - Shows NeoVim setup without cloning

#### Dry Run Behavior
When `--dry-run` is enabled:
- ✅ Logs all commands that would be executed
- ✅ Shows all packages that would be installed
- ✅ Displays all symlinks that would be created
- ✅ Reports all configuration changes
- ✅ Detects and reports system setup (VM, monitors, WM, DM)
- ❌ NO system modifications
- ❌ NO package installations
- ❌ NO file changes

#### Logging
- Regular installation: `/tmp/dotfiles-install.log`
- Dry run installation: `/tmp/dotfiles-dryrun.log`
- All actions logged with timestamp
- Dry-run commands prefixed with `[DRY RUN]`

#### Help System
- Added `-h` / `--help` flag
- Shows usage information
- Documents `--dry-run` functionality

### Documentation

#### New Documentation Files
- `DRY_RUN_GUIDE.md` - Comprehensive guide for dry-run mode
  - Usage examples
  - What dry run does and doesn't do
  - Use cases (VM testing, previewing changes, validation)
  - Best practices
  - Troubleshooting

#### Updated Documentation
- `README.md` - Added dry-run mode section
- Links to `DRY_RUN_GUIDE.md` for detailed information
- Updated usage examples

### Script Improvements

#### Better Error Handling
- All scripts have consistent error handling
- Dry-run mode gracefully handles missing dependencies
- Clear warning messages in dry-run mode

#### Better User Feedback
- Clear distinction between dry-run and normal mode
- `[DRY RUN]` prefix for all dry-run actions
- Summary message at end of dry-run
- Instructions to run without --dry-run for real installation

#### Better VM Detection
- VM type detected and reported
- VM-specific optimizations documented
- Multi-monitor detection works in dry-run

#### Better Monitor Detection
- Reports connected monitors clearly
- Shows monitor count
- Explains how configuration adapts

### Technical Details

#### Environment Variables
- `DRY_RUN` - Exported by main script to all sub-scripts
- `LOG_FILE` - Different log file for dry-run vs normal
- `VM_TYPE` - Detected and passed to sub-scripts
- `WM`, `DM`, `INSTALL_DM` - Configuration choices
- `MONITOR_COUNT`, `CONNECTED_MONITORS` - Hardware detection

#### Functions
- `dry_run_cmd()` - Wrapper for all potentially dangerous commands
  - Checks `DRY_RUN` flag
  - Logs command if dry-run enabled
  - Executes command if dry-run disabled
- Logging functions: `log()`, `success()`, `warn()`, `error()`
- Consistent across all scripts

### Installation Flow

1. Main installer parses `--dry-run` flag
2. Sets `DRY_RUN=true` if flag present
3. Exports to all sub-scripts
4. Each sub-script checks `DRY_RUN` variable
5. Commands wrapped in `dry_run_cmd()`
6. Dry-run: logs, Normal: executes
7. Final summary based on mode

### Usage Examples

#### Test in VM
```bash
# In your VM
./install.sh --dry-run
# Review output
# Run for real when satisfied
./install.sh
```

#### Preview Installation
```bash
# See what would be installed
./install.sh --dry-run

# Save output to review later
./install.sh --dry-run | tee installation-plan.txt
```

#### Compare Before/After
```bash
# Before installation
pacman -Q | sort > packages-before.txt

./install.sh --dry-run

# After real installation
pacman -Q | sort > packages-after.txt
diff packages-before.txt packages-after.txt
```

### Benefits

#### Safety
- No risk of breaking system
- No package conflicts
- No configuration conflicts
- Can test repeatedly

#### Transparency
- See exactly what will happen
- Understand all changes
- Plan before executing
- Document installation process

#### Flexibility
- Test different configurations
- Compare i3 vs Hyprland
- Validate environment
- Perfect for VM testing

#### Debugging
- See installation logic
- Identify potential issues
- Validate package names
- Test hardware detection

### Migration

#### From Old install.sh
- Old `install.sh` kept as reference
- New modular system in `scripts/` directory
- `install-new.sh` wrapper for backward compatibility
- Can use either system

#### Legacy Support
- Original `install.sh` preserved
- Can be removed once comfortable with new system
- Documentation covers both approaches

### Future Enhancements

#### Potential Additions
- `--verbose` flag for more detailed output
- `--force` flag to skip confirmation prompts
- `--config` flag to load configuration from file
- Progress bars for long operations
- Rollback capability if installation fails

#### Testing
- Automated testing framework
- Test in multiple VM types
- Test with different monitor configurations
- Test with different package sets

### Compatibility

#### Platforms
- Arch Linux (primary target)
- Arch-based distributions
- VirtualBox, VMware, QEMU/KVM
- Bare metal systems

#### WMs
- i3-gaps (X11)
- Hyprland (Wayland)
- Single monitor
- Dual monitor

#### Display Managers
- SDDM (default)
- LightDM
- GDM
- Existing DM detection

---

## Previous Changes

### Initial Implementation
- Modularized installation into 7 scripts
- Support for i3-gaps and Hyprland
- Multi-monitor detection and configuration
- VM detection and optimizations
- Comprehensive documentation

