# Dotfiles Provisioning Scripts

The default installation entrypoint is the repository root:

```bash
./install.sh
```

That command delegates to `bootstrap/install.sh`, which initializes and applies
the chezmoi source state under `../home/`.

## Chezmoi Workflow

Preview changes without modifying the home directory:

```bash
./install.sh --dry-run
```

Initialize without applying:

```bash
./install.sh --no-apply
```

The package hook is opt-in. Set `machine.install_packages = true` in
`../home/.chezmoidata.toml` only after reviewing the package lists. Set
`machine.install_optional = true` separately for AUR/Homebrew optional
packages.

## Legacy Installer Reference

The legacy installer remains available for migration comparison only:

```bash
./scripts/install.sh --dry-run
```

It is Arch/Linux-specific and owns package installation, AUR setup, display
manager configuration, window-manager selection, generated configuration,
symlink creation, backups, snapshots, profiles, and uninstall behavior.

Those responsibilities are being replaced in stages:

- chezmoi owns home-directory files and rendered templates;
- `.chezmoidata.toml` owns package and machine defaults;
- `run_*` hooks own narrowly scoped package and post-apply actions;
- legacy state and rollback code remains available until real-machine cutover
  is complete.

Do not run the legacy installer against files already managed by chezmoi.
Doing so can replace managed files with symlinks and create conflicting backup
state.

## Troubleshooting

Preview the target changes:

```bash
./install.sh --dry-run
```

If package installation is enabled and fails, check the package manager and
the rendered package hook:

```bash
chezmoi execute-template < home/run_onchange_before_10-install-packages.sh.tmpl
```

Refresh Linux font caches manually when needed:

```bash
fc-cache -f "$HOME/.local/share/fonts"
```

Window-manager configuration remains platform and machine specific. Review
`home/.chezmoidata.toml` and `home/.chezmoiignore.tmpl` before enabling i3 or
Hyprland content.

## Migration Rules

- Never add `.config/zsh/keys.zsh` to chezmoi source state.
- Rotate existing credentials before adding password-manager-backed templates.
- Keep generated logs, receipts, profiles, and backups outside source state.
- Validate changes in a disposable home directory before applying to the live
  account.

## License

MIT License - See main repository for details.
