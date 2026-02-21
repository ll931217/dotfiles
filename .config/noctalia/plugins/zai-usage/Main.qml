// Z.ai Usage Monitor - Main Plugin
// Monitors Z.ai coding plan usage

import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons

Item {
  id: root

  // Required by plugin system
  property var pluginApi: null

  // Exposed properties for bar widget
  property int sessionPercent: 0      //5-hour TOKENS_LIMIT (Session)
  property int weeklyPercent: 0       // Weekly TOKENS_LIMIT (5 sessions total)
  property int searchPercent: 0      // Monthly TIME_LIMIT (Search)
  property string sessionReset: ""      // Session reset time
  property string weeklyReset: ""       // Weekly reset time
  property string searchReset: ""      // Search reset time (monthly, 1st of month)
  property bool loading: false
  property string error: ""
  property string planLevel: ""

  // API configuration
  readonly property string apiUrl: "https://api.z.ai/api/monitor/usage/quota/limit"

  // Format Unix timestamp (ms) to YYYY-MM-DD HH:mm:ss
  function formatTimestamp(timestamp) {
    if (!timestamp) return ""
    var date = new Date(timestamp)
    var year = date.getFullYear()
    var month = String(date.getMonth() + 1).padStart(2, '0')
    var day = String(date.getDate()).padStart(2, '0')
    var hours = String(date.getHours()).padStart(2, '0')
    var minutes = String(date.getMinutes()).padStart(2, '0')
    var seconds = String(date.getSeconds()).padStart(2, '0')
    return year + "-" + month + "-" + day + " " + hours + ":" + minutes + ":" + seconds
  }

  // Fetch usage data
  function fetch() {
    loading = true
    error = ""
    fetchProcess.running = true
  }

  // Process for fetching API data
  Process {
    id: fetchProcess
    running: false
    command: [
      "bash", "-c",
      "API_KEY=$(cat ~/.config/opencode/opencode.json 2>/dev/null | jq -r '.provider.\"zai-coding-plan\".options.apiKey' 2>/dev/null); " +
      "if [ -z \"$API_KEY\" ] || [ \"$API_KEY\" = \"null\" ]; then " +
      "  echo \"NO_KEY\"; " +
      "else " +
      "  curl -s --max-time 10 -H \"Authorization: Bearer $API_KEY\" -H \"Content-Type: application/json\" '" + apiUrl + "'; " +
      "fi"
    ]

    stdout: StdioCollector {
      onStreamFinished: {
        root.loading = false
        var response = text.trim()
        
        if (response === "NO_KEY") {
          root.error = "NO_KEY"
          return
        }
        
        if (!response || response.length === 0) {
          root.error = "NETWORK_ERROR"
          return
        }
        
        try {
          var data = JSON.parse(response)
          if (!data.success) {
            root.error = "API_ERROR"
            return
          }
          root.parseResponse(data)
        } catch (e) {
          Logger.e("ZaiUsage", "Parse error: " + e)
          root.error = "PARSE_ERROR"
        }
      }
    }

    onExited: {
      if (exitCode !== 0) {
        root.loading = false
        root.error = "NETWORK_ERROR"
      }
    }
  }

  // Parse API response
  function parseResponse(data) {
    if (!data.data || !data.data.limits) {
      root.error = "INVALID_RESPONSE"
      return
    }

    var limits = data.data.limits
    root.planLevel = data.data.level || ""

    // Reset values
    root.sessionPercent = 0
    root.weeklyPercent = 0
    root.searchPercent = 0
    root.sessionReset = ""
    root.weeklyReset = ""
    root.searchReset = ""

    for (var i = 0; i < limits.length; i++) {
      var limit = limits[i]
      var type = limit.type
      var unit = limit.unit
      var percent = limit.percentage || 0
      var resetTime = limit.nextResetTime || 0

      if (type === "TOKENS_LIMIT" && unit === 3 && limit.number === 5) {
        // unit=3, number=5 = 5-hour rolling window (Session)
        root.sessionPercent = percent
        root.sessionReset = formatTimestamp(resetTime)
      } else if (type === "TOKENS_LIMIT" && unit === 6) {
        // unit=6 = Weekly total (5 sessions aggregated)
        root.weeklyPercent = percent
        root.weeklyReset = formatTimestamp(resetTime)
      } else if (type === "TIME_LIMIT" && unit === 5 && limit.number === 1) {
        // unit=5, number=1 = Monthly web search quota
        root.searchPercent = percent
        // TIME_LIMIT resets on 1st of each month at 00:00 UTC (no nextResetTime)
        root.searchReset = "Monthly (1st of month 00:00 UTC)"
      }
    }
    Logger.i("ZaiUsage", "Parsed: session=" + root.sessionPercent + " weekly=" + root.weeklyPercent + " search=" + root.searchPercent)
  }

  // Refresh timer - uses refreshIntervalSeconds from settings (default 60)
  Timer {
    id: refreshTimer
    interval: (pluginApi?.settings?.refreshIntervalSeconds || 60) * 1000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: {
      Logger.i("ZaiUsage", "Refreshing usage data...")
      root.fetch()
    }
  }

  // Initialize on load
  Component.onCompleted: {
    Logger.i("ZaiUsage", "Plugin loaded, starting refresh timer (interval: " + (pluginApi?.settings?.refreshIntervalSeconds || 60) + "s)")
  }
}
