// Scout's boxes: what's found on screen right now, over the game. Each image found gets its box and score; one just
// under what it needs gets a faint one. Clicks go through to the game. Scout's key hides it; ScoutPill says what's
// been seen.
import QtQuick
import QtQuick.Window

Window {
    id: overlay
    visibility: scout.isOn ? Window.FullScreen : Window.Hidden
    transientParent: null  // its own window: it shows while the Studio is hidden (Windows hides a hidden window's tool windows too)
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput | Qt.Tool
    color: "transparent"
    title: "darbit Scout"
    readonly property real ratio: Screen.devicePixelRatio  // screen pixels to Qt's (1.5 at 150% scaling)

    Repeater {
        model: scout.boxes.filter(function (box) { return box.shown || (!box.found && box.w && box.score >= box.needs - 0.15) })
        delegate: Item {
            required property var modelData
            // boxes come in screen pixels; the window counts in Qt's, which Windows' display scaling makes bigger
            x: modelData.x / overlay.ratio - overlay.x; y: modelData.y / overlay.ratio - overlay.y
            width: modelData.w / overlay.ratio; height: modelData.h / overlay.ratio
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
}
