// A soft accent light that follows the mouse over a card or tile (#441), inside its rounded edge. It's made only while
// the mouse is on the card: at rest nothing of it is drawn. Put it in the card, before its contents.
import QtQuick
import QtQuick.Shapes

Item {
    id: light
    property bool hovered: false
    property point at: Qt.point(width / 2, height / 2)  // the mouse, in the card
    property real radius: 16
    readonly property real reach: 240
    anchors.fill: parent
    opacity: hovered && studio.motion.on ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: studio.motion.slow; easing.type: Easing.BezierSpline; easing.bezierCurve: studio.motion.ease } }

    Loader {
        anchors.fill: parent
        active: light.opacity > 0
        sourceComponent: Shape {
            ShapePath {
                strokeWidth: -1
                fillGradient: RadialGradient {
                    centerX: light.at.x; centerY: light.at.y; centerRadius: light.reach
                    focalX: light.at.x; focalY: light.at.y
                    GradientStop { position: 0; color: Qt.rgba(studio.colors.accent.r, studio.colors.accent.g, studio.colors.accent.b, 0.16) }
                    GradientStop { position: 0.6; color: Qt.rgba(studio.colors.accent.r, studio.colors.accent.g, studio.colors.accent.b, 0) }
                }
                PathRectangle { x: 0; y: 0; width: light.width; height: light.height; radius: light.radius }
            }
        }
    }
}
