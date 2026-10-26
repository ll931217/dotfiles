local root = "/home/ll931217/.config/hypr-omarchy/"
local session = "/home/ll931217/.local/bin/omarchy-inspired-session"
local controller = "/usr/bin/python " .. root .. "desktop_actions.py "
local modes = { default = true, resize = true, gaps = true, ["gaps-inner"] = true, ["gaps-outer"] = true }
local bindings, seen = {}, {}
local function fail(message)
    error(root .. "keys.tsv: " .. message .. "; fix the registry and verify the config", 0)
end
local function shell_quote(value)
    return "'" .. tostring(value):gsub("'", "'\\''") .. "'"
end
local function notice(title, text)
    hl.exec_cmd("/usr/bin/notify-send " .. shell_quote(title) .. " " .. shell_quote(text))
end

-- API shapes audited against Hyprland efb50993780079460b0cbed1363e2166a2de1d9f.
local defaults = { inner = 6, outer = 2 }
local overrides = {}
hl.config({ general = { gaps_in = defaults.inner, gaps_out = defaults.outer } })
local function gap_value(value, operation)
    if operation == "zero" then return 0 end
    return math.max(0, value + (operation == "plus" and 5 or -5))
end
local function apply_gaps(workspace, values)
    hl.workspace_rule({ workspace = workspace, gaps_in = values.inner, gaps_out = values.outer })
end
local function change_gaps(kind, scope, operation)
    local active = hl.get_active_workspace()
    if not active then
        notice("Gap change unavailable", "Focus a workspace, then retry the gap key.")
        return
    end
    local current = active.config_name
    if scope == "current" then
        local values = overrides[current] or { inner = defaults.inner, outer = defaults.outer }
        values[kind] = gap_value(values[kind], operation)
        overrides[current] = values
        apply_gaps(current, values)
        notice("Workspace gaps changed", current .. ": " .. kind .. " = " .. values[kind])
        return
    end
    for _, workspace in ipairs(hl.get_workspaces()) do
        local name = workspace.config_name
        overrides[name] = overrides[name] or { inner = defaults.inner, outer = defaults.outer }
    end
    defaults[kind] = gap_value(defaults[kind], operation)
    hl.config({ general = { gaps_in = defaults.inner, gaps_out = defaults.outer } })
    for name, values in pairs(overrides) do
        values[kind] = gap_value(values[kind], operation)
        apply_gaps(name, values)
    end
    notice("All workspace gaps changed", kind .. ": " .. operation .. " (including future workspaces)")
end
local function focus_layer()
    local active = hl.get_active_window()
    if not active then
        notice("Focus unchanged", "Focus a window before switching between floating and tiled windows.")
        return
    end
    local candidates = hl.get_windows({ workspace = active.workspace, floating = not active.floating })
    table.sort(candidates, function(a, b) return a.focus_history_id < b.focus_history_id end)
    for _, window in ipairs(candidates) do
        if not window.hidden and window.accepts_input then
            hl.dispatch(hl.dsp.focus({ window = window }))
            return
        end
    end
    notice("Focus unchanged", "No visible opposite-layer window on this workspace; toggle floating with Super+Shift+Space.")
end
local function mode_action(mode)
    return function()
        hl.dispatch(hl.dsp.submap(mode == "default" and "reset" or mode))
        local instruction = {
            default = "Normal keys restored.",
            resize = "H/J shrink width/height; K/L grow height/width. Enter or Escape exits.",
            gaps = "O: outer; I: inner. US = current, + (Shift+=) all. Enter or Escape exits.",
            ["gaps-inner"] = "Inner gaps: US = current, + (Shift+=) all; minus/0 current, Shift variants all. Enter or Escape exits.",
            ["gaps-outer"] = "Outer gaps: US = current, + (Shift+=) all; minus/0 current, Shift variants all. Enter or Escape exits.",
        }
        notice("Keyboard mode: " .. mode, instruction[mode])
    end
end
local function toggle_fullscreen()
    local window = hl.get_active_window()
    if not window then return end
    local title = window.title
    local wine_game = window.xwayland and (
        title == "World of Warcraft" or title == "Path of Exile" or title == "Path of Exile 2"
    )
    if wine_game then
        -- Borderless compositor fullscreen avoids Wine's display-mode bounce.
        hl.dispatch(hl.dsp.window.fullscreen_state({
            window = window, internal = 2, client = 0, action = "toggle",
        }))
    else
        hl.dispatch(hl.dsp.window.fullscreen({ action = "toggle" }))
    end
