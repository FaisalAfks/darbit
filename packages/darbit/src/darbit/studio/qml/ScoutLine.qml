// One image in Scout's pill docked on a side: its picture in its state's colour, its name and best score, why it's
// weak, and its screen or score. Hovered, its retakes: on the shot where it was last seen, and on the screen now
// (only now for one never seen). A click lands on it.
import QtQuick
import "scout.js" as Scout

Rectangle {
    id: line
    required property var image
    property bool on: false
    signal picked()
    signal retakeOnShot()
    signal retakeNow()
    readonly property color ink: Scout.ink(studio.colors, image)
    readonly property bool open: area.containsMouse || on
    readonly property string reason: Scout.shortReason(image)
    width: 360
    height: reason !== "" ? 44 : 36
    radius: 10
    color: open ? studio.colors.raised : "transparent"

    MouseArea {
        id: area
        anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
        onClicked: line.picked()
    }
    Rectangle {
        id: thumb
        x: 10; anchors.verticalCenter: parent.verticalCenter
        width: 34; height: 24; radius: 5
        color: studio.colors.bg
        border.color: line.ink; border.width: line.image.state === "not" ? 1 : 2
        opacity: line.image.state === "not" ? 0.7 : 1
        clip: true
        Thumbnail {
            anchors.fill: parent; anchors.margins: 2
            source: line.image.file
        }
    }
    Column {
        anchors { left: thumb.right; leftMargin: 10; right: side.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
        Row {
            spacing: 6
            Text {
                text: line.image.name
                color: studio.colors.text; font.family: "monospace"; font.pixelSize: 12
            }
            Text {
                visible: line.image.state === "weak"
                text: line.image.best.toFixed(2)
                color: studio.colors.warn; font.family: "monospace"; font.pixelSize: 12
            }
        }
        Text {
            visible: line.reason !== ""
            text: line.reason
            color: studio.colors.warn; font.pixelSize: 11
        }
    }
    // its screen or score, or, hovered, its retakes
    Item {
        id: side
        anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
        width: line.open ? retakes.width : rest.width
        height: 28
        Text {
            id: rest
            visible: !line.open || !retakes.visible
            anchors { right: parent.right; verticalCenter: parent.verticalCenter }
            text: line.image.state === "not" ? line.image.screen : line.image.state === "weak" ? line.image.seenOn : ""
            color: studio.colors.muted; font.pixelSize: 12
        }
        Chip {
            visible: line.image.state === "seen" && !line.open
            anchors { right: parent.right; verticalCenter: parent.verticalCenter }
            height: 20; tone: "ok"; text: line.image.best.toFixed(2)
        }
        Row {
            id: retakes
            visible: line.open
            anchors { right: parent.right; verticalCenter: parent.verticalCenter }
            spacing: 6
            PillButton {
                objectName: "lineRetakeOnShot"
                visible: line.image.shot !== ""
                small: true; icon: "⟲"; text: line.image.seenOn
                onClicked: line.retakeOnShot()
            }
            PillButton { small: true; icon: "⟲"; text: "now"; onClicked: line.retakeNow() }
        }
    }
}
