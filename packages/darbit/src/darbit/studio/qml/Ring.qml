// A progress ring: `done` of `total` in the accent's two colours, the number in the middle and a caption under it.
// It sweeps from empty when its page shows and to its share when the number changes, and the number counts up.
// `small` is a pill's: only the number, sized to fit. A pill gives it `tokens: studio.pillMotion`.
import QtQuick
import QtQuick.Shapes
import "motion.js" as Motion

Item {
    id: ring
    property real done: 0
    property real total: 1
    property real thickness: 12
    property string caption: ""
    property bool small: false
    property var tokens: studio.motion
    readonly property real share: total > 0 ? Math.min(done / total, 1) : 0
    property real shown: 0
    property bool ready: false
    width: 120; height: 120

    function sweep(start, wait) {
        if (!tokens.on) { sweeping.stop(); shown = share; return }
        shown = start
        sweeping.wait = wait
        sweeping.restart()
    }
    onShareChanged: if (ready) sweep(shown, 0)
    onVisibleChanged: if (visible) sweep(0, tokens.sweepDelay); else { sweeping.stop(); shown = share }
    Component.onCompleted: { ready = true; if (Motion.fresh()) sweep(0, tokens.sweepDelay); else shown = share }
    SequentialAnimation {
        id: sweeping
        property int wait: 0
        PauseAnimation { duration: sweeping.wait }
        NumberAnimation { target: ring; property: "shown"; to: ring.share; duration: ring.tokens.sweep; easing.type: Easing.BezierSpline; easing.bezierCurve: ring.tokens.ease }
    }
    CountUp { id: counted; to: ring.done; tokens: ring.tokens }

    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: studio.colors.raised; strokeWidth: ring.thickness; fillColor: "transparent"
            PathAngleArc {
                centerX: ring.width / 2; centerY: ring.height / 2
                radiusX: ring.width / 2 - ring.thickness / 2; radiusY: radiusX
                startAngle: 0; sweepAngle: 360
            }
        }
        ShapePath {
            strokeWidth: ring.thickness; fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            strokeColor: studio.colors.accent
            PathAngleArc {
                centerX: ring.width / 2; centerY: ring.height / 2
                radiusX: ring.width / 2 - ring.thickness / 2; radiusY: radiusX
                startAngle: -90; sweepAngle: Math.max(0.1, 360 * ring.shown)
            }
        }
    }
    Column {
        anchors.centerIn: parent
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: counted.counting ? Math.round(counted.value) : Math.round(ring.done)
            color: studio.colors.text
            font.pixelSize: ring.width * (ring.small ? 0.34 : 0.22); font.weight: Font.Bold
        }
        Text {
            visible: !ring.small
            anchors.horizontalCenter: parent.horizontalCenter
            text: "of " + ring.total
            color: studio.colors.muted
            font.pixelSize: 12
        }
    }
    Text {
        visible: ring.caption !== ""
        anchors { horizontalCenter: parent.horizontalCenter; top: parent.bottom; topMargin: 6 }
        width: ring.width + 40; horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight
        text: ring.caption; color: studio.colors.muted; font.pixelSize: 12
    }
}
