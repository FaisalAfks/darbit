// A bot in the sidebar or the bot menu: its square, its name, what it's doing, and a dot for its state.
// `folded` shows the square alone.
import QtQuick
import QtQuick.Controls.Basic

Rectangle {
    id: row
    property var bot: ({})
    property bool folded: false
    readonly property bool chosen: bot.path === studio.bot.path
    readonly property string state: bot.status || "stopped"
    signal clicked()
    height: folded ? 48 : 52
    radius: 12
    color: chosen ? studio.colors.raisedHover : area.containsMouse ? studio.colors.raised : "transparent"
    Behavior on color { ColorAnimation { duration: studio.effects ? 120 : 0 } }

    Rectangle {  // the chosen bot's edge
        visible: row.chosen && !row.folded
        x: 0; y: 10; width: 3; height: row.height - 20; radius: 1.5
        color: studio.colors.accent
    }
    Avatar {
        id: square
        x: row.folded ? (row.width - width) / 2 : 12
        anchors.verticalCenter: parent.verticalCenter
        name: row.bot.name || ""; accent: row.bot.accent || ""; size: 32
        Rectangle {  // the state, on the square's corner when folded
            visible: row.folded && row.state !== "stopped"
            anchors { right: parent.right; bottom: parent.bottom; margins: -3 }
            width: 12; height: 12; radius: 6
            color: row.state === "running" ? studio.colors.ok : row.state === "paused" ? studio.colors.warn : studio.colors.danger
            border.color: studio.colors.bg; border.width: 2
        }
    }
    Column {
        visible: !row.folded
        anchors { left: square.right; leftMargin: 12; right: dot.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
        Text { width: parent.width; text: row.bot.name || ""; color: studio.colors.text; font.pixelSize: 14; font.weight: Font.DemiBold; elide: Text.ElideRight }
        Text {
            width: parent.width; elide: Text.ElideRight
            text: row.bot.error ? "can't load: see its darbit.toml" : row.state === "stopped" ? (row.bot.summary || "stopped") : row.state
            color: row.bot.error ? studio.colors.danger : row.state === "running" ? studio.colors.ok : studio.colors.muted
            font.pixelSize: 12
        }
    }
    Rectangle {
        id: dot
        visible: !row.folded
        anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
        width: 8; height: 8; radius: 4
        color: row.state === "running" ? studio.colors.ok : row.state === "paused" ? studio.colors.warn
            : row.state === "failed" ? studio.colors.danger : studio.colors.faint
    }
    MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: row.clicked() }
    ToolTip.visible: row.folded && area.containsMouse
    ToolTip.text: (bot.name || "") + " · " + row.state
    ToolTip.delay: 300
}
