# Omarchy-inspired Hyprland with chezmoi

The existing profile and its session entrypoint are managed by chezmoi. They remain an **alternate session alongside i3**: this import does not change `machine.wm`, SDDM, boot, networking, credentials or running processes.

## Scope

- `home/dot_config/hypr-omarchy/` restores the Lua profile, key inventory, Python action/startup helpers, Rofi styling and manual-lock configuration to `~/.config/hypr-omarchy/`.
- `home/dot_local/bin/executable_omarchy-inspired-session` restores the existing session command, including its executable bit.
- Source is not templated or behaviorally rewritten. Imports match the installed files except for an explicit `str` parameter/return annotation on the keymap normalizer, needed to remove an existing Python type ambiguity. Chezmoi also normalizes that executable's permissions from `0744` to `0755` on restore. These differences are intentionally visible in the preview; the live file was not rewritten. The reviewed scripts contain `/home/ll931217` and host-specific monitor settings. The ignore guard limits deployment to personal Arch amd64 with that HOME, independently of whether i3 or Hyprland is selected as the default. This is **current-host configuration management, not a fresh-machine installer**.

The source directories deliberately are not `exact_`: applying this selection must not delete unmanaged files, the nested local Git repository, or other local assets.

## Dependencies retained outside chezmoi

The current desktop still requires the installed packages, Handy settings/models, `/usr/local/bin/st`, `~/.local/bin/xembedsniproxy`, the local `~/GitHub/_RICE/omarchy` upstream checkout, optimized binaries under `~/.local/opt/omarchy-integration/`, and the existing public helper code under `~/.local/share/omarchy-inspired/`. The AI entrypoint `~/.local/bin/omarchy-ai` and its helper modules also remain separately installed.

The system SDDM entry `/usr/local/share/wayland-sessions/omarchy-inspired.desktop` remains separately installed. Chezmoi does not create privileged session files or select a session for you. Existing personal wallpaper/assets remain local and are not published in the dotfiles repository.

**Never recursively add `~/.local/state/omarchy-inspired` or `~/.local/share/omarchy-inspired`.** The former contains private clipboard/notification data, accounts/usage, consent, runtime manifests, approvals, journals and recovery evidence. The latter includes manifest-bound adapters that cannot safely be overwritten while the native shell runs. Both are ignored; caches, backup files and the profile's nested Git metadata are ignored too. No credentials or runtime approvals were imported.

A fresh-machine installation needs a separately reviewed installer that provisions binaries/upstream dependencies, regenerates a private runtime, obtains consent and reviews the new hashes. Copying the current private runtime or its approvals is not an acceptable substitute.

## Preview and restore only this profile

Run from this existing host. Keep external refresh disabled and include only files/directories so unrelated package hooks cannot execute. Explicit recursion is important: without it, a directory diff can omit changed files inside the profile.

```bash
chezmoi --refresh-externals=never --skip-secrets diff --recursive --include=files \
  ~/.config/hypr-omarchy ~/.local/bin/omarchy-inspired-session
chezmoi --refresh-externals=never --skip-secrets apply --dry-run --recursive --include=files,dirs \
  ~/.config/hypr-omarchy ~/.local/bin/omarchy-inspired-session
```

Review the preview before removing `--dry-run`. Do not run a broad apply for this migration. Applying the files does not restart services, activate a desktop, import an environment or execute `startup.py`. Do not reload a changed live compositor configuration without reviewing its diff first. Any future changes to manifest-bound external adapters require their controlled drain/refresh/review lifecycle, not a chezmoi overwrite.

Confirm management and configuration without activation:

```bash
chezmoi source-path ~/.config/hypr-omarchy/startup.py
omarchy-inspired-session --check
python -I -B ~/.config/hypr-omarchy/startup.py --check
python -I -B ~/.local/share/omarchy-inspired/full-desktop/client.py --status
```

Fresh login, manual password unlock, Handy dictation and interactive tray/workspace acceptance remain user-operated. Do not force logout, lock, microphone capture or private clipboard inspection for verification.

## Keep intentional local edits

Use `chezmoi re-add` on **individual reviewed files**, then inspect the source diff. Do not add the entire live directory: it also contains caches, backups, local repositories and unreviewed assets. Chezmoi ignores prevent accidental deployment; they are not a secret scanner or permission to add private data.

The regression checks for this integration are `python -B -m unittest discover -s tests -p test_hypr_omarchy_chezmoi.py`. They render profile guards and exercise a disposable chezmoi source/destination; they never apply to the real desktop or run session hooks.
