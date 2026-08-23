-- Amp colorscheme for Neovim
-- Palette mirrors ~/.tmux/plugins/tmux-amp-theme/amp-theme.tmux (dark variant)

vim.cmd("highlight clear")
if vim.fn.exists("syntax_on") then
  vim.cmd("syntax reset")
end
vim.o.background = "dark"
vim.g.colors_name = "amp"

local c = {
  bg        = "#0F0F0F",
  surface   = "#161616",
  elevated  = "#1A1A1A",
  element   = "#1E1E1E",
  border    = "#262626",

  fg        = "#F2ECDD",
  muted     = "#B8AFA0",
  dim       = "#7A7367",

  accent    = "#E7894C",
  accent2   = "#E3A25A",
  red       = "#D9634F",
  blue      = "#6A9FCC",
  cyan      = "#8FC4C4",
  green     = "#7C9B96",

  none      = "NONE",
}

local hl = function(group, spec) vim.api.nvim_set_hl(0, group, spec) end

-- Editor UI
hl("Normal",            { fg = c.fg, bg = c.bg })
hl("NormalNC",          { fg = c.fg, bg = c.bg })
hl("NormalFloat",       { fg = c.fg, bg = c.surface })
hl("FloatBorder",       { fg = c.border, bg = c.surface })
hl("FloatTitle",        { fg = c.accent, bg = c.surface, bold = true })
hl("WinSeparator",      { fg = c.border, bg = c.none })
hl("VertSplit",         { fg = c.border, bg = c.none })

hl("LineNr",            { fg = c.dim, bg = c.none })
hl("CursorLine",        { bg = "#1F1A12" })
hl("CursorLineNr",      { fg = c.accent, bg = "#1F1A12", bold = true })
hl("CursorColumn",      { bg = "#1F1A12" })
hl("ColorColumn",       { bg = c.surface })
hl("SignColumn",        { fg = c.muted, bg = c.none })
hl("FoldColumn",        { fg = c.dim, bg = c.none })
hl("Folded",            { fg = c.muted, bg = c.surface, italic = true })

hl("Visual",            { bg = "#3A2614" })
hl("VisualNOS",         { bg = "#3A2614" })
hl("Search",            { fg = c.bg, bg = c.accent2, bold = true })
hl("IncSearch",         { fg = c.bg, bg = c.accent, bold = true })
hl("CurSearch",         { fg = c.bg, bg = c.accent, bold = true })
hl("MatchParen",        { fg = c.accent, bold = true, underline = true })

hl("StatusLine",        { fg = c.fg, bg = c.surface })
hl("StatusLineNC",      { fg = c.muted, bg = c.surface })
hl("TabLine",           { fg = c.muted, bg = c.surface })
hl("TabLineFill",       { bg = c.bg })
hl("TabLineSel",        { fg = c.bg, bg = c.accent, bold = true })

hl("WinBar",            { fg = c.muted, bg = c.none })
hl("WinBarNC",          { fg = c.dim, bg = c.none })

hl("Pmenu",             { fg = c.fg, bg = c.surface })
hl("PmenuSel",          { fg = c.bg, bg = c.accent, bold = true })
hl("PmenuSbar",         { bg = c.elevated })
hl("PmenuThumb",        { bg = c.muted })
hl("WildMenu",          { fg = c.bg, bg = c.accent, bold = true })

hl("Cursor",            { fg = c.bg, bg = c.fg })
hl("lCursor",           { fg = c.bg, bg = c.fg })
hl("TermCursor",        { fg = c.bg, bg = c.accent })

hl("ModeMsg",           { fg = c.accent, bold = true })
hl("MoreMsg",           { fg = c.green })
hl("Question",          { fg = c.blue })
hl("WarningMsg",        { fg = c.accent2 })
hl("ErrorMsg",          { fg = c.red, bold = true })
hl("MsgArea",           { fg = c.fg })
hl("MsgSeparator",      { fg = c.border, bg = c.surface })

hl("NonText",           { fg = c.dim })
hl("Whitespace",        { fg = c.dim })
hl("EndOfBuffer",       { fg = c.bg })
hl("SpecialKey",        { fg = c.dim })
hl("Title",             { fg = c.accent, bold = true })
hl("Directory",         { fg = c.accent, bold = true })

hl("SpellBad",          { sp = c.red, undercurl = true })
hl("SpellCap",          { sp = c.accent2, undercurl = true })
hl("SpellLocal",        { sp = c.cyan, undercurl = true })
hl("SpellRare",         { sp = c.blue, undercurl = true })

