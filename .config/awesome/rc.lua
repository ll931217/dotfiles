-- AwesomeWM Configuration
-- Based on your i3 config migration

-- {{{ Standard libraries
local gears = require("gears")
local awful = require("awful")
require("awful.autofocus")
local wibox = require("wibox")
local beautiful = require("beautiful")
local naughty = require("naughty")
local hotkeys_popup = require("awful.hotkeys_popup")
-- }}}

-- {{{ Debug logging
local debug_log_file = os.getenv("HOME") .. "/.awesome-debug.log"
local debug_enabled = true

local function debug_log(message)
    if not debug_enabled then return end

    -- Write to log file with timestamp
    local timestamp = os.date("%Y-%m-%d %H:%M:%S")
    local log_entry = string.format("[%s] %s\n", timestamp, message)

    -- Append to log file
    local f = io.open(debug_log_file, "a")
    if f then
        f:write(log_entry)
        f:close()
    end

    -- Also show notification
    naughty.notify({text = message, timeout = 3})
end

-- Clear log on startup
local f = io.open(debug_log_file, "w")
if f then
    f:write("=== AwesomeWM Debug Log ===\n")
    f:close()
end

debug_log("AwesomeWM starting up...")
-- }}}

-- Hotkeys popup is available via hotkeys_popup.show_help()

-- {{{ Notification configuration
naughty.config.defaults.timeout = 5
naughty.config.defaults.position = "top_right"
naughty.config.defaults.margin = 8
naughty.config.defaults.gap = 1
-- }}}

-- {{{ Error handling
if awesome.startup_errors then
    naughty.notify({
        preset = naughty.config.presets.critical,
        title = "Oops, errors during startup!",
        text = awesome.startup_errors
    })
end

do
    local in_error = false
    awesome.connect_signal("debug::error", function (err)
        if in_error then return end
        in_error = true

        naughty.notify({
            preset = naughty.config.presets.critical,
            title = "Oops, an error happened!",
            text = tostring(err)
        })
        in_error = false
    end)
end
-- }}}

