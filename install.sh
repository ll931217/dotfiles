#!/bin/bash

echo "Copying Configs"
cp -R .zshrc .tmux.conf .bash_aliases .config/ .scripts .local ~/
echo "Done: Copying Configs"

echo "Downloading Terminal Fonts"
mkdir -p $HOME/.local/share/fonts/MesloLGS
wget -nc -P $HOME/.local/share/fonts/MesloLGS -i ./meslo-urls.txt
echo "Done: Downloading Terminal Fonts"

echo "Installing NVM"
mkdir $HOME/.nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.34.0/install.sh | bash
echo 'export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}"  ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
[ -s "$NVM_DIR/nvm.sh"  ] && \. "$NVM_DIR/nvm.sh" # This loads nvm' >> $HOME/.zshrc.local
echo "Done: Installing NVM"

echo "Installing NeoVim"
if [ -d ~/.config/nvim ]; then
    mv ~/.config/nvim ~/.config/nvim.bak
fi
git clone https://github.com/AstroNvim/AstroNvim ~/.config/nvim
nvim +PackerSync
echo "Done: Installing NeoVim"

# Install Antigen for ZSH
echo "Installing Antigen for ZSH"
curl -L git.io/antigen > ~/.config/antigen.zsh
echo "Done: Installing Antigen for ZSH"

echo "Done with setting up environment"
