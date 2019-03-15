#!/bin/bash

# Copy configs
echo Copying Configs
cp -R .vimrc .vimrc.bundles .zshrc .tmux.conf .bash_aliases .config/ .scripts .local ~/
echo Done

# Install Powerlevel9k
echo Installing Powerlevel9k
if [ ! -d "~/Documents/GitHub" ]; then
  mkdir -p ~/Documents/GitHub
fi
cd ~/Documents/GitHub
git clone https://github.com/bhilburn/powerlevel9k.git
rm -rf powerlevel9k
cd ~/
echo Done

# Install VIM Pathogen
mkdir -p ~/.vim/autoload ~/.vim/bundle && \
curl -LSso ~/.vim/autoload/pathogen.vim https://tpo.pe/pathogen.vim

# Install Antigen for ZSH
curl -L git.io/antigen > ~/.config/antigen.zsh

echo "Done"