hl("QuickFixLine",      { bg = c.elevated, bold = true })
hl("Conceal",           { fg = c.muted })

-- Syntax
hl("Comment",           { fg = c.dim, italic = true })
hl("Constant",          { fg = c.cyan })
hl("String",            { fg = c.green })
hl("Character",         { fg = c.green })
hl("Number",            { fg = c.accent2 })
hl("Boolean",           { fg = c.accent2, bold = true })
hl("Float",             { fg = c.accent2 })

hl("Identifier",        { fg = c.fg })
hl("Function",          { fg = c.accent, bold = true })

hl("Statement",         { fg = c.accent2 })
hl("Conditional",       { fg = c.accent2, italic = true })
hl("Repeat",            { fg = c.accent2, italic = true })
hl("Label",             { fg = c.accent2 })
hl("Operator",          { fg = c.muted })
hl("Keyword",           { fg = c.red, italic = true })
hl("Exception",         { fg = c.red, italic = true })

hl("PreProc",           { fg = c.accent2 })
hl("Include",           { fg = c.accent2, italic = true })
hl("Define",            { fg = c.accent2 })
hl("Macro",             { fg = c.accent2 })
hl("PreCondit",         { fg = c.accent2 })

hl("Type",              { fg = c.blue })
hl("StorageClass",      { fg = c.red, italic = true })
hl("Structure",         { fg = c.blue })
hl("Typedef",           { fg = c.blue })

hl("Special",           { fg = c.accent })
hl("SpecialChar",       { fg = c.accent })
hl("Tag",               { fg = c.accent })
hl("Delimiter",         { fg = c.muted })
hl("SpecialComment",    { fg = c.muted, italic = true })
hl("Debug",             { fg = c.red })

hl("Underlined",        { fg = c.blue, underline = true })
hl("Bold",              { bold = true })
hl("Italic",            { italic = true })
hl("Todo",              { fg = c.bg, bg = c.accent2, bold = true })
hl("Error",             { fg = c.red, bold = true })

-- Treesitter
hl("@variable",                { fg = c.fg })
hl("@variable.builtin",        { fg = c.red, italic = true })
hl("@variable.parameter",      { fg = c.accent2 })
hl("@variable.member",         { fg = c.cyan })

hl("@constant",                { fg = c.cyan })
hl("@constant.builtin",        { fg = c.accent2, italic = true })
hl("@constant.macro",          { fg = c.accent2 })

hl("@module",                  { fg = c.blue })
hl("@label",                   { fg = c.accent2 })

hl("@string",                  { fg = c.green })
hl("@string.escape",           { fg = c.accent, italic = true })
hl("@string.special",          { fg = c.accent })
hl("@character",               { fg = c.green })
hl("@number",                  { fg = c.accent2 })
hl("@boolean",                 { fg = c.accent2, bold = true })
hl("@float",                   { fg = c.accent2 })

hl("@function",                { fg = c.accent, bold = true })
hl("@function.builtin",        { fg = c.accent, italic = true })
hl("@function.call",           { fg = c.accent })
hl("@function.macro",          { fg = c.accent, italic = true })
hl("@function.method",         { fg = c.accent, bold = true })
hl("@function.method.call",    { fg = c.accent })

hl("@constructor",             { fg = c.blue, bold = true })
hl("@operator",                { fg = c.muted })

hl("@keyword",                 { fg = c.red, italic = true })
hl("@keyword.conditional",     { fg = c.accent2, italic = true })
hl("@keyword.repeat",          { fg = c.accent2, italic = true })
hl("@keyword.return",          { fg = c.red, italic = true, bold = true })
hl("@keyword.function",        { fg = c.red, italic = true })
hl("@keyword.operator",        { fg = c.accent2, italic = true })
hl("@keyword.import",          { fg = c.accent2, italic = true })
hl("@keyword.exception",       { fg = c.red, italic = true })

hl("@type",                    { fg = c.blue })
hl("@type.builtin",            { fg = c.blue, italic = true })
hl("@type.definition",         { fg = c.blue, bold = true })

hl("@attribute",               { fg = c.accent2 })
hl("@property",                { fg = c.cyan })
hl("@field",                   { fg = c.cyan })

hl("@punctuation.bracket",     { fg = c.muted })
hl("@punctuation.delimiter",   { fg = c.muted })
hl("@punctuation.special",     { fg = c.accent })

hl("@comment",                 { fg = c.dim, italic = true })
hl("@comment.todo",            { fg = c.bg, bg = c.accent2, bold = true })
hl("@comment.note",            { fg = c.bg, bg = c.blue, bold = true })
hl("@comment.warning",         { fg = c.bg, bg = c.accent2, bold = true })
hl("@comment.error",           { fg = c.bg, bg = c.red, bold = true })

