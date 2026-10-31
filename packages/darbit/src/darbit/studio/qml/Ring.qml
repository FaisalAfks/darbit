// A progress ring: `done` of `total`, the number in the middle.
import QtQuick
import QtQuick.Shapes

Item {
    id: ring
    property real done: 0
    property real total: 1
    property real thickness: 12
    readonly property real share: total > 0 ? Math.min(done / total, 1) : 0
    width: 120; height: 120

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
            strokeColor: studio.colors.accent; strokeWidth: ring.thickness; fillColor: "transparent"
            capStyle: ShapePath.FlatCap
            PathAngleArc {
                centerX: ring.width / 2; centerY: ring.height / 2
                radiusX: ring.width / 2 - ring.thickness / 2; radiusY: radiusX
                startAngle: -90; sweepAngle: 360 * ring.share
            }
        }
    }
    Column {
        anchors.centerIn: parent
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: ring.done
            color: studio.colors.text
            font.pixelSize: 26; font.weight: Font.Bold
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "of " + ring.total
            color: studio.colors.muted
            font.pixelSize: 12
        }
    }
}