end
local function factory(action)
    local name = action:match("^session:(%l+)$")
    if name then
        if name ~= "terminal" and name ~= "lock" and name ~= "logout" then fail("unknown action " .. action) end
        return hl.dsp.exec_cmd(session .. " --" .. name)
    end
    if action:match("^desktop:[a-z][a-z0-9-]*$") or action:match("^ai:[a-z][a-z0-9-]*$") then
        return hl.dsp.exec_cmd(controller .. action)
    end
    if action == "native:close" then return hl.dsp.window.close() end
    if action == "native:fullscreen" then return toggle_fullscreen end
    if action == "native:float" then return hl.dsp.window.float({ action = "toggle" }) end
    if action == "native:focus-layer" then return focus_layer end
    if action == "native:reload" then return hl.dsp.exec_cmd("/usr/bin/hyprctl reload config-only") end
    local operation, direction = action:match("^native:(%l+):(%l+)$")
    if (operation == "focus" or operation == "move") and
        ({ left = true, right = true, up = true, down = true })[direction] then
        if operation == "focus" then return hl.dsp.focus({ direction = direction }) end
        return hl.dsp.window.move({ direction = direction })
    end
    local target = action:match("^native:workspace:(%d+)$")
    if target then return hl.dsp.focus({ workspace = tonumber(target) }) end
    target = action:match("^native:send:(%d+)$")
    if target then return hl.dsp.window.move({ workspace = tonumber(target), follow = false }) end
    local mode = action:match("^native:mode:([a-z-]+)$")
    if mode and modes[mode] then return mode_action(mode) end
    local x, y = action:match("^native:resize:(%-?%d+):(%-?%d+)$")
    if x then return hl.dsp.window.resize({ x = tonumber(x), y = tonumber(y), relative = true }) end
    local kind, scope, change = action:match("^native:gaps:(%l+):(%l+):(%l+)$")
    if (kind == "inner" or kind == "outer") and (scope == "current" or scope == "all") and
        (change == "plus" or change == "minus" or change == "zero") then
        return function() change_gaps(kind, scope, change) end
    end
    fail("unknown action " .. action)
end

for line in io.lines(root .. "keys.tsv") do
    if line ~= "mode\tchord\taction\tlabel\tcompatibility" then
        local mode, chord, action, label, compatibility = line:match("^([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)$")
        if not mode or not modes[mode] then fail("invalid row " .. line) end
        local modifiers, key, used = {}, nil, {}
        for token in chord:gmatch("[^+]+") do
            local modifier = ({ super = "SUPER", mod4 = "SUPER", ctrl = "CTRL", control = "CTRL", alt = "ALT", shift = "SHIFT" })[token:lower()]
            if modifier then
                if key or used[modifier] then fail("invalid modifier in " .. chord) end
                used[modifier] = true
                table.insert(modifiers, modifier)
            else
                if key or not token:match("^[%w_]+$") then fail("invalid chord " .. chord) end
                key = token
            end
        end
        if not key then fail("missing key in " .. chord) end
        table.sort(modifiers)
        local identity = mode .. ":" .. table.concat(modifiers, "+") .. ":" .. key:lower()
        if seen[identity] then fail("duplicate " .. mode .. " " .. chord) end
        seen[identity] = true
        bindings[mode] = bindings[mode] or {}
        table.insert(modifiers, key)
        table.insert(bindings[mode], { chord = table.concat(modifiers, " + "), action = factory(action), label = label, compatibility = compatibility })
    end
end
local function install(mode)
    for _, binding in ipairs(bindings[mode] or {}) do
        hl.bind(binding.chord, binding.action, { description = binding.label .. " — " .. binding.compatibility })
    end
end
install("default")
for _, mode in ipairs({ "resize", "gaps", "gaps-inner", "gaps-outer" }) do
    hl.define_submap(mode, function() install(mode) end)
end
return { count = (function() local n = 0; for _ in pairs(seen) do n = n + 1 end; return n end)() }
