#!/bin/bash

echo "Copying Configs"
cp -R .zshrc .tmux.conf .bash_aliases .config/ .scripts .local ~/
echo "Done: Copying Configs"

echo "Downloading Terminal Fonts"
mkdir -p "$HOME/.local/share/fonts/MesloLGS"
wget -nc -P "$HOME/.local/share/fonts/MesloLGS" -i ./font_urls/meslo-urls.txt
echo "Done: Downloading Terminal Fonts"

echo "Installing pnpm"
curl -fsSL https://get.pnpm.io/install.sh | sh -
pnpm env use --global lts
echo "Done: Installing pnpm"

echo "Installing NeoVim"
if [ -d ~/.config/nvim ]; then
  mv ~/.config/nvim ~/.config/nvim.bak
  mv ~/.local/share/nvim ~/.local/share/nvim.bak
  mv ~/.local/state/nvim ~/.local/state/nvim.bak
fi

if command -v "gh" &>/dev/null; then
  echo "Cloning lazyvim config using github-cli"
  gh repo clone ll931217/lazyvim_config ~/.config/nvim
else
  echo "Cloning lazyvim config using git"
  git clone https://github.com/ll931217/lazyvim_config.git ~/.config/nvim
fi
echo "Done: Installing NeoVim"

echo "Done with setting up environment"
