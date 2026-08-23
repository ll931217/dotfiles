# AwesomeWM Configuration

This directory contains a migrated i3 configuration for AwesomeWM.

## Files

- **rc.lua** - Main AwesomeWM configuration file
- **theme.lua** - Color scheme and styling
- **wibar.lua** - Status bar widget

## Installation

The config is already symlinked to `~/.config/awesome/awesome/`.

To use AwesomeWM, change your display manager (e.g., lightdm, gdm) to use awesome instead of i3.

## Keybindings

All your i3 keybindings have been migrated:

### Modifiers
- `Mod` = Super/Windows key
- `Shift` = Shift
- `Ctrl` = Control

### Navigation
- `Mod+h/j/k/l` - Focus left/down/up/right
- `Mod+Shift+h/j/k/l` - Swap windows in direction
- `Mod+1-0` - Switch to tags (workspaces)
- `Mod+Shift+1-0` - Move window to tag

### Window Management
- `Mod+Return` - Open Alacritty
- `Mod+q` - Close window
- `Mod+f` - Toggle fullscreen
- `Mod+d` - Rofi launcher
- `Mod+Shift+space` - Toggle floating
- `Mod+a` - Toggle scratchpad
- `Mod+Shift+a` - Move to scratchpad

### Modes
- `Mod+r` - Resize mode (use hjkl or arrows, Esc to exit)
- `Mod+Shift+g` - Gaps mode (o=outer, i=inner, Esc to exit)
- `Mod+Shift+e` - Exit mode (L=logout, R=reboot, P=poweroff)

### Special Keys
- `Mod+s` - Focus Spotify (starts it if not running)
- `Mod+o` - Copy password to clipboard
- `Mod+Shift+q` - Power menu (rofi)
- `Mod+Shift+s` - Screenshot (flameshot)
- `Mod+Shift+t` - Random wallpaper
- `Mod+Shift+n` - NSFW wallpaper
- `Mod+Shift+x` - Lock screen
- `Mod+Shift+c` - Reload AwesomeWM config

### Media Keys
All media keys work (volume, brightness, playback controls).

## Features Migrated

### 1. Full i3-like experience
- HJKL navigation
- Tag-based workspaces
- Scratchpad support
- Floating windows
- Gap controls
- Status bar (similar to i3bar)

### 2. Per-side borders for Alacritty
Alacritty windows show a **left red border** when focused:
- Red (#f44336) 3px border on the left side
- Transparent (invisible) when unfocused
- Uses AwesomeWM's titlebar system to achieve this

The implementation is in `rc.lua` under the "Per-side borders for Alacritty" section.

### 3. Autostart Programs
All your i3 autostart programs are preserved:
- pipewire
- fcitx5 (input method)
- dunst (notifications)
- Screen layout (DP-0 primary, HDMI-0 rotated left)
- picom (compositor)
- feh (wallpaper)

### 4. Window Rules
All your window rules have been converted to AwesomeWM format:
- Browsers (Brave, Firefox, zen) → Tag 1 or 2
- Gaming (Steam, Lutris, winboat) → Tag 5 or 7, floating
- Discord → Tag 8
- Spotify → Tag 9
- mpv → Tag 10

### 5. Color Scheme
Uses your exact i3 color scheme:
- Accent color: #f44336 (red)
- Background: #2f343f
- Text: #f3f4f5
- Status bar: #1e293b with #f1f5f9 text

## Testing AwesomeWM

To test without switching your display manager:

1. From your current i3 session:
   ```bash
   awesome
   ```

2. If you like it, make it permanent by updating your display manager config.

## Differences from i3

### Tags vs Workspaces
- i3 has numbered workspaces (1-10)
- AwesomeWM uses **tags** which are more flexible
- A window can have multiple tags
- You can view multiple tags at once

### Titlebars
- AwesomeWM has built-in titlebars
- We use them for the per-side Alacritty border feature
- Can add custom buttons/widgets to titlebars

### Layouts
- AwesomeWM has many built-in layouts
- `Mod+Shift+space` toggles between them
- We only use tile layout by default (like i3)

### Lua Config
- Configuration is written in Lua (more powerful than i3's simple config)
- Full programming language available
- Can create custom widgets, layouts, etc.

## Testing & Troubleshooting

### Quick Test
Run the test script to check for syntax errors:
```bash
~/.config/awesome/test.sh
```

Or manually test with:
```bash
awesome -k
```

### If AwesomeWM won't start:
1. Check logs: `journalctl -u awesome -xe`
2. View logs: `less ~/.local/share/awesome/awesome.0000.log`
3. Check config for Lua syntax errors

### Common Issues

**"unexpected symbol near"** - Lua syntax error in rc.lua
**"cannot open"** - Missing theme.lua or other files
**"no screens"** - Check xrandr/screen layout in autostart

### Testing Without Switching DM

To test AwesomeWM without changing your display manager:

```bash
awesome
```

Press `Mod+Shift+c` to reload config while testing.

## Customization

To customize:
- **Keybindings**: Edit `rc.lua` in the keybindings section
- **Colors**: Edit `theme.lua` color variables
- **Layouts**: Add to `layouts` table in `rc.lua`
- **Window rules**: Edit `awful.rules.rules` in `rc.lua`
- **Autostart**: Edit `autostart` table in `rc.lua`

## Resources

- AwesomeWM docs: https://awesomewm.org/doc/api/
- AwesomeWM wiki: https://awesomewm.org/wiki/
- Lua reference: https://www.lua.org/manual/5.4/
