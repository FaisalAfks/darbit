// Behind every page: the theme's background, with soft light in its corners in the glass themes. With the aurora on
// (darbit settings) the light drifts slowly back and forth: only while the window is in sight, never on battery, and
// stepped 10 times a second, which is plenty for something this slow.
import QtQuick
import QtQuick.Shapes

Rectangle {
    id: backdrop
    color: studio.colors.bg

    readonly property int drift: 18000  // one way, in milliseconds
    readonly property bool drifting: studio.aurora && studio.glass && studio.motion.on && !studio.onBattery
    property real phase: 0  // 0 to 2 and round again: there and back
    readonly property real along: phase <= 1 ? phase : 2 - phase
    readonly property real eased: studio.aurora ? (1 - Math.cos(Math.PI * along)) / 2 : 0  // slow at each end
    Timer {
        interval: 100
        repeat: true
        running: backdrop.drifting
        onTriggered: backdrop.phase = (backdrop.phase + interval / backdrop.drift) % 2
    }
    Connections {
        target: studio
        function onLookChanged() { if (!studio.aurora) backdrop.phase = 0 }
    }

    Item {
        anchors.fill: parent
        transform: [
            Rotation { origin.x: backdrop.width / 2; origin.y: backdrop.height / 2; angle: 6 * backdrop.eased },
            Translate { x: 0.04 * backdrop.width * backdrop.eased; y: -0.03 * backdrop.height * backdrop.eased }
        ]
        Repeater {
            model: studio.glass ? [
                { x: 0.18, y: 0.02, size: 0.75, tint: studio.colors.accent2, alpha: 0.16 },
                { x: 0.70, y: 0.78, size: 0.45, tint: studio.colors.ok, alpha: 0.07 },
                { x: 0.92, y: 0.98, size: 0.6, tint: studio.colors.warn, alpha: 0.07 }
            ] : []
            delegate: Shape {
                required property var modelData
                readonly property color tint: Qt.lighter(modelData.tint, 1.0)  // the model holds the colour as text
                readonly property real reach: Math.max(backdrop.width, backdrop.height) * modelData.size / 2
                x: backdrop.width * modelData.x - reach; y: backdrop.height * modelData.y - reach
                width: reach * 2; height: reach * 2
                ShapePath {
                    strokeWidth: -1
                    fillGradient: RadialGradient {
                        centerX: reach; centerY: reach; centerRadius: reach
                        focalX: reach; focalY: reach
                        GradientStop { position: 0; color: Qt.rgba(tint.r, tint.g, tint.b, modelData.alpha) }
                        GradientStop { position: 1; color: Qt.rgba(tint.r, tint.g, tint.b, 0) }
                    }
                    startX: 0; startY: 0
                    PathLine { x: reach * 2; y: 0 }
                    PathLine { x: reach * 2; y: reach * 2 }
                    PathLine { x: 0; y: reach * 2 }
                    PathLine { x: 0; y: 0 }
                }
            }
        }
    }
}
