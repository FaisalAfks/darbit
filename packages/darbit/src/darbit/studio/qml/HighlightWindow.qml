// Highlight: what's found on screen right now, over the game. Each picture found gets its box and score; one just
// under what it needs gets a faint one. Clicks go through to the game. Ctrl+Alt+H (or Esc in the Studio) hides it.
import QtQuick
import QtQuick.Window

Window {
    id: overlay
    visibility: highlight.isOn ? Window.FullScreen : Window.Hidden
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput | Qt.Tool
    color: "transparent"
    title: "darbit Highlight"

    Repeater {
        model: highlight.boxes.filter(function (box) { return box.shown || (!box.found && box.w && box.score >= box.needs - 0.15) })
        delegate: Item {
            required property var modelData
            x: modelData.x - highlight.origin[0]; y: modelData.y - highlight.origin[1]
            width: modelData.w; height: modelData.h
            readonly property bool alike: modelData.with && modelData.with.length > 0
            readonly property color ink: modelData.found && !alike ? studio.colors.ok : studio.colors.warn
            opacity: modelData.found ? 1 : 0.55
            Rectangle {
                anchors.fill: parent; anchors.margins: -3
                radius: 6; color: "transparent"
                border.width: 2
                border.color: parent.ink
            }
            Rectangle {
                x: -3; y: -height - 6
                width: lines.implicitWidth + 14; height: lines.implicitHeight + 6; radius: 10
                color: Qt.rgba(0.04, 0.05, 0.08, 0.85)
                border.color: parent.ink
                Column {
                    id: lines
                    anchors.centerIn: parent
                    Text {
                        text: (parent.parent.parent.alike ? "⚠ " : "") + modelData.name + "  " + modelData.score.toFixed(2)
                        color: parent.parent.parent.ink
                        font.pixelSize: 12; font.weight: Font.DemiBold
                    }
                    Text {
                        visible: parent.parent.parent.alike
                        text: "also " + (modelData.with || []).join(", ")
                        color: studio.colors.muted
                        font.pixelSize: 11
                    }
                }
            }
        }
    }

    // what this is, at the top
    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        y: 14
        width: info.implicitWidth + 32; height: 40; radius: 20
        color: studio.colors.glassStrong; border.color: studio.colors.line
        Row {
            id: info
            anchors.centerIn: parent; spacing: 10
            Rectangle { width: 9; height: 9; radius: 4.5; color: studio.colors.ok; anchors.verticalCenter: parent.verticalCenter }
            Text {
                text: "Highlight · " + (studio.bot.name || "") + " · " + highlight.found + " of " + highlight.boxes.length + " found"
                    + (highlight.alike ? " · " + highlight.alike + " look-alikes (try the colour option)" : "")
                    + " · " + Math.round(highlight.took) + " ms · Ctrl+Alt+H hides"
                color: studio.colors.text; font.pixelSize: 13; font.weight: Font.DemiBold
            }
        }
    }
}
