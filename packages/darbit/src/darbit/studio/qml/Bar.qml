// A thin progress bar: `share` from 0 to 1 in `tint` (ok by default) on a faint track.
import QtQuick

Rectangle {
    property real share: 0
    property color tint: studio.colors.ok
    height: 8; radius: 4
    color: studio.colors.raised
    Rectangle {
        height: parent.height; radius: parent.radius
        width: parent.width * Math.max(0, Math.min(parent.share, 1))
        color: parent.tint
        Behavior on width { NumberAnimation { duration: 200; easing.type: Easing.OutCubic } }
    }
}
