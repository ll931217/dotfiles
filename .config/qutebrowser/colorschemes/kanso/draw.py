def zen(c, options={}):
    # Kansō Zen Palette (Evolution of Kanagawa)
    palette = {
        "background": "#101010",  # Zen Dark
        "background-alt": "#1F1F28",  # Sumi Ink
        "background-attention": "#16161D",  # Sumi Ink 2
        "border": "#101010",  # Deep Black
        "current-line": "#2D4F67",  # Wave Blue (Selection)
        "selection": "#2D4F67",  # Wave Blue
        "foreground": "#DCD7BA",  # Fuji White
        "foreground-alt": "#727169",  # Fuji Gray
        "foreground-attention": "#DCD7BA",  # Fuji White
        "comment": "#727169",  # Fuji Gray
        "cyan": "#6A9589",  # Wave Aqua
        "green": "#76946A",  # Autumn Green
        "orange": "#7E9CD8",  # Crystal Blue (Accent)
        "pink": "#D27E99",  # Sakura Pink
        "purple": "#957FB8",  # Oni Violet
        "red": "#C34043",  # Autumn Red
        "yellow": "#C0A36E",  # Boat Yellow
    }

    spacing = options.get("spacing", {"vertical": 5, "horizontal": 5})

    padding = options.get(
        "padding",
        {
            "top": spacing["vertical"],
            "right": spacing["horizontal"],
            "bottom": spacing["vertical"],
            "left": spacing["horizontal"],
        },
    )

    ## Completion widget
    c.colors.completion.category.bg = palette["background"]
    c.colors.completion.category.border.bottom = palette["border"]
    c.colors.completion.category.border.top = palette["border"]
    c.colors.completion.category.fg = palette["foreground"]
    c.colors.completion.even.bg = palette["background"]
    c.colors.completion.odd.bg = palette["background-alt"]
    c.colors.completion.fg = palette["foreground"]
    c.colors.completion.item.selected.bg = palette["selection"]
    c.colors.completion.item.selected.border.bottom = palette["selection"]
    c.colors.completion.item.selected.border.top = palette["selection"]
    c.colors.completion.item.selected.fg = palette["foreground"]
    c.colors.completion.match.fg = palette["orange"]  # Crystal Blue match
    c.colors.completion.scrollbar.bg = palette["background"]
    c.colors.completion.scrollbar.fg = palette["foreground"]

    ## Downloads
    c.colors.downloads.bar.bg = palette["background"]
    c.colors.downloads.error.bg = palette["background"]
    c.colors.downloads.error.fg = palette["red"]
    c.colors.downloads.stop.bg = palette["background"]
    c.colors.downloads.system.bg = "none"

    ## Hints
    c.colors.hints.bg = palette["background-alt"]
    c.colors.hints.fg = palette["purple"]
    c.hints.border = "1px solid " + palette["background"]
    c.colors.hints.match.fg = palette["foreground-alt"]

    ## Keyhints
    c.colors.keyhint.bg = palette["background"]
    c.colors.keyhint.fg = palette["purple"]
    c.colors.keyhint.suffix.fg = palette["selection"]

    ## Messages
    c.colors.messages.error.bg = palette["background"]
    c.colors.messages.error.border = palette["background-alt"]
    c.colors.messages.error.fg = palette["red"]
    c.colors.messages.info.bg = palette["background"]
    c.colors.messages.info.border = palette["background-alt"]
    c.colors.messages.info.fg = palette["comment"]
    c.colors.messages.warning.bg = palette["background"]
    c.colors.messages.warning.border = palette["background-alt"]
    c.colors.messages.warning.fg = palette["red"]

    ## Prompts
    c.colors.prompts.bg = palette["background"]
    c.colors.prompts.border = "1px solid " + palette["background-alt"]
    c.colors.prompts.fg = palette["cyan"]
    c.colors.prompts.selected.bg = palette["selection"]

    ## Statusbar
    c.colors.statusbar.caret.bg = palette["background"]
    c.colors.statusbar.caret.fg = palette["orange"]
    c.colors.statusbar.caret.selection.bg = palette["background"]
    c.colors.statusbar.caret.selection.fg = palette["orange"]
    c.colors.statusbar.command.bg = palette["background"]
    c.colors.statusbar.command.fg = palette["pink"]
    c.colors.statusbar.command.private.bg = palette["background"]
    c.colors.statusbar.command.private.fg = palette["foreground-alt"]
    c.colors.statusbar.insert.bg = palette["background-attention"]
    c.colors.statusbar.insert.fg = palette["foreground-attention"]
    c.colors.statusbar.normal.bg = palette["background"]
    c.colors.statusbar.normal.fg = palette["foreground"]
    c.colors.statusbar.passthrough.bg = palette["background"]
    c.colors.statusbar.passthrough.fg = palette["orange"]
    c.colors.statusbar.private.bg = palette["background-alt"]
    c.colors.statusbar.private.fg = palette["foreground-alt"]
    c.colors.statusbar.progress.bg = palette["background"]
    c.colors.statusbar.url.error.fg = palette["red"]
    c.colors.statusbar.url.fg = palette["foreground"]
    c.colors.statusbar.url.hover.fg = palette["cyan"]
    c.colors.statusbar.url.success.http.fg = palette["green"]
    c.colors.statusbar.url.success.https.fg = palette["green"]
    c.colors.statusbar.url.warn.fg = palette["yellow"]
    c.statusbar.padding = padding

    ## Tabs
    c.colors.tabs.bar.bg = palette["background-alt"]
    c.colors.tabs.even.bg = palette["background-alt"]
    c.colors.tabs.even.fg = palette["foreground-alt"]
    c.colors.tabs.indicator.error = palette["red"]
    c.colors.tabs.indicator.start = palette["orange"]
    c.colors.tabs.indicator.stop = palette["green"]
    c.colors.tabs.indicator.system = "none"
    c.colors.tabs.odd.bg = palette["background-alt"]
    c.colors.tabs.odd.fg = palette["foreground-alt"]
    c.colors.tabs.selected.even.bg = palette["background"]
    c.colors.tabs.selected.even.fg = palette["foreground"]
    c.colors.tabs.selected.odd.bg = palette["background"]
    c.colors.tabs.selected.odd.fg = palette["foreground"]
    c.tabs.padding = padding
    c.tabs.indicator.width = 1
    c.tabs.favicons.scale = 1
