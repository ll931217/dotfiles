local M = {}

M.general = {
  -- 'n' for Normal Mode
  n = {
    [';'] = { ':', 'Enter command mode', opts = { nowait = true }},
    ['<leader>q'] = { ':qall <CR>', 'Exit Neovim' },
  }
}

return M
