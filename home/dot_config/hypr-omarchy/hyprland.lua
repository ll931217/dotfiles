-- Omarchy defaults with personal monitors, shortcuts, and session services.
local config_dir = os.getenv("HOME") .. "/.config/hypr-omarchy"
package.path = config_dir .. "/?.lua;" .. package.path

for _, module in ipairs({ "omarchy-looknfeel", "omarchy-input-env", "omarchy-windows" }) do
	package.loaded[module] = nil
	require(module)
end

hl.monitor({ output = "", mode = "preferred", position = "auto", scale = 1 })
hl.monitor({
	output = "HDMI-A-1",
	mode = "1920x1080@119.98",
	position = "0x0",
	scale = 1,
	transform = 1,
})
hl.monitor({ output = "DP-1", mode = "2560x1440@59.95", position = "1080x0", scale = 1 })
hl.on("hyprland.start", function()
	if os.getenv("OMARCHY_INSPIRED_TEST") ~= "1" then
		-- Export the explicit graphical/input-method environment before helpers.
		hl.exec_cmd("/usr/bin/python -I -B /home/ll931217/.config/hypr-omarchy/startup.py")
	end
end)

-- Keep Tokyo Night colors and personal focus/lock behavior over upstream defaults.
hl.config({
	general = {
		col = {
			active_border = "rgba(7aa2f7ff)",
			inactive_border = "rgba(414868ff)",
		},
	},
	group = {
		col = {
			border_active = "rgba(7aa2f7ff)",
			border_inactive = "rgba(414868ff)",
		},
	},
	misc = {
		focus_on_activate = false,
		anr_missed_pings = 5,
		allow_session_lock_restore = false,
	},
	cursor = { hide_on_key_press = false, warp_on_change_workspace = 0 },
	binds = { workspace_back_and_forth = true, hide_special_on_workspace_change = false },
})

require("keyboard")
hl.bind("SUPER + mouse:272", hl.dsp.window.drag(), { mouse = true })
hl.bind("SUPER + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- Only the native clipboard image editor; leave the screenshot helper unchanged.
hl.window_rule({
	name = "omarchy-clipboard-image-editor",
	match = { class = "^org[.]omarchy[.]ClipboardImage$" },
	float = true,
	center = true,
	size = { "80%", "80%" },
	max_size = { "80%", "80%" },
})

-- Keep the synchronizer's exact import statement, with a block-local data loader.
-- Missing/corrupt generated colors leave the personal defaults above intact.
do
	local dofile = require("appearance").load
	hl.config(dofile("/home/ll931217/.local/state/omarchy-inspired/native-ui/current/hyprland.lua"))
end