hl("@tag",                     { fg = c.red })
hl("@tag.attribute",           { fg = c.accent2 })
hl("@tag.delimiter",           { fg = c.muted })

hl("@markup.heading",          { fg = c.accent, bold = true })
hl("@markup.heading.1",        { fg = c.accent, bold = true })
hl("@markup.heading.2",        { fg = c.accent2, bold = true })
hl("@markup.heading.3",        { fg = c.blue, bold = true })
hl("@markup.heading.4",        { fg = c.cyan, bold = true })
hl("@markup.heading.5",        { fg = c.green, bold = true })
hl("@markup.heading.6",        { fg = c.muted, bold = true })
hl("@markup.list",             { fg = c.accent })
hl("@markup.list.checked",     { fg = c.green })
hl("@markup.list.unchecked",   { fg = c.muted })
hl("@markup.italic",           { italic = true })
hl("@markup.strong",           { bold = true })
hl("@markup.underline",        { underline = true })
hl("@markup.strikethrough",    { strikethrough = true })
hl("@markup.quote",            { fg = c.muted, italic = true })
hl("@markup.link",             { fg = c.blue, underline = true })
hl("@markup.link.label",       { fg = c.accent })
hl("@markup.link.url",         { fg = c.blue, underline = true, italic = true })
hl("@markup.raw",              { fg = c.green })
hl("@markup.raw.block",        { fg = c.green, bg = c.surface })

hl("@diff.plus",               { fg = c.green })
hl("@diff.minus",              { fg = c.red })
hl("@diff.delta",              { fg = c.accent2 })

-- LSP / Diagnostics
hl("DiagnosticError",          { fg = c.red })
hl("DiagnosticWarn",           { fg = c.accent2 })
hl("DiagnosticInfo",           { fg = c.blue })
hl("DiagnosticHint",           { fg = c.cyan })
hl("DiagnosticOk",             { fg = c.green })

hl("DiagnosticVirtualTextError", { fg = c.red, bg = c.none, italic = true })
hl("DiagnosticVirtualTextWarn",  { fg = c.accent2, bg = c.none, italic = true })
hl("DiagnosticVirtualTextInfo",  { fg = c.blue, bg = c.none, italic = true })
hl("DiagnosticVirtualTextHint",  { fg = c.cyan, bg = c.none, italic = true })
hl("DiagnosticVirtualTextOk",    { fg = c.green, bg = c.none, italic = true })

hl("DiagnosticUnderlineError", { sp = c.red, undercurl = true })
hl("DiagnosticUnderlineWarn",  { sp = c.accent2, undercurl = true })
hl("DiagnosticUnderlineInfo",  { sp = c.blue, undercurl = true })
hl("DiagnosticUnderlineHint",  { sp = c.cyan, undercurl = true })
hl("DiagnosticUnderlineOk",    { sp = c.green, undercurl = true })

hl("LspReferenceText",         { bg = c.elevated })
hl("LspReferenceRead",         { bg = c.elevated })
hl("LspReferenceWrite",        { bg = c.elevated, bold = true })
hl("LspInlayHint",             { fg = c.dim, bg = c.none, italic = true })
hl("LspCodeLens",              { fg = c.dim, italic = true })
hl("LspSignatureActiveParameter", { fg = c.accent, bold = true })

-- Git signs / gitsigns
hl("DiffAdd",                  { fg = c.green, bg = c.none })
hl("DiffChange",               { fg = c.accent2, bg = c.none })
hl("DiffDelete",               { fg = c.red, bg = c.none })
hl("DiffText",                 { fg = c.accent, bg = c.none, bold = true })

hl("GitSignsAdd",              { fg = c.green })
hl("GitSignsChange",           { fg = c.accent2 })
hl("GitSignsDelete",           { fg = c.red })
hl("GitSignsAddInline",        { fg = c.bg, bg = c.green })
hl("GitSignsChangeInline",     { fg = c.bg, bg = c.accent2 })
hl("GitSignsDeleteInline",     { fg = c.bg, bg = c.red })

