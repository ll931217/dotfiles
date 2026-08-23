return {
  {
    "LazyVim/LazyVim",
    opts = {
      -- colorscheme = "tokyonight-moon",
      -- colorscheme = "catppuccin",
      -- colorscheme = "eldritch",
      -- colorscheme = "dracula",
      -- colorscheme = "kanso",
      colorscheme = "amp",
    },
  },
  {
    "eldritch-theme/eldritch.nvim",
    lazy = false,
    priority = 1000,
    opts = {
      transparent = true,
    },
  },
  {
    "catppuccin/nvim",
    config = function()
      require("catppuccin").setup({
        flavour = "mocha",
        term_colors = true,
        transparent_background = true,
      })
    end,
    opts = {
      term_colors = true,
      transparent_background = true,
    },
  },
  {
    "Mofiqul/dracula.nvim",
    opts = {
      transparent_bg = true,
    },
  },
  {
    "tokyonight.nvim",
    opts = {
      transparent = true,
      styles = {
        sidebars = "transparent",
        floats = "transparent",
      },
    },
  },
  {
    "webhooked/kanso.nvim",
    lazy = false,
    priority = 1000,
    opts = {
      transparent = true,
    },
  },
}
