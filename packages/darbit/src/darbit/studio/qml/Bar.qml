// A thin progress bar: `share` from 0 to 1, in `tint` or the accent's two colours, growing into place.
import QtQuick

Rectangle {
    id: bar
    property real share: 0
    property color tint: studio.colors.ok
    property bool gradientFill: false
    height: 7; radius: 3.5
    color: studio.colors.raised
    Rectangle {
        height: parent.height; radius: parent.radius
        width: parent.width * Math.max(0, Math.min(bar.share, 1))
        color: bar.tint
        gradient: bar.gradientFill ? accentFill : null
        Gradient {
            id: accentFill
            orientation: Gradient.Horizontal
            GradientStop { position: 0; color: studio.colors.accent }
            GradientStop { position: 1; color: studio.colors.accent2 }
        }
        Behavior on width { NumberAnimation { duration: studio.effects ? 500 : 0; easing.type: Easing.OutCubic } }
    }
}