-- Telescope / Snacks Picker
hl("TelescopeNormal",          { fg = c.fg, bg = c.surface })
hl("TelescopeBorder",          { fg = c.border, bg = c.surface })
hl("TelescopeTitle",           { fg = c.accent, bg = c.surface, bold = true })
hl("TelescopePromptNormal",    { fg = c.fg, bg = c.elevated })
hl("TelescopePromptBorder",    { fg = c.elevated, bg = c.elevated })
hl("TelescopePromptTitle",     { fg = c.bg, bg = c.accent, bold = true })
hl("TelescopePromptPrefix",    { fg = c.accent, bg = c.elevated })
hl("TelescopeResultsNormal",   { fg = c.fg, bg = c.surface })
hl("TelescopeResultsBorder",   { fg = c.surface, bg = c.surface })
hl("TelescopeResultsTitle",    { fg = c.surface, bg = c.surface })
hl("TelescopePreviewNormal",   { fg = c.fg, bg = c.bg })
hl("TelescopePreviewBorder",   { fg = c.border, bg = c.bg })
hl("TelescopePreviewTitle",    { fg = c.bg, bg = c.green, bold = true })
hl("TelescopeSelection",       { fg = c.accent, bg = "#3A2614", bold = true })
hl("TelescopeMatching",        { fg = c.accent2, bold = true })

hl("SnacksPicker",             { link = "TelescopeNormal" })
hl("SnacksPickerBorder",       { link = "TelescopeBorder" })
hl("SnacksPickerTitle",        { link = "TelescopeTitle" })
hl("SnacksPickerMatch",        { fg = c.accent2, bold = true })
hl("SnacksPickerSelected",     { fg = c.accent, bold = true })
hl("SnacksPickerDir",          { fg = c.muted })

-- Neo-tree / mini.files / nvim-tree
hl("NeoTreeNormal",            { fg = c.fg, bg = c.surface })
hl("NeoTreeNormalNC",          { fg = c.fg, bg = c.surface })
hl("NeoTreeRootName",          { fg = c.accent, bold = true })
hl("NeoTreeDirectoryName",     { fg = c.fg })
hl("NeoTreeDirectoryIcon",     { fg = c.accent })
hl("NeoTreeFileName",          { fg = c.fg })
hl("NeoTreeFileIcon",          { fg = c.muted })
hl("NeoTreeIndentMarker",      { fg = c.border })
hl("NeoTreeGitAdded",          { fg = c.green })
hl("NeoTreeGitModified",       { fg = c.accent2 })
hl("NeoTreeGitDeleted",        { fg = c.red })
hl("NeoTreeGitUntracked",      { fg = c.accent2, italic = true })
hl("NeoTreeGitIgnored",        { fg = c.dim })

hl("MiniFilesTitle",           { fg = c.accent, bold = true })
hl("MiniFilesTitleFocused",    { fg = c.bg, bg = c.accent, bold = true })
hl("MiniFilesBorder",          { fg = c.border })
hl("MiniFilesNormal",          { fg = c.fg, bg = c.surface })

-- Indent / Mini
hl("IndentBlanklineChar",      { fg = c.border })
hl("IblIndent",                { fg = c.border })
hl("IblScope",                 { fg = c.accent, bold = true })
hl("MiniIndentscopeSymbol",    { fg = c.accent })

-- Blink / cmp
hl("BlinkCmpMenu",             { fg = c.fg, bg = c.surface })
hl("BlinkCmpMenuBorder",       { fg = c.border, bg = c.surface })
hl("BlinkCmpMenuSelection",    { fg = c.accent, bg = c.elevated, bold = true })
hl("BlinkCmpLabelMatch",       { fg = c.accent2, bold = true })
hl("BlinkCmpKind",             { fg = c.accent })

hl("CmpItemAbbr",              { fg = c.fg })
hl("CmpItemAbbrDeprecated",    { fg = c.dim, strikethrough = true })
hl("CmpItemAbbrMatch",         { fg = c.accent2, bold = true })
hl("CmpItemAbbrMatchFuzzy",    { fg = c.accent2, bold = true })
hl("CmpItemKind",              { fg = c.accent })
hl("CmpItemMenu",              { fg = c.muted })

-- Noice
hl("NoiceCmdlinePopupBorder",  { fg = c.accent })
hl("NoiceCmdlineIcon",         { fg = c.accent })
hl("NoiceLspProgressTitle",    { fg = c.accent })
hl("NoiceLspProgressClient",   { fg = c.cyan })
hl("NoiceLspProgressSpinner",  { fg = c.accent2 })

