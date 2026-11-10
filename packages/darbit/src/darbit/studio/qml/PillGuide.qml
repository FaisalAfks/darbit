// Where a dragged pill can go (#384, #449, #467), drawn over the screen it's on, inside its work area (never under the
// taskbar): the part of the nearest edge by the mouse glows and follows it, a dashed ghost of the pill shows where it
// lands if let go now (on the edge's centre or a corner when it's dropped very close to one), in its size and the
// form it takes on that edge, and a dashed line shows how far into the middle it has to go to float.
// Each glides to its new place with the pill motion tokens rather than jumping. `origin` is where this item's
// top-left is, in the place's points. Clicks go through.
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

    // the part of the edge by the mouse glows, a short bright line with its light fading into the screen, and follows
    // the mouse along it; faint while it would float. Each edge has its own glow, so going from one edge to another
    // fades across instead of jumping. Clipped to the work area: the light never spills over the taskbar
    Item {
        x: guide.sx; y: guide.sy
        width: guide.area.width; height: guide.area.height
        clip: true
        Repeater {
            model: ["top", "bottom", "left", "right"]
            delegate: Item {
                id: edgeGlow
                required property string modelData
                readonly property bool across: modelData === "top" || modelData === "bottom"
                readonly property real reach: 320   // points along the edge the glow covers
                readonly property real depth: 60    // and into the screen
                readonly property var pointer: guide.place.pointer
                readonly property bool shows: guide.near === modelData && pointer.x !== undefined
                // the mouse along this edge, in the work area; a glow shown again starts there, and glides after
                readonly property real wanted: !shows ? at
                    : across ? Math.max(0, Math.min(width, pointer.x - guide.area.x))
                    : Math.max(0, Math.min(height, pointer.y - guide.area.y))
                property real at: 0
                property bool fresh: true
                onWantedChanged: { if (shows && !fresh) at = wanted }
                onShowsChanged: { if (shows) { at = wanted; fresh = false } else fresh = true }
                Behavior on at { enabled: !edgeGlow.fresh; NumberAnimation { duration: guide.tokens.fast; easing.type: Easing.BezierSpline; easing.bezierCurve: guide.tokens.decelerate } }
                readonly property real edgeX: modelData === "right" ? width : modelData === "left" ? 0 : at
                readonly property real edgeY: modelData === "bottom" ? height : modelData === "top" ? 0 : at
                width: parent.width; height: parent.height
                opacity: shows ? (guide.floating ? 0.3 : 1) : 0
                Behavior on opacity { NumberAnimation { duration: guide.tokens.normal; easing.type: Easing.BezierSpline; easing.bezierCurve: guide.tokens.ease } }

                // the light into the screen: a circle's soft gradient, squashed to the glow's depth
                Shape {
                    x: edgeGlow.edgeX - edgeGlow.reach / 2; y: edgeGlow.edgeY - edgeGlow.reach / 2
                    width: edgeGlow.reach; height: edgeGlow.reach
                    transform: Scale {
                        origin.x: edgeGlow.reach / 2; origin.y: edgeGlow.reach / 2
                        xScale: edgeGlow.across ? 1 : 2 * edgeGlow.depth / edgeGlow.reach
                        yScale: edgeGlow.across ? 2 * edgeGlow.depth / edgeGlow.reach : 1
                    }
                    ShapePath {
                        strokeColor: "transparent"
                        fillGradient: RadialGradient {
                            centerX: edgeGlow.reach / 2; centerY: edgeGlow.reach / 2; centerRadius: edgeGlow.reach / 2
                            focalX: centerX; focalY: centerY
                            GradientStop { position: 0; color: Qt.rgba(guide.ink.r, guide.ink.g, guide.ink.b, 0.45) }
                            GradientStop { position: 1; color: "transparent" }
                        }
                        PathRectangle { width: edgeGlow.reach; height: edgeGlow.reach }
                    }
                }
                // the line on the edge, brightest by the mouse
                Rectangle {
                    x: edgeGlow.across ? edgeGlow.at - edgeGlow.reach / 2 : (edgeGlow.modelData === "right" ? edgeGlow.width - 5 : 0)
                    y: edgeGlow.across ? (edgeGlow.modelData === "bottom" ? edgeGlow.height - 5 : 0) : edgeGlow.at - edgeGlow.reach / 2
                    width: edgeGlow.across ? edgeGlow.reach : 5
                    height: edgeGlow.across ? 5 : edgeGlow.reach
                    radius: 2.5
                    gradient: Gradient {
                        orientation: edgeGlow.across ? Gradient.Horizontal : Gradient.Vertical
                        GradientStop { position: 0; color: "transparent" }
                        GradientStop { position: 0.5; color: guide.ink }
                        GradientStop { position: 1; color: "transparent" }
                    }
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

    // where it lands if let go now: a dashed ghost of the pill, its size and form on that edge, following the mouse
    // along the edge and settling onto a corner or the centre it's pulled onto
    Item {
        id: ghostMark
        objectName: "pillGhost"
        readonly property var box: guide.place.ghost
        readonly property bool shows: box.x !== undefined
        property bool fresh: true
        property real gx: 0
        property real gy: 0
        property real gw: 0
        property real gh: 0
        onBoxChanged: {
            if (box.x === undefined) { fresh = true; return }  // read here: `shows` may not have caught up yet
            gx = box.x - guide.origin.x; gy = box.y - guide.origin.y; gw = box.width; gh = box.height
            fresh = false
        }
        x: gx; y: gy; width: gw; height: gh
        opacity: shows ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: guide.tokens.fast } }
        Behavior on gx { enabled: !ghostMark.fresh; NumberAnimation { duration: guide.tokens.fast; easing.type: Easing.BezierSpline; easing.bezierCurve: guide.tokens.decelerate } }
        Behavior on gy { enabled: !ghostMark.fresh; NumberAnimation { duration: guide.tokens.fast; easing.type: Easing.BezierSpline; easing.bezierCurve: guide.tokens.decelerate } }
        Behavior on gw { enabled: !ghostMark.fresh; NumberAnimation { duration: guide.tokens.normal; easing.type: Easing.BezierSpline; easing.bezierCurve: guide.tokens.ease } }
        Behavior on gh { enabled: !ghostMark.fresh; NumberAnimation { duration: guide.tokens.normal; easing.type: Easing.BezierSpline; easing.bezierCurve: guide.tokens.ease } }
        // the pill's own corners: round ends on a plain row, rounder corners on a column (FloatingPill)
        readonly property real corner: box.form === "row" && gh <= 56 ? gh / 2 : 22
        Shape {
            anchors.fill: parent
            ShapePath {
                strokeColor: guide.ink; strokeWidth: 1.5
                strokeStyle: ShapePath.DashLine; dashPattern: [5, 4]
                fillColor: Qt.rgba(guide.ink.r, guide.ink.g, guide.ink.b, 0.10)
                PathRectangle { width: ghostMark.gw; height: ghostMark.gh; radius: ghostMark.corner }
            }
        }
    }
}
