#!/usr/bin/env bash

echo "Copying Configs"
# cp -R .zshrc .tmux.conf .config/ .scripts .local ~/
ln -s "$(pwd)/.zshrc" "$HOME/.zshrc"
ln -s "$(pwd)/.zshrc.fzf" "$HOME/.zshrc.fzf"
ln -s "$(pwd)/.zshrc.local" "$HOME/.zshrc.local"
ln -s "$(pwd)/.tmux.conf" "$HOME/.tmux.conf"
ln -s "$(pwd)/.scripts" "$HOME/.scripts"

mkdir -p "$HOME/.local/share"
ln -s "$(pwd)/.local/share/fonts" "$HOME/.local/share/fonts"

SOURCE_DIR="$(pwd)/.config"
TARGET_DIR="$XDG_CONFIG_HOME"

# Build an array of *entries* in the source directory
mapfile -t entries < <(find "$SOURCE_DIR" -maxdepth 1 -mindepth 1)

for item in "${entries[@]}"; do
  base=$(basename "$item")
  target="$TARGET_DIR/$base"

  # If the target already exists, handle it
  if [[ -e "$target" || -L "$target" ]]; then
    echo "Skipping existing: $target"
    continue
  fi

  ln -s "$item" "$target"
  echo "Linked: $target → $item"
done
echo "Done: Copying Configs"

echo "Downloading Terminal Fonts"
# TODO: Add more fonts
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
