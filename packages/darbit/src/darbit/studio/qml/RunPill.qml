// The run controls: the bot's state and how long it has run, Play or Pause, and Stop.
import QtQuick
import "format.js" as Format

Pill {
    id: pill
    readonly property string state: studio.bot.status || "stopped"
    readonly property bool active: state === "running" || state === "paused"
    readonly property color dot: state === "running" ? studio.colors.ok : state === "paused" ? studio.colors.warn
        : state === "failed" ? studio.colors.danger : studio.colors.faint

    Item {
        width: status.implicitWidth + 24; height: 40
        Row {
            id: status
            anchors.verticalCenter: parent.verticalCenter
            x: 12; spacing: 8
            Rectangle { width: 8; height: 8; radius: 4; color: pill.dot; anchors.verticalCenter: parent.verticalCenter }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: pill.state.charAt(0).toUpperCase() + pill.state.slice(1)
                color: studio.colors.text; font.pixelSize: 14; font.weight: Font.Bold
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                visible: pill.active && studio.bot.since
                text: Format.duration(studio.now - (studio.bot.since || studio.now))
                color: studio.colors.muted; font.pixelSize: 14
            }
        }
    }
    IconButton {
        glyph: pill.state === "running" ? "❚❚" : "▶"
        tip: pill.state === "running" ? "Pause" : (pill.active ? "Go on" : "Play")
        onClicked: pill.active ? studio.pause() : studio.start()
    }
    IconButton { glyph: "■"; tip: "Stop"; enabled: pill.active; onClicked: studio.stop() }
}
