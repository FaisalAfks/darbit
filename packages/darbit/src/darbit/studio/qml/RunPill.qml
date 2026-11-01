// The run pill (#245): while a bot runs, the Studio hides and this shows at the top of the screen: the bot, where it
// is and for how long, Pause, Stop and ⤢ back to the Studio. It slides up a few seconds after the mouse leaves it,
// leaving a sliver; moving the mouse to that edge brings it back (runpill.py). The bot never sees it in a capture.
import QtQuick
import QtQuick.Window
import "format.js" as Format

Window {
    id: pillWindow
    readonly property string state: studio.bot.status || "stopped"
    readonly property color dot: state === "running" ? studio.colors.ok : state === "paused" ? studio.colors.warn : studio.colors.faint
    readonly property var now: {
        var tiles = studio.overview
        for (var index = 0; index < tiles.length; index++)
            if (tiles[index].kind === "now") return tiles[index].data
        return null
    }
    readonly property var steps: now && now.path ? now.path.map(function (step) { return String(step).split(" > ").pop() }) : []
    readonly property real ratio: Screen.devicePixelRatio
    readonly property int shownY: Screen.virtualY + 14
    readonly property int peek: 4  // what's left showing when it's tucked away
    visible: runPill.isOpen
    transientParent: null  // its own window: it shows while the Studio is hidden
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowDoesNotAcceptFocus | Qt.Tool
    color: "transparent"
    title: "darbit run pill"
    width: pill.width + 24
    height: pill.height + 24
    x: Screen.virtualX + (Screen.width - width) / 2
    y: runPill.tucked ? Screen.virtualY - pill.y - pill.height + peek : shownY
    Behavior on y { NumberAnimation { duration: studio.effects ? 180 : 0; easing.type: Easing.OutCubic } }
    Component.onCompleted: ghost.keepOutOfCaptures(pillWindow)
    onXChanged: report()
    onWidthChanged: report()
    onHeightChanged: report()
    onVisibleChanged: report()
    // where it shows, in screen pixels (where it's tucked follows from it)
    function report() { runPill.setArea(Math.round(x * ratio), Math.round(Screen.virtualY * ratio), Math.round(width * ratio), Math.round((shownY - Screen.virtualY + height) * ratio)) }

    Timer { interval: 1000; running: runPill.isOpen && !runPill.tucked; repeat: true; onTriggered: studio.tick() }

    Rectangle {
        id: pill
        x: 12; y: 12
        width: row.implicitWidth + 16; height: 56; radius: 28
        color: studio.colors.glassStrong
        border.color: studio.colors.line
        Behavior on width { NumberAnimation { duration: studio.effects ? 180 : 0; easing.type: Easing.OutCubic } }

        Row {
            id: row
            x: 8; anchors.verticalCenter: parent.verticalCenter
            spacing: 4
            Item {
                width: label.implicitWidth + 24; height: 40
                Row {
                    id: label
                    x: 12; anchors.verticalCenter: parent.verticalCenter
                    spacing: 9
                    Rectangle {
                        width: 11; height: 11; radius: 5.5; color: pillWindow.dot
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    Text {
                        text: studio.bot.name || "darbit"
                        color: studio.colors.text; font.pixelSize: 14; font.weight: Font.Bold
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    Text {
                        readonly property string where: pillWindow.state === "paused" ? "Paused" : pillWindow.steps.join(" › ")
                        readonly property string time: studio.bot.since ? Format.duration(studio.now - studio.bot.since) : ""
                        text: [where, time].filter(function (part) { return part !== "" }).join(" · ")
                        width: Math.min(implicitWidth, 420); elide: Text.ElideLeft
                        color: studio.colors.muted; font.pixelSize: 13
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
            Rectangle { width: 1; height: 24; color: studio.colors.line; anchors.verticalCenter: parent.verticalCenter }
            IconButton {
                glyph: pillWindow.state === "paused" ? "▶" : "❚❚"
                tip: pillWindow.state === "paused" ? "Go on" : "Pause"
                anchors.verticalCenter: parent.verticalCenter
                onClicked: studio.pause()
            }
            IconButton { glyph: "■"; tip: "Stop the bot"; anchors.verticalCenter: parent.verticalCenter; onClicked: studio.stop() }
            IconButton { glyph: "⤢"; tip: "Open darbit Studio"; anchors.verticalCenter: parent.verticalCenter; onClicked: runPill.close() }
        }
    }
}
