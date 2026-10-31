// A progress ring: `done` of `total` in the accent's two colours, the number in the middle and a caption under it.
// It sweeps to its share when the number changes.
import QtQuick
import QtQuick.Shapes

Item {
    id: ring
    property real done: 0
    property real total: 1
    property real thickness: 12
    property string caption: ""
    readonly property real share: total > 0 ? Math.min(done / total, 1) : 0
    property real shown: 0
    width: 120; height: 120
    onShareChanged: shown = share
    Component.onCompleted: shown = share
    Behavior on shown { NumberAnimation { duration: studio.effects ? 700 : 0; easing.type: Easing.OutCubic } }

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
            text: Math.round(ring.done)
            color: studio.colors.text
            font.pixelSize: ring.width * 0.22; font.weight: Font.Bold
        }
        Text {
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
