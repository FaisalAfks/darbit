// A thin progress bar: `share` from 0 to 1, in `tint` or the accent's two colours, growing into place. With `shares`
// (each from 0 to 1) and their `tints`, it's a stacked bar: one part after another (gains by source).
import QtQuick

Rectangle {
    id: bar
    property real share: 0
    property color tint: studio.colors.ok
    property bool gradientFill: false
    property var shares: []
    property var tints: []
    height: 7; radius: 3.5
    color: studio.colors.raised
    Rectangle {
        visible: bar.shares.length === 0
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
    Row {
        visible: bar.shares.length > 0
        height: parent.height
        Repeater {
            model: bar.shares.length
            delegate: Rectangle {
                required property int index
                readonly property bool first: index === 0
                readonly property bool last: index === bar.shares.length - 1
                height: bar.height
                width: bar.width * Math.max(0, Math.min(Number(bar.shares[index]) || 0, 1))
                color: bar.tints[index] || bar.tint
                // only the bar's two ends are round
                topLeftRadius: first ? bar.radius : 0; bottomLeftRadius: first ? bar.radius : 0
                topRightRadius: last ? bar.radius : 0; bottomRightRadius: last ? bar.radius : 0
                Behavior on width { NumberAnimation { duration: studio.effects ? 500 : 0; easing.type: Easing.OutCubic } }
            }
        }
    }
}
