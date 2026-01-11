local wezterm = require("wezterm")

local function font_with_fallback(name, params)
	local names = { name }
	return wezterm.font_with_fallback(names, params)
end

local font_name = "JetBrainsMonoNL Nerd Font"

local config = {
	-- OpenGL for GPU acceleration
	front_end = "OpenGL",

	-- Use built-in color scheme to avoid loading errors
	colors = {
		foreground = "#ffffff",
		background = "#1e1e1e",
		cursor_bg = "#ffffff",
		cursor_border = "#ffffff",
		cursor_fg = "#000000",
		selection_bg = "#444444",
		selection_fg = "#ffffff",
		ansi = {"#000000", "#ff0000", "#00ff00", "#ffff00", "#0000ff", "#ff00ff", "#00ffff", "#ffffff"},
		brights = {"#555555", "#ff5555", "#55ff55", "#ffff55", "#5555ff", "#ff55ff", "#55ffff", "#ffffff"},
	},

	-- Simplified font config for performance
	font = font_with_fallback(font_name),
	font_size = 10,
	line_height = 1.0,

	-- Cursor style
	default_cursor_style = "BlinkingUnderline",

	-- Keybinds (unchanged)
	disable_default_key_bindings = true,
	keys = {
		{
			key = [[\]],
			mods = "CTRL|ALT",
			action = wezterm.action({
				SplitHorizontal = { domain = "CurrentPaneDomain" },
			}),
		},
		{
			key = [[\]],
			mods = "CTRL",
			action = wezterm.action({
				SplitVertical = { domain = "CurrentPaneDomain" },
			}),
		},
		{
			key = "q",
			mods = "CTRL",
			action = wezterm.action({ CloseCurrentPane = { confirm = false } }),
		},
		{
			key = "h",
			mods = "CTRL|SHIFT",
			action = wezterm.action({ ActivatePaneDirection = "Left" }),
		},
		{
			key = "l",
			mods = "CTRL|SHIFT",
			action = wezterm.action({ ActivatePaneDirection = "Right" }),
		},
		{
			key = "k",
			mods = "CTRL|SHIFT",
			action = wezterm.action({ ActivatePaneDirection = "Up" }),
		},
		{
			key = "j",
			mods = "CTRL|SHIFT",
			action = wezterm.action({ ActivatePaneDirection = "Down" }),
		},
		{
			key = "h",
			mods = "CTRL|SHIFT|ALT",
			action = wezterm.action({ AdjustPaneSize = { "Left", 1 } }),
		},
		{
			key = "l",
			mods = "CTRL|SHIFT|ALT",
			action = wezterm.action({ AdjustPaneSize = { "Right", 1 } }),
		},
		{
			key = "k",
			mods = "CTRL|SHIFT|ALT",
			action = wezterm.action({ AdjustPaneSize = { "Up", 1 } }),
		},
		{
			key = "j",
			mods = "CTRL|SHIFT|ALT",
			action = wezterm.action({ AdjustPaneSize = { "Down", 1 } }),
		},
		{
			key = "t",
			mods = "CTRL",
			action = wezterm.action({ SpawnTab = "CurrentPaneDomain" }),
		},
		{
			key = "w",
			mods = "CTRL|SHIFT",
			action = wezterm.action({ CloseCurrentTab = { confirm = false } }),
		},
		{
			key = "Tab",
			mods = "CTRL",
			action = wezterm.action({ ActivateTabRelative = 1 }),
		},
		{
			key = "Tab",
			mods = "CTRL|SHIFT",
			action = wezterm.action({ ActivateTabRelative = -1 }),
		},
		{
			key = "x",
			mods = "CTRL",
			action = "ActivateCopyMode",
		},
		{
			key = "v",
			mods = "CTRL|SHIFT",
			action = wezterm.action({ PasteFrom = "Clipboard" }),
		},
		{
			key = "c",
			mods = "CTRL|SHIFT",
			action = wezterm.action({ CopyTo = "ClipboardAndPrimarySelection" }),
		},
	},

	-- Performance optimizations
	bold_brightens_ansi_colors = false, -- Disable for better performance
	
	-- Reduced padding
	window_padding = {
		left = 10,
		right = 10,
		top = 8,
		bottom = 8,
	},

	-- Tab Bar
	enable_tab_bar = true,
	hide_tab_bar_if_only_one_tab = true,
	show_tab_index_in_tab_bar = false,
	tab_bar_at_bottom = false,
	use_fancy_tab_bar = false, -- Disable fancy tab bar for performance

	-- General
	automatically_reload_config = false, -- Disable auto-reload
	inactive_pane_hsb = { saturation = 1.0, brightness = 1.0 },
	window_background_opacity = 1.0, -- Remove transparency for performance
	window_close_confirmation = "NeverPrompt",
}

-- Fixed Wayland detection for Sway
if os.getenv("XDG_SESSION_TYPE") == "wayland" then
	config.enable_wayland = true
else
	config.enable_wayland = false
end

return config
