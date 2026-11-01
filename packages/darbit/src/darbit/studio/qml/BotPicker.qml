// The bot menu (without the sidebar): the chosen bot; its menu lists every bot, New bot and darbit's settings.
import QtQuick
import QtQuick.Controls.Basic

Rectangle {
    id: picker
    signal addBot()
    signal openStudio()
    height: 48
    implicitWidth: row.implicitWidth + 28
    radius: 24
    color: area.containsMouse ? studio.colors.raisedHover : studio.colors.glass
    border.color: studio.colors.line
    Behavior on color { ColorAnimation { duration: studio.effects ? 120 : 0 } }

    Row {
        id: row
        x: 8; anchors.verticalCenter: parent.verticalCenter
        spacing: 10
        Avatar { name: studio.bot.name || ""; accent: studio.bot.accent || ""; size: 32; radius: 16 }
        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: studio.bot.name || "No bots yet"
            color: studio.colors.text
            font.pixelSize: 15; font.weight: Font.Bold
        }
        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: "▾"; color: studio.colors.muted; font.pixelSize: 12
            rotation: menu.opened ? 180 : 0
            Behavior on rotation { NumberAnimation { duration: studio.effects ? 160 : 0 } }
        }
    }
    MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: menu.open() }

    Popup {
        id: menu
        y: picker.height + 10
        width: 320
        padding: 8
        background: Rectangle { radius: 16; color: studio.colors.glassStrong; border.color: studio.colors.line }
        enter: Transition {
            ParallelAnimation {
                NumberAnimation { property: "opacity"; from: 0; to: 1; duration: studio.effects ? 150 : 0 }
                NumberAnimation { property: "scale"; from: 0.96; to: 1; duration: studio.effects ? 180 : 0; easing.type: Easing.OutCubic }
            }
        }
        exit: Transition { NumberAnimation { property: "opacity"; to: 0; duration: studio.effects ? 100 : 0 } }
        contentItem: Column {
            spacing: 2
            Repeater {
                model: studio.bots
                delegate: BotRow {
                    required property var modelData
                    width: 304
                    bot: modelData
                    onClicked: { studio.selectBot(modelData.path); menu.close() }
                }
            }
            Rectangle { width: 304; height: 1; color: studio.colors.line }
            MenuLine { text: "New bot…"; icon: "＋"; onClicked: { menu.close(); picker.addBot() } }
            MenuLine { text: "darbit settings"; icon: "⚙"; onClicked: { menu.close(); picker.openStudio() } }
        }
    }
}
