-- Adapted from /home/ll931217/GitHub/_RICE/omarchy/default/hypr/{windows.lua,apps/pip.lua,apps/system.lua}.
hl.window_rule({
  name = "omarchy-suppress-maximize",
  match = { class = ".*" },
  suppress_event = "maximize",
})

-- Like i3's gaming rules, float launchers without treating them as games.
hl.window_rule({
  name = "omarchy-game-launchers",
  match = { class = "^(steam|Steam|lutris|net[.]lutris[.]Lutris|itch)$" },
  float = true,
  center = true,
  border_size = 0,
})

-- Numbered Steam app IDs identify games; steam_app_default also includes
-- Battle.net and Wine helper/tray windows, so never match that class alone.
hl.window_rule({
  name = "omarchy-steam-games-fullscreen",
  match = { class = "^steam_app_[0-9]+$" },
  fullscreen = true,
})
hl.window_rule({
  name = "omarchy-wine-games-fullscreen",
  match = {
    class = "^(steam_app_default|[Ww]ow[.]exe|[Ww]ow[Cc]lassic[.]exe|[Pp]ath[Oo]f[Ee]xile.*[.]exe)$",
    title = "^(World of Warcraft|Path of Exile|Path of Exile 2)$",
  },
  -- Wine/Proton can undo fullscreen when told to switch display modes.
  -- Fill the monitor without changing the game's own fullscreen mode.
  fullscreen_state = "2 0",
})

hl.window_rule({
  name = "omarchy-xwayland-empty-drag",
  match = {
    class = "^$",
    title = "^$",
    xwayland = true,
    float = true,
    fullscreen = false,
    pin = false,
  },
  no_focus = true,
})

hl.window_rule({
  name = "omarchy-picture-in-picture",
  match = { title = "(Picture.?in.?[Pp]icture)" },
  float = true,
  pin = true,
  size = { 600, 338 },
  keep_aspect_ratio = true,
  border_size = 0,
  move = { "(monitor_w-window_w-40)", "(monitor_h*0.04)" },
})

-- Scoped to capture.py's editor; monitor-relative sizing leaves room to move it.
hl.window_rule({
  name = "omarchy-screenshot-editor",
  match = { class = "^com[.]omarchy[.]Screenshot$" },
  float = true,
  center = true,
  size = { "80%", "80%" },
  max_size = { "80%", "80%" },
})

hl.window_rule({
  name = "omarchy-portal-dialogs",
  match = { class = "xdg-desktop-portal-gtk" },
  float = true,
  center = true,
  size = { 875, 600 },
})

hl.window_rule({
  name = "omarchy-file-dialogs",
  match = {
    class = "(sublime_text|DesktopEditors|org.gnome.Nautilus)",
    title = "^(Open.*Files?|Open [F|f]older.*|Save.*Files?|Save.*As|Save|All Files|.*wants to [open|save].*|[C|c]hoose.*)",
  },
  float = true,
  center = true,
  size = { 875, 600 },
})