-- Notify / Snacks notifier
hl("NotifyERRORBorder",        { fg = c.red })
hl("NotifyERRORIcon",          { fg = c.red })
hl("NotifyERRORTitle",         { fg = c.red, bold = true })
hl("NotifyWARNBorder",         { fg = c.accent2 })
hl("NotifyWARNIcon",           { fg = c.accent2 })
hl("NotifyWARNTitle",          { fg = c.accent2, bold = true })
hl("NotifyINFOBorder",         { fg = c.blue })
hl("NotifyINFOIcon",           { fg = c.blue })
hl("NotifyINFOTitle",          { fg = c.blue, bold = true })
hl("NotifyDEBUGBorder",        { fg = c.dim })
hl("NotifyDEBUGIcon",          { fg = c.dim })
hl("NotifyDEBUGTitle",         { fg = c.dim })

-- Which-key
hl("WhichKey",                 { fg = c.accent })
hl("WhichKeyGroup",            { fg = c.blue })
hl("WhichKeyDesc",             { fg = c.fg })
hl("WhichKeySeparator",        { fg = c.dim })
hl("WhichKeyFloat",            { bg = c.surface })
hl("WhichKeyBorder",           { fg = c.border, bg = c.surface })

-- Lazy
hl("LazyButtonActive",         { fg = c.bg, bg = c.accent, bold = true })
hl("LazyButton",               { fg = c.fg, bg = c.elevated })
hl("LazyH1",                   { fg = c.bg, bg = c.accent, bold = true })
hl("LazyH2",                   { fg = c.accent, bold = true })
hl("LazySpecial",              { fg = c.accent2 })
hl("LazyProp",                 { fg = c.muted })

-- Lualine (basic — extras inherit from groups above)
hl("lualine_a_normal",         { fg = c.bg, bg = c.accent, bold = true })
hl("lualine_a_insert",         { fg = c.bg, bg = c.green, bold = true })
hl("lualine_a_visual",         { fg = c.bg, bg = c.blue, bold = true })
hl("lualine_a_replace",        { fg = c.bg, bg = c.red, bold = true })
hl("lualine_a_command",        { fg = c.bg, bg = c.accent2, bold = true })
hl("lualine_b_normal",         { fg = c.fg, bg = c.elevated })
hl("lualine_c_normal",         { fg = c.muted, bg = c.surface })

-- Bufferline
hl("BufferLineFill",           { bg = c.bg })
hl("BufferLineBackground",     { fg = c.muted, bg = c.surface })
hl("BufferLineBufferSelected", { fg = c.accent, bg = c.bg, bold = true, italic = false })
hl("BufferLineBufferVisible",  { fg = c.fg, bg = c.surface })
hl("BufferLineSeparator",      { fg = c.bg, bg = c.surface })

-- Treesitter context
hl("TreesitterContext",                 { bg = c.surface })
hl("TreesitterContextLineNumber",       { fg = c.accent, bg = c.surface, bold = true })
hl("TreesitterContextBottom",           { sp = c.border, underline = true })

-- Render-markdown / markview
hl("RenderMarkdownH1Bg",       { fg = c.bg, bg = c.accent })
hl("RenderMarkdownH2Bg",       { fg = c.bg, bg = c.accent2 })
hl("RenderMarkdownH3Bg",       { fg = c.bg, bg = c.blue })
hl("RenderMarkdownH4Bg",       { fg = c.bg, bg = c.cyan })
hl("RenderMarkdownH5Bg",       { fg = c.bg, bg = c.green })
hl("RenderMarkdownH6Bg",       { fg = c.bg, bg = c.muted })
hl("RenderMarkdownCode",       { bg = c.surface })

-- Mini.diff
hl("MiniDiffSignAdd",          { fg = c.green })
hl("MiniDiffSignChange",       { fg = c.accent2 })
hl("MiniDiffSignDelete",       { fg = c.red })
hl("MiniDiffOverAdd",          { fg = c.green, bg = c.surface })
hl("MiniDiffOverChange",       { fg = c.accent2, bg = c.surface })
hl("MiniDiffOverDelete",       { fg = c.red, bg = c.surface })

-- Terminal ANSI palette
vim.g.terminal_color_0  = c.bg
vim.g.terminal_color_1  = c.red
vim.g.terminal_color_2  = c.green
vim.g.terminal_color_3  = c.accent2
vim.g.terminal_color_4  = c.blue
vim.g.terminal_color_5  = c.accent
vim.g.terminal_color_6  = c.cyan
vim.g.terminal_color_7  = c.fg
vim.g.terminal_color_8  = c.dim
vim.g.terminal_color_9  = c.red
vim.g.terminal_color_10 = c.green
vim.g.terminal_color_11 = c.accent2
vim.g.terminal_color_12 = c.blue
vim.g.terminal_color_13 = c.accent
vim.g.terminal_color_14 = c.cyan
vim.g.terminal_color_15 = c.fg
