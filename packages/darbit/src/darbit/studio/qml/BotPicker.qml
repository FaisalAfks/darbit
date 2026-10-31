// The bot picker: the chosen bot's square and name; a menu of every bot the service knows.
import QtQuick
import QtQuick.Controls.Basic

Pill {
    id: pill
    Item {
        width: row.implicitWidth + 16; height: 40
        Row {
            id: row
            anchors.verticalCenter: parent.verticalCenter
            x: 4; spacing: 10
            Avatar { name: studio.bot.name || ""; accent: studio.bot.accent || ""; size: 32; radius: 16 }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: studio.bot.name || "no bots"
                color: studio.colors.text
                font.pixelSize: 15; font.weight: Font.Bold
            }
            Text { anchors.verticalCenter: parent.verticalCenter; text: "▾"; color: studio.colors.muted; font.pixelSize: 12 }
        }
        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: menu.open() }
        Menu {
            id: menu
            y: parent.height + 8
            background: Rectangle {
                implicitWidth: 260; radius: 12
                color: studio.colors.glassStrong; border.color: studio.colors.line
            }
            Repeater {
                model: studio.bots
                delegate: MenuItem {
                    required property var modelData
                    text: modelData.name + "  ·  " + modelData.status
                    onTriggered: studio.selectBot(modelData.path)
                    contentItem: Text { text: parent.text; color: studio.colors.text; leftPadding: 8 }
                    background: Rectangle { color: parent.highlighted ? studio.colors.raisedHover : "transparent"; radius: 8 }
                }
            }
        }
    }
}
