#!/usr/bin/env bash
# Test script for context monitor hook

echo "Testing Context Monitor Hook..."
echo ""

# Create a test JSON input
TEST_SESSION_ID="test-$(date +%s)"
TEST_JSON=$(cat <<EOF
{
  "session_id": "$TEST_SESSION_ID",
  "transcript_path": "$HOME/.claude/context-test.jsonl",
  "cwd": "$HOME/test-project",
  "hook_event_name": "Stop",
  "permission_mode": "default"
}
EOF
)

# Create a test transcript file with estimated 80% context size
# 200k * 0.8 = 160k tokens * 4 chars/token = 640k characters
TEST_TRANSCRIPT="$HOME/.claude/context-test.jsonl"
echo '{"type":"test","content":"'$(
  # Create content that's roughly 80% of 200k context
  head -c 640000 /dev/urandom | tr -dc 'a-zA-Z0-9 ' | fold -w 80
)'"}' > "$TEST_TRANSCRIPT"

# Also test with a file that simulates high context usage
HIGH_USAGE_TRANSCRIPT="$HOME/.claude/context-test-high.jsonl"
echo '{"type":"test","content":"'$(
  # Simulate 90% context
  head -c 720000 /dev/urandom | tr -dc 'a-zA-Z0-9 ' | fold -w 80
)'"}' > "$HIGH_USAGE_TRANSCRIPT"

echo "✅ Created test transcript files:"
echo "   - Standard test (~80%): $TEST_TRANSCRIPT"
echo "   - High usage test (~90%): $HIGH_USAGE_TRANSCRIPT"
echo ""

# Test with standard 80% context
echo "🧪 Test 1: Sending input simulating 80% context..."
echo "$TEST_JSON" | sed "s|transcript_path.*|transcript_path\": \"$TEST_TRANSCRIPT\",|" | bash ~/.claude/scripts/context-monitor.sh
echo ""

# Clean up cooldown file for second test
rm -f "$HOME/.claude/context-alert-state"

# Test with high context usage
echo "🧪 Test 2: Sending input simulating 90% context..."
echo "$TEST_JSON" | sed "s|transcript_path.*|transcript_path\": \"$HIGH_USAGE_TRANSCRIPT\",|" | bash ~/.claude/scripts/context-monitor.sh
echo ""

# Check logs
if [ -f "$HOME/.claude/hooks-logs/context-monitor.log" ]; then
    echo "📋 Recent log entries:"
    tail -2 "$HOME/.claude/hooks-logs/context-monitor.log"
else
    echo "⚠️  No log file found yet"
fi

echo ""
echo "✅ Test complete!"
echo ""
echo "If you didn't see notifications, check:"
echo "1. Is notify-send installed? Run: which notify-send"
echo "2. Is your desktop environment configured for notifications?"
echo "3. Check the hook log: cat ~/.claude/hooks-logs/context-monitor.log"
