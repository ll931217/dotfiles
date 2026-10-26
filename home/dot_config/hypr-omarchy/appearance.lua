-- Decode only the generated border-data format; never execute generated Lua.
local appearance = {}
local limit = 8192
local color = '"(#%x%x%x%x%x%x)"'
local pattern = "^%s*return%s*{%s*general%s*=%s*{%s*col%s*=%s*{%s*active_border%s*=%s*"
	.. color
	.. "%s*,%s*inactive_border%s*=%s*"
	.. color
	.. "%s*}%s*}%s*,%s*group%s*=%s*{%s*col%s*=%s*{%s*border_active%s*=%s*"
	.. color
	.. "%s*,%s*border_inactive%s*=%s*"
	.. color
	.. "%s*}%s*}%s*}%s*$"

---@param path string
---@return table? data
---@return string? reason
local function read_palette(path)
	local file = io.open(path, "rb")
	if not file then
		return nil, "missing-or-unreadable"
	end
	local ok, source = pcall(file.read, file, limit + 1)
	pcall(file.close, file)
	if not ok or type(source) ~= "string" then
		return nil, "read-failed"
	end
	if #source > limit then
		return nil, "oversized"
	end
	-- The generator emits line comments and four quoted #RRGGBB values only.
	source = source:gsub("%-%-[^\r\n]*", "")
	local active, inactive, group_active, group_inactive = source:match(pattern)
	if not active then
		return nil, "invalid-border-data"
	end
	return {
		general = { col = { active_border = active, inactive_border = inactive } },
		group = { col = { border_active = group_active, border_inactive = group_inactive } },
	}
end

---@param path string
---@return table
function appearance.load(path)
	local ok, data, reason = pcall(read_palette, path)
	if ok and data then
		return data
	end
	-- No raw file contents, parser errors or subprocesses in the diagnostic.
	pcall(function()
		io.stderr:write(
			"Omarchy-inspired appearance: ",
			ok and reason or "read-failed",
			"; default borders retained. Re-select a theme in the native picker to regenerate the palette.\n"
		)
	end)
	return {}
end

return appearance