-- {{{ Variable definitions
local modkey = "Mod4"
local altkey = "Mod1"
local terminal = "alacritty"

-- Load theme
beautiful.init(gears.filesystem.get_configuration_dir() .. "theme.lua")

-- {{{ Helper functions
local function client_menu_toggle_fn()
    local c = client.focus
    if not c then return end
end
-- }}}

-- {{{ Layouts
local layouts = {
    awful.layout.suit.tile,
    awful.layout.suit.tile.left,
    awful.layout.suit.tile.bottom,
    awful.layout.suit.tile.top,
    awful.layout.suit.fair,
    awful.layout.suit.fair.horizontal,
    awful.layout.suit.spiral,
    awful.layout.suit.spiral.dwindle,
    awful.layout.suit.max,
    awful.layout.suit.magnifier,
    awful.layout.suit.corner.nw,
    awful.layout.suit.corner.ne,
    awful.layout.suit.corner.sw,
    awful.layout.suit.corner.se,
    awful.layout.suit.floating
}
-- }}}

-- {{{ Menu
local myawesomemenu = awful.menu({ items = {
    { "hotkeys", function() hotkeys_popup.show_help(nil, awful.screen.focused()) end },
    { "manual", terminal .. " -e man awesome" },
    { "edit config", terminal .. " -e nvim ~/.config/awesome/rc.lua" },
    { "restart", awesome.restart },
    { "quit", function() awesome.quit() end }
    }
})

mylauncher = awful.widget.launcher({ menu = myawesomemenu })
-- }}}

-- {{{ Keyboard & Mouse
root.buttons(gears.table.join(
    awful.button({ }, 3, function () myawesomemenu:toggle() end),
    awful.button({ }, 4, awful.tag.viewnext),
    awful.button({ }, 5, awful.tag.viewprev)
))
-- }}}

-- {{{ Key bindings
local globalkeys = gears.table.join(
    -- Terminal
    awful.key({ modkey }, "Return", function() awful.spawn(terminal) end,
              {description = "open terminal", group = "launcher"}),
    awful.key({ modkey }, "d", function() awful.spawn("rofi -show drun") end,
              {description = "rofi launcher", group = "launcher"}),
    awful.key({ modkey, "Shift" }, "q", function() awful.spawn("~/.config/rofi/scripts/powermenu_t1") end,
              {description = "power menu", group = "launcher"}),

    -- Focus (hjkl like i3)
    awful.key({ modkey }, "h", function() awful.client.focus.bydirection("left") end),
    awful.key({ modkey }, "j", function() awful.client.focus.bydirection("down") end),
    awful.key({ modkey }, "k", function() awful.client.focus.bydirection("up") end),
    awful.key({ modkey }, "l", function() awful.client.focus.bydirection("right") end),

    -- Move windows (Shift+hjkl like i3)
    awful.key({ modkey, "Shift" }, "h", function() awful.client.swap.bydirection("left") end),
    awful.key({ modkey, "Shift" }, "j", function() awful.client.swap.bydirection("down") end),
    awful.key({ modkey, "Shift" }, "k", function() awful.client.swap.bydirection("up") end),
    awful.key({ modkey, "Shift" }, "l", function() awful.client.swap.bydirection("right") end),

    -- Fullscreen
    awful.key({ modkey }, "f", function()
        local c = client.focus
        if c then c.fullscreen = not c.fullscreen end
    end),

    -- Scratchpad
    awful.key({ modkey }, "a", function() toggle_scratchpad() end),
    awful.key({ modkey, "Shift" }, "a", function() move_to_scratchpad() end),

    -- Screenshot
    awful.key({ modkey, "Shift" }, "s", function() awful.spawn("flameshot gui") end),

    -- Copy password
    awful.key({ modkey }, "o", function() awful.spawn("cat ~/.pvt/pw | xclip -selection c") end),

    -- Bitwarden
    awful.key({ modkey, "Shift" }, "d", function() awful.spawn("rofi-rbw") end),

    -- Screen recording
    awful.key({ modkey }, "v", function() awful.spawn("~/.scripts/screen_record.sh start DP-0") end),
    awful.key({ modkey, "Shift" }, "v", function() awful.spawn("~/.scripts/screen_record.sh stop") end),

    -- Wallpaper
    awful.key({ modkey, "Shift" }, "t", function() awful.spawn("~/.scripts/randwall_new.sh") end),
    awful.key({ modkey, "Shift" }, "n", function() awful.spawn("~/.scripts/randwall.sh ~/.pvt/NSFW/") end),

    -- Layout
    awful.key({ modkey, "Shift" }, "space", function () awful.client.floating.toggle() end),
    awful.key({ modkey }, "r", function() enter_resize_mode() end),
    awful.key({ modkey, "Shift" }, "g", function() enter_gaps_mode() end),

    -- Reload
    awful.key({ modkey, "Shift" }, "c", awesome.restart),
    awful.key({ modkey, "Shift" }, "e", function() enter_exit_mode() end),

    -- Lock
    awful.key({ modkey, "Shift" }, "x", function() awful.spawn("lock") end),

    -- Help
    awful.key({ modkey, "Control" }, "h", hotkeys_popup.show_help),

    -- Media keys
    awful.key({}, "XF86AudioRaiseVolume", function() awful.spawn("pactl set-sink-volume 0 +5%") end),
    awful.key({}, "XF86AudioLowerVolume", function() awful.spawn("pactl set-sink-volume 0 -5%") end),
    awful.key({}, "XF86AudioMute", function() awful.spawn("pactl set-sink-mute 0 toggle") end),
    awful.key({}, "XF86MonBrightnessUp", function() awful.spawn("xbacklight -inc 20") end),
    awful.key({}, "XF86MonBrightnessDown", function() awful.spawn("xbacklight -dec 20") end),
    awful.key({}, "XF86AudioPlay", function() awful.spawn("playerctl play-pause") end),
    awful.key({}, "XF86AudioPause", function() awful.spawn("playerctl pause") end),
    awful.key({}, "XF86AudioNext", function() awful.spawn("playerctl next") end),
    awful.key({}, "XF86AudioPrev", function() awful.spawn("playerctl previous") end)
)

root.keys(globalkeys)
-- }}}

-- {{{ Client keys
local clientkeys = gears.table.join(
    awful.key({ modkey }, "q", function(c) c:kill() end)
)
-- }}}

-- {{{ Tag switching (Mod+1-0)
local taglist_buttons = gears.table.join(
    awful.button({ }, 1, function(t) t:view_only() end),
    awful.button({ modkey }, 1, function(t)
        if client.focus then
            client.focus:move_to_tag(t)
        end
    end)
)
-- }}}

-- {{{ Scratchpad implementation
local scratchpad_clients = {}

function move_to_scratchpad()
    local c = client.focus
    if not c then return end
    c.hidden = true
    c.sticky = true
    c.floating = true
    c:tags({})
    table.insert(scratchpad_clients, c)
end

function toggle_scratchpad()
    if #scratchpad_clients == 0 then
        naughty.notify({text = "No clients in scratchpad", timeout = 2})
        return
    end

    for _, c in ipairs(scratchpad_clients) do
        if c.hidden then
            c.hidden = false
            c:tags({awful.screen.focused().selected_tag})
            c:raise()
            return
        end
    end

    for i = #scratchpad_clients, 1, -1 do
        if not scratchpad_clients[i].hidden then
            scratchpad_clients[i].hidden = true
            return
        end
    end
end
-- }}}

-- {{{ Modes
function enter_resize_mode()
    local grabber = awful.keygrabber.run(function(_, key, event)
        if event == "release" then return end
        local c = client.focus
        if not c then return end

        if key == "h" or key == "Left" then c:relative_move(-10, 0, 0, 0)
        elseif key == "j" or key == "Down" then c:relative_move(0, 10, 0, 0)
        elseif key == "k" or key == "Up" then c:relative_move(0, -10, 0, 0)
        elseif key == "l" or key == "Right" then c:relative_move(10, 0, 0, 0)
        elseif key == "Escape" or key == "Return" then awful.keygrabber.stop(grabber) end
    end)
end

function enter_gaps_mode()
    local grabber = awful.keygrabber.run(function(_, key, event)
        if event == "release" then return end
        if key == "Escape" then awful.keygrabber.stop(grabber) end
    end)
end

function enter_exit_mode()
    local grabber = awful.keygrabber.run(function(_, key, event)
        if event == "release" then return end
        if key == "l" then awesome.quit()
        elseif key == "r" then awful.spawn("systemctl reboot")
        elseif key == "p" then awful.spawn("systemctl poweroff")
        elseif key == "Escape" or key == "Return" then awful.keygrabber.stop(grabber) end
    end)
end
-- }}}

-- {{{ Per-side borders for Alacritty
-- Update titlebar color on focus change
client.connect_signal("focus", function(c)
    if c.class and c.class:match("Alacritty") and c.titlebars_left then
        c.titlebars_left:set_bg("#f44336")
    end
end)

client.connect_signal("unfocus", function(c)
    if c.class and c.class:match("Alacritty") and c.titlebars_left then
        c.titlebars_left:set_bg("#00000000")
    end
end)
-- }}}

-- {{{ Wibar (status bar)
awful.screen.connect_for_each_screen(function(s)
    debug_log("Creating wibar for screen: " .. tostring(s))

    local mywibox = awful.wibar({
        position = "bottom",
        screen = s,
        height = 24,
        bg = "#1e293b"
    })

    -- Clock
    local mytextclock = wibox.widget.textclock("%H:%M")

    mywibox:setup {
        layout = wibox.layout.align.horizontal,
        { -- Left
            layout = wibox.layout.fixed.horizontal,
            mylauncher,
            awful.widget.taglist(s, awful.widget.taglist.filter.all, taglist_buttons)
        },
        { -- Middle
            layout = wibox.layout.flex.horizontal,
            awful.widget.tasklist(s, awful.widget.tasklist.filter.currenttags)
        },
        { -- Right
            layout = wibox.layout.fixed.horizontal,
            mytextclock
        }
    }

    debug_log("Wibar created successfully")
end)
-- }}}

-- {{{ Window rules
awful.rules.rules = {
    -- All clients
    { rule = { },
      properties = {
          border_width = beautiful.border_width,
          border_color = beautiful.border_normal,
          focus = awful.client.focus.filter,
          raise = true,
          keys = clientkeys,
          screen = awful.screen.preferred,
          placement = awful.placement.no_overlap + awful.placement.no_offscreen
      },
      callback = function(c)
          debug_log("Rules applied to: " .. (c.class or c.name or "unknown"))
      end
    },

    -- Floating windows
    { rule_any = {
        class = { "Arandr", "Blueman", "Gpick", "Kruler", "Sxiv" }
      },
      properties = { floating = true } },

    -- Terminal (no tag assignment - lets it open on default tag for debugging)
    -- { rule = { class = "Alacritty" }, properties = { tag = "3" } },

    -- Browsers
    { rule = { class = "Brave-browser" }, properties = { tag = "1" } },
    { rule = { class = "Firefox" }, properties = { tag = "2" } },
    { rule = { class = "zen" }, properties = { tag = "2" } },

    -- Gaming
    { rule = { class = "steam" }, properties = { tag = "5", floating = true } },
    { rule = { class = "Lutris" }, properties = { tag = "5", floating = true } },
    { rule = { class = "winboat" }, properties = { tag = "7", floating = true } },

    -- Other
    { rule = { class = "Discord" }, properties = { tag = "8" } },
    { rule = { class = "Spotify" }, properties = { tag = "9" } },
    { rule = { class = "mpv" }, properties = { tag = "10", floating = true } },
}
-- }}}

-- {{{ Tags
-- Create tags on each screen (runs immediately for existing screens)
awful.screen.connect_for_each_screen(function(s)
    debug_log("Setting up tags for screen: " .. tostring(s))

    local tag_names = {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10"}
    local tag_layouts = {layouts[1], layouts[1], layouts[1], layouts[1],
                       layouts[1], layouts[1], layouts[1], layouts[1],
                       layouts[1], layouts[1]}
    awful.tag(tag_names, s, tag_layouts)

    debug_log("Created " .. #s.tags .. " tags on screen")

    -- List all tags
    for i, tag in ipairs(s.tags) do
        debug_log("  Tag " .. i .. ": " .. tag.name)
    end
end)
-- }}}

-- {{{ Signals
client.connect_signal("manage", function(c)
    debug_log("Managing window: " .. (c.name or c.class or "unknown"))

    -- Log screen and tags info
    local s = c.screen
    if s then
        debug_log("  Screen: " .. tostring(s) .. ", tags count: " .. #s.tags)
        if #s.tags > 0 then
            local tag_names = {}
            for _, t in ipairs(s.tags) do table.insert(tag_names, t.name) end
            debug_log("  Available tags: " .. table.concat(tag_names, ", "))
        end
    else
        debug_log("  Screen: NONE!")
    end

    -- Log first tag (where window will be if not assigned)
    if c.first_tag then
        debug_log("  Assigned to tag: " .. c.first_tag.name)
    else
        debug_log("  No tag assigned (first_tag is nil)")
    end

    -- Set proper placement for windows during startup
    if awesome.startup and
      not c.size_hints.user_position
      and not c.size_hints.program_position then
        awful.placement.no_offscreen(c)
    end

    -- Add titlebar to left side for Alacritty windows
    if c.class and c.class:match("Alacritty") then
        awful.titlebar(c, {
            size = 3,
            position = "left",
            bg = "#00000000",
            fg = "#f3f4f5"
        })
    end
end)

client.connect_signal("mouse::enter", function(c)
    c:emit_signal("request::activate", "mouse_enter", {raise = false})
end)

client.connect_signal("property::urgent", function(c)
    if c.urgent then
        c.minimized = false
        c:emit_signal("request::activate")
    end
end)
-- }}}

-- {{{ Autostart
local autostart = {
    "systemctl --user restart pipewire",
    "~/.screenlayout/default.sh",
    "fcitx5 -d",
    "dunst -config ~/.config/dunst/dunstrc",
    "xrandr --output DP-0 --primary --output HDMI-0 --auto --rotate left --left-of DP-0",
    "picom --config ~/.config/picom.conf",
    "sh ~/.fehbg"
}

for _, app in ipairs(autostart) do
    awful.spawn.with_shell(app)
end
-- }}}
