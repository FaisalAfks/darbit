// The bots, down the left side (a Studio setting): every bot, New bot at the bottom, darbit's settings in the footer.
// On a narrow window it folds to the bots' squares.
import QtQuick
import QtQuick.Controls.Basic

Rectangle {
    id: side
    property bool folded: false
    signal addBot()
    signal openStudio()
    implicitWidth: folded ? 76 : 256
    Behavior on implicitWidth { NumberAnimation { duration: studio.effects ? 220 : 0; easing.type: Easing.OutCubic } }
    color: Qt.rgba(1, 1, 1, studio.glass ? 0.025 : 0.0)
    clip: true
    Rectangle { anchors { right: parent.right; top: parent.top; bottom: parent.bottom } width: 1; color: studio.colors.line }

    Row {  // darbit
        id: brand
        x: side.folded ? 22 : 20; y: 22
        spacing: 10
        Image { source: "../logo.png"; width: 32; height: 32; sourceSize: Qt.size(64, 64); smooth: true }
        Text {
            visible: !side.folded
            text: "darbit Studio"; color: studio.colors.text
            font.pixelSize: 15; font.weight: Font.Bold
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    Text {
        visible: !side.folded
        x: 22; y: brand.y + 54
        text: "BOTS"; color: studio.colors.faint
        font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 1.4
    }
    ListView {
        id: list
        x: 10; y: brand.y + (side.folded ? 52 : 76)
        width: side.width - 20
        height: footer.y - y - 64
        clip: true
        spacing: 2
        model: studio.bots
        boundsBehavior: Flickable.StopAtBounds
        delegate: BotRow {
            required property var modelData
            width: list.width
            bot: modelData
            folded: side.folded
            onClicked: studio.selectBot(modelData.path)
        }
        add: Transition { NumberAnimation { property: "opacity"; from: 0; to: 1; duration: studio.effects ? 200 : 0 } }
    }
    Rectangle {  // New bot
        id: add
        x: 12; y: footer.y - 56
        width: side.width - 24; height: 44; radius: 12
        color: addArea.containsMouse ? studio.colors.raised : "transparent"
        border.color: addArea.containsMouse ? studio.colors.accent : Qt.rgba(1, 1, 1, 0.16)
        Behavior on border.color { ColorAnimation { duration: studio.effects ? 120 : 0 } }
        Text {
            anchors.centerIn: parent
            text: side.folded ? "＋" : "＋  New bot"
            color: addArea.containsMouse ? studio.colors.accent : studio.colors.muted
            font.pixelSize: 14; font.weight: Font.DemiBold
        }
        MouseArea { id: addArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: side.addBot() }
        ToolTip.visible: side.folded && addArea.containsMouse
        ToolTip.text: "New bot (Ctrl+N)"
    }
    Rectangle {  // darbit's settings
        id: footer
        x: 10; y: side.height - height - 12
        width: side.width - 20; height: 44; radius: 12
        color: footArea.containsMouse ? studio.colors.raised : "transparent"
        Row {
            x: side.folded ? (parent.width - 16) / 2 : 12; anchors.verticalCenter: parent.verticalCenter; spacing: 10
            Text { text: "⚙"; color: studio.colors.muted; font.pixelSize: 15 }
            Text { visible: !side.folded; text: "darbit settings"; color: studio.colors.muted; font.pixelSize: 14; font.weight: Font.DemiBold }
        }
        MouseArea { id: footArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: side.openStudio() }
        ToolTip.visible: side.folded && footArea.containsMouse
        ToolTip.text: "darbit settings (Ctrl+,)"
    }
}
