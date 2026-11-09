// Where a dragged pill can go (#384, #449), drawn over the screen it's on, inside its work area (never under the
// taskbar): the nearest edge lights up, a circle marks its corners and centre (a drop very close to one lands on it),
// the filled circle follows the mouse along the edge to where the pill lands if let go now, and a dashed line shows
// how far into the middle it has to go to float. Each glides to its new place rather than jumping. `origin` is where
// this item's top-left is, in the place's points. Clicks go through.
import QtQuick
import QtQuick.Shapes

Item {
    id: guide
    required property QtObject place
    property point origin: Qt.point(0, 0)
    readonly property var area: place.work
    readonly property string near: place.near
    readonly property bool floating: place.floating
    readonly property color ink: studio.colors.accent
    readonly property var tokens: studio.pillMotion
    readonly property real sx: area.x - origin.x
    readonly property real sy: area.y - origin.y
    readonly property real line: place.line
    visible: place.dragging
    opacity: visible ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: studio.effects ? 120 : 0 } }

    // the edge it docks to, lit, with its glow fading into the screen; faint while it would float. Each edge has its
    // own light, so going from one edge to another fades across instead of jumping
    Repeater {
        model: ["top", "bottom", "left", "right"]
        delegate: Item {
            id: edgeLight
            required property string modelData
            readonly property bool across: modelData === "top" || modelData === "bottom"
            readonly property bool start: modelData === "top" || modelData === "left"
            x: guide.sx + (modelData === "right" ? guide.area.width - width : 0)
            y: guide.sy + (modelData === "bottom" ? guide.area.height - height : 0)
            width: across ? guide.area.width : 60
            height: across ? 60 : guide.area.height
            opacity: guide.near === modelData ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: guide.tokens.normal; easing.type: Easing.BezierSpline; easing.bezierCurve: guide.tokens.ease } }
            Rectangle {
                x: edgeLight.modelData === "right" ? parent.width - width : 0
                y: edgeLight.modelData === "bottom" ? parent.height - height : 0
                width: edgeLight.across ? parent.width : 5
                height: edgeLight.across ? 5 : parent.height
                color: guide.ink
                opacity: guide.floating ? 0.25 : 0.9
                Behavior on opacity { NumberAnimation { duration: studio.effects ? 120 : 0 } }
            }
            Rectangle {
                anchors.fill: parent
                opacity: guide.floating ? 0 : 0.35
                Behavior on opacity { NumberAnimation { duration: guide.tokens.fast } }
                gradient: Gradient {
                    orientation: edgeLight.across ? Gradient.Vertical : Gradient.Horizontal
                    GradientStop { position: 0; color: edgeLight.start ? guide.ink : "transparent" }
                    GradientStop { position: 1; color: edgeLight.start ? "transparent" : guide.ink }
                }
            }
        }
    }

    // past this line it floats
    Item {
        x: guide.sx + guide.line; y: guide.sy + guide.line
        width: guide.area.width - 2 * guide.line; height: guide.area.height - 2 * guide.line
        visible: width > 0 && height > 0
        Shape {
            anchors.fill: parent
            ShapePath {
                strokeColor: guide.floating ? guide.ink : studio.colors.muted
                strokeWidth: 1.5
                strokeStyle: ShapePath.DashLine; dashPattern: [5, 4]
                fillColor: "transparent"
                PathRectangle { width: guide.area.width - 2 * guide.line; height: guide.area.height - 2 * guide.line; radius: 18 }
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

    // the edge's corners and centre: always three, so they glide to another edge instead of being drawn again
    Repeater {
        model: 3
        delegate: Rectangle {
            required property int index
            readonly property var at: guide.place.snaps.length > index ? guide.place.snaps[index] : ({ x: 0, y: 0, on: false })
            readonly property bool on: at.on
            readonly property bool shows: guide.place.snaps.length > index
            // shown again: it starts where it is, and glides only from there
            property bool fresh: true
            property real cx: 0
            property real cy: 0
            onAtChanged: { if (!shows) { fresh = true; return } cx = at.x - guide.origin.x; cy = at.y - guide.origin.y; fresh = false }
            x: cx - width / 2
            y: cy - height / 2
            visible: shows
            width: on ? 26 : 18; height: width; radius: width / 2
            color: on ? Qt.rgba(guide.ink.r, guide.ink.g, guide.ink.b, 0.35) : Qt.rgba(guide.ink.r, guide.ink.g, guide.ink.b, 0.08)
            border.color: guide.ink; border.width: on ? 2.5 : 1.5
            opacity: guide.floating ? 0.4 : 1
            Behavior on cx { enabled: !fresh; NumberAnimation { duration: guide.tokens.normal; easing.type: Easing.BezierSpline; easing.bezierCurve: guide.tokens.ease } }
            Behavior on cy { enabled: !fresh; NumberAnimation { duration: guide.tokens.normal; easing.type: Easing.BezierSpline; easing.bezierCurve: guide.tokens.ease } }
            Behavior on width { NumberAnimation { duration: studio.effects ? 120 : 0; easing.type: Easing.OutBack } }
        }
    }

    // where it lands if let go now: follows the mouse along the edge, and settles onto a corner or the centre it's
    // pulled onto
    Rectangle {
        id: landingMark
        objectName: "pillLanding"
        readonly property var at: guide.place.landing
        readonly property bool shows: at.x !== undefined
        property bool fresh: true
        property real cx: 0
        property real cy: 0
        onAtChanged: { if (!shows) { fresh = true; return } cx = at.x - guide.origin.x; cy = at.y - guide.origin.y; fresh = false }
        x: cx - width / 2; y: cy - height / 2
        width: 26; height: 26; radius: 13
        color: Qt.rgba(guide.ink.r, guide.ink.g, guide.ink.b, 0.35)
        border.color: guide.ink; border.width: 2.5
        opacity: shows ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: guide.tokens.fast } }
        Behavior on cx { enabled: !landingMark.fresh; NumberAnimation { duration: guide.tokens.fast; easing.type: Easing.BezierSpline; easing.bezierCurve: guide.tokens.decelerate } }
        Behavior on cy { enabled: !landingMark.fresh; NumberAnimation { duration: guide.tokens.fast; easing.type: Easing.BezierSpline; easing.bezierCurve: guide.tokens.decelerate } }
        Rectangle {
            anchors.centerIn: parent
            width: 8; height: 8; radius: 4
            color: guide.ink
        }
    }
}
