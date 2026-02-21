// Z.ai Usage Bar Widget
// Displays percentage in the status bar

import QtQuick
import Quickshell
import qs.Commons
import qs.Widgets
import qs.Services.UI

Item {
  id: root

  property var pluginApi: null
  property ShellScreen screen
  property string widgetId: ""
  property string section: ""
  property int sectionWidgetIndex: -1
  property int sectionWidgetsCount: 0

  readonly property var mainInstance: pluginApi?.mainInstance

  // Get values from main instance
  property int sessionPercent: mainInstance ? mainInstance.sessionPercent : 0
  property int weeklyPercent: mainInstance ? mainInstance.weeklyPercent : 0
  property int searchPercent: mainInstance ? mainInstance.searchPercent : 0
  property string sessionReset: mainInstance ? mainInstance.sessionReset : ""
  property string weeklyReset: mainInstance ? mainInstance.weeklyReset : ""
  property string searchReset: mainInstance ? mainInstance.searchReset : ""
  property bool loading: mainInstance ? mainInstance.loading : false
  property string error: mainInstance ? mainInstance.error : ""

  // Computed display values
  property string displayText: {
    if (!mainInstance) return "..."
    if (loading) return "..."
    if (error) {
      if (error === "NO_KEY") return "NO KEY"
      return "—"
    }
    var pct = sessionPercent
    if (pct > 100) return pct + "%!"
    return pct + "%"
  }

  property color displayColor: {
    if (!mainInstance || loading) return "#999999"
    if (error) {
      if (error === "NO_KEY") return "#FF9500"
      return "#999999"
    }
    var pct = sessionPercent
    if (pct > 100) return "#FF0000"
    if (pct >= 75) return "#FF3B30"
    if (pct >= 50) return "#FFCC00"
    return "#34C759"
  }

  // Tooltip text with table format
  property string tooltipText: {
    if (!mainInstance) return "Loading..."
    if (error) return "Error: " + error

    var lines = ["Z.ai Usage"]
    if (sessionPercent > 0) {
      lines.push("Session (5h): " + sessionPercent + "%" + (sessionReset ? "\n  Reset: " + sessionReset : ""))
    }
    if (weeklyPercent > 0) {
      lines.push("Weekly: " + weeklyPercent + "%" + (weeklyReset ? "\n  Reset: " + weeklyReset : ""))
    }
    if (searchPercent > 0) {
      lines.push("Search (monthly): " + searchPercent + "%" + (searchReset ? "\n  Reset: " + searchReset : ""))
    }
    if (mainInstance.planLevel) lines.push("Plan: " + mainInstance.planLevel)
    return lines.join("\n")
  }

  // Size
  implicitWidth: 50
  implicitHeight: 24

  // Background
  Rectangle {
    anchors.fill: parent
    radius: 4
    color: "#2A2A2A"
  }

  // Text
  Text {
    anchors.centerIn: parent
    text: displayText
    font.pixelSize: 12
    font.family: "monospace"
    color: displayColor
  }

  // Mouse area for tooltip
  MouseArea {
    anchors.fill: parent
    hoverEnabled: true
    onHoveredChanged: {
      if (containsMouse) {
        TooltipService.show(root, tooltipText, BarService.getTooltipDirection(root.screenName))
      } else {
        TooltipService.hide()
      }
    }
  }
}
