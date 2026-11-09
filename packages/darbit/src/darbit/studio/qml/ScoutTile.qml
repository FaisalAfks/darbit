// One image in Scout's pill: its picture framed in its state's colour (seen, weak, not seen yet), its name, and its
// best score or where it belongs. `on` is the one landed on. A click lands on it; `compact` is the floating card's grid,
// with the picture only.
import QtQuick
import QtQuick.Controls.Basic
import "scout.js" as Scout

Rectangle {
    id: tile
    required property var image
    property bool on: false
    property bool compact: false  // the floating card's grid: the picture and its state only
    signal picked()
    readonly property color ink: Scout.ink(studio.colors, image)
    width: compact ? 56 : 124
    height: compact ? 44 : 100
    radius: compact ? 9 : 12
    color: on ? studio.colors.raisedHover : area.containsMouse ? studio.colors.raised : "transparent"
    border.color: on ? studio.colors.accent : "transparent"
    border.width: 2

    Rectangle {
        id: frame
        x: tile.compact ? 4 : 6; y: x
        width: parent.width - 2 * x
        height: tile.compact ? parent.height - 2 * y : 56
        radius: tile.compact ? 6 : 8
        color: studio.colors.bg
        border.color: tile.ink
        border.width: tile.image.state === "not" ? 1 : 2
        opacity: tile.image.state === "not" ? 0.7 : 1
        clip: true
        Thumbnail {
            anchors.fill: parent; anchors.margins: 3
            source: tile.image.file
        }
    }
    Text {
        id: nameText
        visible: !tile.compact
        x: 8; anchors.top: frame.bottom; anchors.topMargin: 5
        width: parent.width - 14
        text: tile.image.name
        elide: Text.ElideMiddle
        color: studio.colors.text; font.family: "monospace"; font.pixelSize: 11
    }
    Row {
        visible: !tile.compact
        x: 8; anchors.bottom: parent.bottom; anchors.bottomMargin: 6
        spacing: 6
        Chip {
            visible: tile.image.state !== "not"
            height: 18
            tone: tile.image.state === "seen" ? "ok" : "warn"
            text: tile.image.best.toFixed(2)
        }
        Text {
            text: tile.image.state === "not" ? "not seen · " + tile.image.screen : tile.image.seenOn
            color: studio.colors.muted; font.pixelSize: 11
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    MouseArea {
        id: area
        anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
        onClicked: tile.picked()
    }
    // a name too long for the tile: whole on hover
    ToolTip.visible: area.containsMouse && nameText.visible && nameText.truncated
    ToolTip.text: nameText.text
    ToolTip.delay: 400
}
