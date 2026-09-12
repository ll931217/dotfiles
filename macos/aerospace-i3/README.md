# i3-inspired AeroSpace profile

Opt-in profile tested on Intel Sonoma with AeroSpace 0.12.0 and SketchyBar
2.23.0. It adapts the navigation and resize behavior in
`home/dot_config/i3/config`, while keeping native macOS Command shortcuts.

## Why a separate profile

The active Mac used `~/.config/aerospace/aerospace.toml` and a shell-based
SketchyBar configuration. The repository's `home/dot_aerospace.toml` and
`home/dot_config/sketchybar` instead describe a different, Lua-based setup.
Those sources and the legacy `macos/.aerospace.toml` are intentionally unchanged.
Do not apply the Lua setup on top of this shell profile. A full chezmoi apply
can replace the bar and create a second AeroSpace config; review its diff first.

## Shortcuts

Use Option in place of Linux Mod4. Command-Q, Command-Tab, Command-Space,
Command-R and normal typing remain available to macOS and applications.

| Shortcut | Action |
| --- | --- |
| Option + H/J/K/L | Focus left/down/up/right without wrapping |
| Option + Shift + H/J/K/L | Move window |
| Option + 1–9 / 0 | Workspace 1–9 / 10; repeat to return |
| Option + Shift + 1–9 / 0 | Send window without following |
| Option + B/I/S/T | Existing browser/IDE/chat/terminal workspaces |
| Option + Shift + B/I/S/T | Send window to corresponding workspace |
| Option + Return | Open Alacritty |
| Option + F | Tiled fullscreen |
| Option + Shift + F | Native macOS fullscreen |
| Option + Shift + Space | Toggle floating |
| Option + R | Resize mode; H/J shrink, K/L grow; arrows also work |
| Option + G | Join mode; H/J/K/L select direction |
| Option + backslash / V | Horizontal / vertical split |
| Option + slash / comma | Tile orientation / accordion layout |
| Option + Tab | Previous workspace |
| Option + Shift + Tab | Move workspace to next monitor |
| Option + Shift + C | Reload AeroSpace |
| Escape / Return in a mode | Return to normal controls |

Existing Option-Shift-R and Option-Shift-semicolon remain resize/service
shortcuts. Resize/join/service bindings show a bar indicator. Direct CLI mode
changes do not update that indicator. Reloading the bar clears it.

## Shell bar integration

The bar uses the i3 palette, a solid 30-point background, numbered/lettered
workspace buttons with one identifier each. Empty workspaces stay clickable.
Full repairs query real state instead of trusting optional event variables.
Workspace switching directly updates only the previous and focused highlights;
it does not rebuild buttons or dispatch another SketchyBar event. Full workspace
mutations are batched, and no per-window icon lookup is needed. Display/wake
events rebuild state when needed; there is no periodic rebuild. Workspace names are restricted
to letters, numbers, underscores and hyphens before creating click commands.

Install these mappings only into the existing shell bar, after backing it up:

| Source | Active target |
| --- | --- |
| `aerospace.toml` | `~/.config/aerospace/aerospace.toml` |
| `spaces.sh` | `~/.config/sketchybar/items/spaces.sh` |
| `workspaces.sh` | `~/.config/sketchybar/plugins/spaces.sh` |
| `front_app.sh` | `~/.config/sketchybar/plugins/front_app.sh` |
| `appearance.sh` | `~/.config/sketchybar/items/appearance.sh` |
| `colors.sh` | `~/.config/sketchybar/colors.sh` |

In the existing `sketchybarrc`, source `"$ITEM_DIR/appearance.sh"` immediately
before `"$ITEM_DIR/spaces.sh"`. Preserve executable permission on the front-app
plugin. Keep SketchyBar registered as a user launchd service; AeroSpace's
startup command reloads the bar, it does not launch a second daemon.
Both Homebrew prefixes are included in the AeroSpace subprocess PATH.

Keep exactly one active AeroSpace config: do not also create `~/.aerospace.toml`.
Validate before reloading:

```sh
python3 -m unittest discover -s macos/aerospace-i3 -v
aerospace reload-config --dry-run --no-gui
aerospace reload-config --no-gui
sketchybar --reload
```

Tests require Python 3.11+ and mock the applications without moving windows.
`bash -n` checks each shell file; live queries verify the loaded bar state.

## Current-machine rollback

The pre-change files are preserved in
`~/.config/aerospace-backup.M2mwXi/`. Restore its `aerospace.toml` to the active
XDG path and its `sketchybar` files to `~/.config/sketchybar`, then validate and
reload as above. The additional `items/appearance.sh` is inert once the original
`sketchybarrc` is restored. No app restart or logout is required.

This does not reproduce i3 scratchpads, parent-container focus, or native tabbed
containers: the installed AeroSpace does not provide direct equivalents.
No existing windows are reassigned during deployment. New Brave windows go to
B; System Settings floats. Existing routing rules otherwise remain in place.
