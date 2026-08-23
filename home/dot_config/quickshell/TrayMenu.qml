import Quickshell
import Quickshell.Widgets
import QtQuick
import QtQuick.Layouts

Scope {
  id: root

  required property var anchorItem
  required property var barWindow
  required property var menu

  property color accent: "#DE8A4B"
  property color background: "#1B1917"
  property color border: "#332E29"
  property color text: "#F1EADF"
  property color mutedText: "#9B9286"
  property color hover: "#25211E"

  function open(): void {
    popup.visible = true
  }

  QsMenuOpener {
    id: menuOpener
    menu: root.menu
  }

  PopupWindow {
    id: popup

    color: "transparent"
    grabFocus: true
    implicitWidth: 236
    implicitHeight: menuColumn.implicitHeight + 8
    visible: false

    anchor {
      window: root.barWindow
      item: root.anchorItem
      edges: Edges.Top
      gravity: Edges.Top
      adjustment: PopupAdjustment.SlideX | PopupAdjustment.FlipY
    }

    Rectangle {
      anchors.fill: parent
      color: root.background
      border.width: 1
      border.color: root.border
      radius: 4

      Column {
        id: menuColumn

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 4
        spacing: 0

        Repeater {
          model: menuOpener.children

          Item {
            id: menuEntry

            required property var modelData

            width: menuColumn.width
            height: modelData.isSeparator ? 9 : 30

            Rectangle {
              anchors.left: parent.left
              anchors.right: parent.right
              anchors.verticalCenter: parent.verticalCenter
              anchors.leftMargin: 8
              anchors.rightMargin: 8
              visible: menuEntry.modelData.isSeparator
              height: 1
              color: root.border
            }

            Rectangle {
              anchors.fill: parent
              visible: !menuEntry.modelData.isSeparator
              color: entryMouse.containsMouse ? root.hover : "transparent"
              radius: 3
            }

            RowLayout {
              anchors.fill: parent
              anchors.leftMargin: 8
              anchors.rightMargin: 8
              visible: !menuEntry.modelData.isSeparator
              spacing: 8

              Item {
                Layout.preferredWidth: 16
                Layout.preferredHeight: 16

                IconImage {
                  anchors.fill: parent
                  visible: menuEntry.modelData.icon !== ""
                  source: menuEntry.modelData.icon
                }

                Text {
                  anchors.centerIn: parent
                  visible: menuEntry.modelData.icon === ""
                    && menuEntry.modelData.buttonType !== QsMenuButtonType.None
                    && menuEntry.modelData.checkState === Qt.Checked
                  color: root.accent
                  text: "●"
                  font.pixelSize: 9
                }
              }

              Text {
                Layout.fillWidth: true
                color: menuEntry.modelData.enabled ? root.text : root.mutedText
                elide: Text.ElideRight
                text: menuEntry.modelData.text
                font.family: "JetBrainsMono Nerd Font"
                font.pixelSize: 11
              }

              Text {
                visible: menuEntry.modelData.hasChildren
                color: root.mutedText
                text: "›"
                font.pixelSize: 16
              }
            }

            MouseArea {
              id: entryMouse

              anchors.fill: parent
              enabled: !menuEntry.modelData.isSeparator && menuEntry.modelData.enabled
              hoverEnabled: enabled
              cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor

              onClicked: {
                menuEntry.modelData.triggered()
                popup.visible = false
              }
            }
          }
        }
      }
    }
  }
}
