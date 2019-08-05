#!/bin/bash

# Copy configs
echo Copying Configs
cp -R .vimrc .vimrc.bundles .zshrc .tmux.conf .bash_aliases .config/ .scripts .local ~/
echo "Done: Copying Configs"

# Install Powerlevel9k
echo "Installing Powerlevel9k"
if [ ! -d "~/Documents/GitHub" ]; then
  mkdir -p ~/Documents/GitHub
fi
cd ~/Documents/GitHub
git clone https://github.com/bhilburn/powerlevel9k.git
cd ~/
echo "Done: Installing PowerLevel9k"

# Install VIM Pathogen
echo "Installing VIM Pathogen"
mkdir -p ~/.vim/autoload ~/.vim/bundle && \
curl -LSso ~/.vim/autoload/pathogen.vim https://tpo.pe/pathogen.vim
echo "Done: Installing VIM Pathogen"

# Install Antigen for ZSH
echo "Installing Antigen for ZSH"
curl -L git.io/antigen > ~/.config/antigen.zsh
echo "Done: Installing Antigen for ZSH"

echo "Done with setting up environment"
