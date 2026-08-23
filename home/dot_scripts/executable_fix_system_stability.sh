#!/bin/bash

echo "🔧 System Stability Fix Script"
echo "================================"

# Update system
echo "📦 Updating system packages..."
sudo pacman -Syu --noconfirm

# Restart picom with stable config
echo "🎨 Restarting picom..."
pkill picom
sleep 2
picom --config ~/.config/picom.conf &

# Clean up core dumps
echo "🧹 Cleaning old core dumps..."
echo "ep0NgXpW" | sudo -S coredumpctl prune --vacuum-time=7d

# Check system status
echo "📊 System status:"
echo "Load average: $(uptime | awk -F'load average:' '{ print $2 }')"
echo "GPU temp: $(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits)°C"
echo "Memory usage: $(free -h | grep Mem | awk '{print $3"/"$2}')"

echo "✅ System stability fix complete!"
echo "💡 Tip: Run this weekly to maintain stability"
