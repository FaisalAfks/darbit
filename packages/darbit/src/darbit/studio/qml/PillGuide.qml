// Where a dragged pill can go (#384), drawn over the screen it's on: the nearest edge lights up, a circle marks each
// of its snap places (filled: where it goes if let go now), and a dashed line shows how far into the middle it has to
// go to float. `origin` is where this item's top-left is, in the place's points. Clicks go through.
import QtQuick
import QtQuick.Shapes

Item {
    id: guide
    required property QtObject place
    property point origin: Qt.point(0, 0)
    readonly property var screen: place.screen
    readonly property string near: place.near
    readonly property bool floating: place.floating
    readonly property color ink: studio.colors.accent
    readonly property real sx: screen.x - origin.x
    readonly property real sy: screen.y - origin.y
    readonly property real line: place.line
    visible: place.dragging
    opacity: visible ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: studio.effects ? 120 : 0 } }

    // the edge it docks to, lit; faint while it would float
    Rectangle {
        readonly property bool across: guide.near === "top" || guide.near === "bottom"
        x: guide.sx + (guide.near === "right" ? guide.screen.width - width : 0)
        y: guide.sy + (guide.near === "bottom" ? guide.screen.height - height : 0)
        width: across ? guide.screen.width : 5
        height: across ? 5 : guide.screen.height
        color: guide.ink
        opacity: guide.floating ? 0.25 : 0.9
        Behavior on opacity { NumberAnimation { duration: studio.effects ? 120 : 0 } }
    }
    Rectangle {  // its glow, fading into the screen
        readonly property bool across: guide.near === "top" || guide.near === "bottom"
        x: guide.sx + (guide.near === "right" ? guide.screen.width - width : 0)
        y: guide.sy + (guide.near === "bottom" ? guide.screen.height - height : 0)
        width: across ? guide.screen.width : 60
        height: across ? 60 : guide.screen.height
        opacity: guide.floating ? 0 : 0.35
        gradient: Gradient {
            orientation: parent.across ? Gradient.Vertical : Gradient.Horizontal
            GradientStop { position: 0; color: guide.near === "top" || guide.near === "left" ? guide.ink : "transparent" }
            GradientStop { position: 1; color: guide.near === "top" || guide.near === "left" ? "transparent" : guide.ink }
        }
    }

    // past this line it floats
    Item {
        x: guide.sx + guide.line; y: guide.sy + guide.line
        width: guide.screen.width - 2 * guide.line; height: guide.screen.height - 2 * guide.line
        visible: width > 0 && height > 0
        Shape {
            anchors.fill: parent
            ShapePath {
                strokeColor: guide.floating ? guide.ink : studio.colors.muted
                strokeWidth: 1.5
                strokeStyle: ShapePath.DashLine; dashPattern: [5, 4]
                fillColor: "transparent"
                PathRectangle { width: guide.screen.width - 2 * guide.line; height: guide.screen.height - 2 * guide.line; radius: 18 }
            }
        }
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            y: -height / 2
            width: lineText.implicitWidth + 20; height: 24; radius: 12
            color: studio.colors.solid; border.color: guide.floating ? guide.ink : studio.colors.line
            Text {
                id: lineText
                anchors.centerIn: parent
                text: guide.floating ? "Let go to float it here" : "Past this line it floats"
                color: guide.floating ? guide.ink : studio.colors.muted
                font.pixelSize: 12; font.weight: Font.DemiBold
            }
        }
    }

    // the snap places on that edge
    Repeater {
        model: guide.place.snaps
        delegate: Rectangle {
            required property var modelData
            readonly property bool on: modelData.on
            x: modelData.x - guide.origin.x - width / 2
            y: modelData.y - guide.origin.y - height / 2
            width: on ? 26 : 18; height: width; radius: width / 2
            color: on ? Qt.rgba(guide.ink.r, guide.ink.g, guide.ink.b, 0.35) : Qt.rgba(guide.ink.r, guide.ink.g, guide.ink.b, 0.08)
            border.color: guide.ink; border.width: on ? 2.5 : 1.5
            opacity: guide.floating ? 0.4 : 1
            Behavior on width { NumberAnimation { duration: studio.effects ? 120 : 0; easing.type: Easing.OutBack } }
            Rectangle {
                visible: parent.on
                anchors.centerIn: parent
                width: 8; height: 8; radius: 4
                color: guide.ink
            }
        }
    }
}
