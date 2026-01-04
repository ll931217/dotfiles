#!/bin/bash
# Test AwesomeWM config for syntax errors

echo "Testing AwesomeWM config syntax..."
awesome -k -c ~/.config/awesome/rc.lua 2>&1

if [ $? -eq 0 ]; then
    echo "✓ Config syntax is valid"
    echo ""
    echo "To test AwesomeWM:"
    echo "  awesome"
    echo ""
    echo "To check logs if it fails:"
    echo "  journalctl -u awesome -xe"
    echo "  less ~/.local/share/awesome/awesome.0000.log"
else
    echo "✗ Config has errors"
    echo "Check the output above for details"
fi
