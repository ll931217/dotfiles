-- AwesomeWM Theme
-- Based on your i3 color scheme

local theme = {}

-- {{{ Font
theme.font = "JetBrainsMonoNL Nerd Font Medium 8"
theme.titlebar_font = "JetBrainsMonoNL Nerd Font Medium 8"
-- }}}

-- {{{ Colors
theme.bg_normal  = "#2f343f"
theme.bg_focus   = "#f44336"
theme.bg_urgent   = "#E53935"

theme.fg_normal  = "#676E7D"
theme.fg_focus   = "#f3f4f5"
theme.fg_urgent   = "#f3f4f5"

theme.border_width  = 2
theme.border_normal = "#2f343f"
theme.border_focus  = "#f44336"
theme.border_marked = "#91231e"

-- Titlebar colors for per-side border feature
theme.titlebar_bg_normal  = "#00000000"  -- Transparent
theme.titlebar_bg_focus   = "#f44336"    -- Red when focused
theme.titlebar_fg_normal  = "#f3f4f5"
theme.titlebar_fg_focus   = "#f3f4f5"
-- }}}

-- {{{ Gaps (like i3-gaps)
theme.useless_gap_width = 5
theme.gap_single_client = true
-- }}}

-- {{{ Wibar (status bar)
theme.wibar_height = 24
theme.wibar_bg = "#1e293b"
theme.wibar_fg = "#f1f5f9"

-- Taglist colors
theme.taglist_bg_empty    = "#1e293b"
theme.taglist_bg_occupied = "#1e293b"
theme.taglist_bg_urgent   = "#1e293b"
theme.taglist_fg_empty    = "#64748b"
theme.taglist_fg_occupied = "#64748b"
theme.taglist_fg_urgent   = "#ef4444"
theme.taglist_fg_focus    = "#06b6d4"

-- Tasklist colors
theme.tasklist_bg_normal = "#1e293b"
theme.tasklist_bg_focus  = "#06b6d4"
theme.tasklist_fg_normal = "#64748b"
theme.tasklist_fg_focus  = "#f1f5f9"

-- Hotkeys popup
theme.hotkeys_bg = "#1e293b"
theme.hotkeys_fg = "#f1f5f9"
theme.hotkeys_border_width = 1
theme.hotkeys_border_color = "#06b6d4"
theme.hotkeys_modifiers_fg = "#06b6d4"
-- }}}

-- {{{ Layout icons
theme.layout_fairh           = "/usr/share/awesome/themes/default/layouts/fairhw.png"
theme.layout_fairv           = "/usr/share/awesome/themes/default/layouts/fairvw.png"
theme.layout_floating        = "/usr/share/awesome/themes/default/layouts/floatingw.png"
theme.layout_magnifier       = "/usr/share/awesome/themes/default/layouts/magnifierw.png"
theme.layout_max             = "/usr/share/awesome/themes/default/layouts/maxw.png"
theme.layout_fullscreen      = "/usr/share/awesome/themes/default/layouts/fullscreenw.png"
theme.layout_tilebottom      = "/usr/share/awesome/themes/default/layouts/tilebottomw.png"
theme.layout_tileleft        = "/usr/share/awesome/themes/default/layouts/tileleftw.png"
theme.layout_tile            = "/usr/share/awesome/themes/default/layouts/tiletopw.png"
theme.layout_tiletop         = "/usr/share/awesome/themes/default/layouts/tiletopw.png"
theme.layout_spiral          = "/usr/share/awesome/themes/default/layouts/spiralw.png"
theme.layout_dwindle         = "/usr/share/awesome/themes/default/layouts/dwindlew.png"
theme.layout_cornernw        = "/usr/share/awesome/themes/default/layouts/cornernww.png"
theme.layout_cornerne        = "/usr/share/awesome/themes/default/layouts/cornernew.png"
theme.layout_cornersw        = "/usr/share/awesome/themes/default/layouts/cornersww.png"
theme.layout_cornerse        = "/usr/share/awesome/themes/default/layouts/cornersew.png"
-- }}}

-- {{{ Icon theme
theme.awesome_icon = "/usr/share/awesome/themes/default/awesome64.png"
-- }}}

return theme
