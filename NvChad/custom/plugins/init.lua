local plugins = {
  --Syntax
  ['kylechui/nvim-surround'] = {
    tag = "*",
    config = function()
      require('nvim-surround').setup({})
    end,
  },

  -- Session management
  ['rmagatti/auto-session'] = {
    config = function()
      require('auto-session').setup({
        log_level = 'error',
        auto_session_suppress_dirs = { '~/', '~/Downloads', '/' },
      })
    end
  },

  -- Keymapping
  ['folke/which-key.nvim'] = {
    disable = false,
    config = function()
      vim.o.timeout = true
      vim.o.timeoutlen = 100
      require('which-key').setup({
        -- your configuration comes here
        -- or leave it empty to use default settings
      })
    end
  },

  -- Debugging
  ['mfussenegger/nvim-dap'] = {
    disable = vim.fn.has 'win32' == 1,
    module = 'dap',
  },
  ['rcarriga/nvim-dap-ui'] = {
    disable = vim.fn.has 'win32' == 1,
    requires = { 'mfussenegger/nvim-dap' },
    after = 'nvim-dap',
  },
  ['theHamsta/nvim-dap-virtual-text'] = {},
  ['nvim-telescope/telescope-dap.nvim'] = {},
  ['jayp0521/mason-nvim-dap.nvim'] = {
    disable = vim.fn.has 'win32' == 1,
    after = 'nvim-dap',
  }
}

return plugins
