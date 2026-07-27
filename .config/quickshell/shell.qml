import Quickshell
import Quickshell.I3
import Quickshell.Services.SystemTray
import Quickshell.Widgets
import QtQuick
import QtQuick.Layouts

Scope {
  id: root

  readonly property color accent: "#DE8A4B"
  readonly property color background: "#11100F"
  readonly property color surface: "#1B1917"
  readonly property color surfaceHover: "#25211E"
  readonly property color panelBorder: "#332E29"
  readonly property color text: "#F1EADF"
  readonly property color mutedText: "#9B9286"
  readonly property color urgent: "#D45D50"

  readonly property string currentDate: Qt.formatDateTime(clock.date, "ddd, MMM d")
  readonly property string currentTime: Qt.formatDateTime(clock.date, "h:mm AP")

  SystemClock {
    id: clock
    precision: SystemClock.Minutes
  }

  Variants {
    model: Quickshell.screens

    PanelWindow {
      id: bar

      required property var modelData

      screen: bar.modelData
      color: root.background
      exclusiveZone: 38
      implicitHeight: 38

      anchors {
        left: true
        right: true
        bottom: true
      }

      Rectangle {
        anchors.fill: parent
        color: root.background

        Rectangle {
          anchors.left: parent.left
          anchors.right: parent.right
          anchors.top: parent.top
          height: 1
          color: root.panelBorder
        }

        Rectangle {
          anchors.left: parent.left
          anchors.top: parent.top
          width: 72
          height: 1
          color: root.accent
        }

        Item {
          anchors.fill: parent

          RowLayout {
            anchors.left: parent.left
            anchors.leftMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            spacing: 3

            Repeater {
              model: I3.workspaces

              Rectangle {
                id: workspaceButton

                required property var modelData

                radius: 3
                color: modelData.urgent
                  ? root.urgent
                  : modelData.active
                    ? root.accent
                    : workspaceMouse.containsMouse
                      ? root.surfaceHover
                      : "transparent"

                Layout.preferredHeight: 26
                Layout.preferredWidth: Math.max(30, workspaceLabel.implicitWidth + 16)

                Text {
                  id: workspaceLabel
                  anchors.centerIn: parent
                  color: modelData.active || modelData.urgent ? root.background : root.mutedText
                  text: modelData.name
                  font.family: "JetBrainsMono Nerd Font"
                  font.pixelSize: 11
                  font.weight: Font.DemiBold
                }

                MouseArea {
                  id: workspaceMouse
                  anchors.fill: parent
                  hoverEnabled: true
                  cursorShape: Qt.PointingHandCursor
                  onClicked: workspaceButton.modelData.activate()
                }
              }
            }
          }

          RowLayout {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            spacing: 7

            Rectangle {
              Layout.preferredWidth: 5
              Layout.preferredHeight: 5
              radius: 3
              color: root.accent
            }

            Text {
              color: root.mutedText
              elide: Text.ElideRight
              text: "i3  /  " + bar.modelData.name
              font.family: "JetBrainsMono Nerd Font"
              font.pixelSize: 10
              font.capitalization: Font.AllUppercase
            }
          }

          RowLayout {
            anchors.right: parent.right
            anchors.rightMargin: 12
            anchors.verticalCenter: parent.verticalCenter
            spacing: 8

            RowLayout {
              visible: SystemTray.items.values.length > 0
              spacing: 2

              Repeater {
                model: SystemTray.items

                Rectangle {
                  id: trayButton

                  required property var modelData
                  readonly property bool usesKeyboardFallback:
                    modelData.icon.toString().includes("input-keyboard-symbolic")

                  color: trayMouse.containsMouse ? root.surfaceHover : "transparent"
                  radius: 3
                  Layout.preferredWidth: 28
                  Layout.preferredHeight: 26

                  IconImage {
                    anchors.centerIn: parent
                    implicitSize: 17
                    source: trayButton.usesKeyboardFallback ? "" : trayButton.modelData.icon
                  }

                  Text {
                    anchors.centerIn: parent
                    visible: trayButton.usesKeyboardFallback
                    color: root.mutedText
                    text: ""
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 15
                  }

                  TrayMenu {
                    id: trayMenu

                    menu: trayButton.modelData.menu
                    anchorItem: trayButton
                    barWindow: bar
                    accent: root.accent
                    background: root.surface
                    border: root.panelBorder
                    text: root.text
                    mutedText: root.mutedText
                    hover: root.surfaceHover
                  }

                  MouseArea {
                    id: trayMouse

                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor

                    onClicked: function(mouse) {
                      if (mouse.button === Qt.RightButton && trayButton.modelData.hasMenu) {
                        trayMenu.open()
                      } else if (mouse.button === Qt.MiddleButton) {
                        trayButton.modelData.secondaryActivate()
                      } else {
                        trayButton.modelData.activate()
                      }
                    }

                    onWheel: function(wheel) {
                      trayButton.modelData.scroll(wheel.angleDelta.y, false)
                    }
                  }
                }
              }
            }

            Rectangle {
              visible: SystemTray.items.values.length > 0
              Layout.preferredWidth: 1
              Layout.preferredHeight: 18
              color: root.panelBorder
            }

            Text {
              color: root.mutedText
              text: root.currentDate
              font.family: "JetBrainsMono Nerd Font"
              font.pixelSize: 11
            }

            Text {
              color: root.text
              text: root.currentTime
              font.family: "JetBrainsMono Nerd Font"
              font.pixelSize: 11
              font.weight: Font.DemiBold
            }
          }
        }
      }
    }
  }
}
