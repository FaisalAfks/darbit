// The run pill (#245): while a bot runs, the Studio hides and this shows at the top of the screen: the bot, where it
// is and for how long, Pause, Stop and ⤢ back to the Studio. It slides out of sight a few seconds after the mouse
// leaves it; moving the mouse to the top edge brings it back (PillWindow, hiding.py).
import QtQuick
import QtQuick.Layouts
import "format.js" as Format

PillWindow {
    id: runWindow
    hiding: runPill
    title: "darbit run pill"
    readonly property string state: studio.bot.status || "stopped"
    readonly property color dot: state === "running" ? studio.colors.ok : state === "paused" ? studio.colors.warn : studio.colors.faint
    readonly property var now: {
        var tiles = studio.overview
        for (var index = 0; index < tiles.length; index++)
            if (tiles[index].kind === "now") return tiles[index].data
        return null
    }
    readonly property var steps: now && now.path ? now.path.map(function (step) { return String(step).split(" > ").pop() }) : []

    Timer { interval: 1000; running: runPill.isOpen && !runPill.tucked; repeat: true; onTriggered: studio.tick() }

    Row {
        Layout.leftMargin: 12; Layout.rightMargin: 12
        spacing: 9
        Rectangle { width: 11; height: 11; radius: 5.5; color: runWindow.dot; anchors.verticalCenter: parent.verticalCenter }
        Text {
            text: studio.bot.name || "darbit"
            color: studio.colors.text; font.pixelSize: 14; font.weight: Font.Bold
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            readonly property string where: runWindow.state === "paused" ? "Paused" : runWindow.steps.join(" › ")
            readonly property string time: studio.bot.since ? Format.duration(studio.now - studio.bot.since) : ""
            text: [where, time].filter(function (part) { return part !== "" }).join(" · ")
            width: Math.min(implicitWidth, 420); elide: Text.ElideLeft
            color: studio.colors.muted; font.pixelSize: 13
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 24; color: studio.colors.line }
    IconButton {
        glyph: runWindow.state === "paused" ? "▶" : "❚❚"
        tip: runWindow.state === "paused" ? "Go on" : "Pause"
        onClicked: studio.pause()
    }
    IconButton { glyph: "■"; tip: "Stop the bot"; onClicked: studio.stop() }
    IconButton { glyph: "⤢"; tip: "Open darbit Studio"; onClicked: runPill.close() }
}
