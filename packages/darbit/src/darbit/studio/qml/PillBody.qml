// What every pill over the game is made of (#384, #449): the pill itself in its form (a row on the top and bottom
// edges, a labelled column on the sides, a card floating), the panels that open beside it, and dragging it. Grabbed,
// it tilts and shakes a little and sways as it moves, and eases into a new form when it changes edge; let go, its
// window (PillWindow, or Capture's) lands it where it was dropped on its edge, or floats it. `place` (docking.py)
// says where it is and its form.
import QtQuick
import QtQuick.Layouts

Item {
    id: body
    required property QtObject place
    default property alias content: pill.content
    property alias drawer: pill.drawer  // what opens under the row, inside the pill (FloatingPill)
    property alias heading: head.data   // the floating card's first line, after its grip
    property alias card: cardBody.data  // the floating card's detail
    property alias below: under.data    // panels that open beside the pill, away from its edge
    property alias ink: pill.ink
    property int cardWidth: 420
    property int besideWidth: 300       // the panels' width beside a column
    readonly property string form: place.form
    readonly property string side: place.edge
    readonly property bool vertical: form === "column"
    readonly property bool floating: form === "card"
    readonly property bool held: place.dragging && dragArea.moving
    readonly property var tokens: studio.pillMotion
    // a pill without card detail of its own floats as its column, in the card
    property bool cardless: true
    Component.onCompleted: {
        var own = 0
        for (var index = 0; index < cardBody.children.length; index++)
            if (cardBody.children[index] !== pill) own++
        cardless = own === 0
    }
    readonly property Item face: floating ? cardFrame : pill
    // the panels shown by the pill: their size, from the ones that show
    readonly property real belowHeight: {
        var tallest = 0
        for (var index = 0; index < under.children.length; index++) {
            var panel = under.children[index]
            if (panel.visible) tallest = Math.max(tallest, panel.y + panel.height)
        }
        return tallest
    }
    readonly property real belowWidth: {
        var widest = 0
        for (var index = 0; index < under.children.length; index++) {
            var panel = under.children[index]
            if (panel.visible) widest = Math.max(widest, panel.x + panel.width)
        }
        return widest
    }
    readonly property bool hasBelow: belowHeight > 0
    // where the pill (or card) is in the body: panels go on the side away from its edge
    readonly property real faceX: side === "right" && hasBelow ? under.width + 10 : 0
    readonly property real faceY: side === "bottom" && hasBelow ? belowHeight + 10 : 0
    readonly property bool besides: side === "left" || side === "right"
    signal grabbed(real x, real y)  // in global points
    signal moved(real x, real y)
    signal dropped()
    signal pressed()                // a press on the pill, before it's known whether it's a drag

    width: besides ? face.width + (hasBelow ? 10 + under.width : 0) : Math.max(face.width, belowWidth)
    height: besides ? Math.max(face.height, belowHeight) : face.height + (hasBelow ? 10 + belowHeight : 0)

    // the pill's sway as it's dragged: a little tilt, a shake when grabbed, a swing with each move
    property real sway: 0
    property real shake: 0
    Behavior on sway { enabled: studio.effects; SpringAnimation { spring: 5; damping: 0.16; epsilon: 0.05 } }
    Timer { id: settle; interval: 70; onTriggered: body.sway = 0 }
    function nudge(dx) {
        if (!studio.effects) return
        sway = Math.max(-3.5, Math.min(3.5, dx * 0.35))
        settle.restart()
    }
    SequentialAnimation {
        id: grabShake
        NumberAnimation { target: body; property: "shake"; to: 2.5; duration: 45 }
        NumberAnimation { target: body; property: "shake"; to: -2.5; duration: 70 }
        NumberAnimation { target: body; property: "shake"; to: 1.5; duration: 60 }
        NumberAnimation { target: body; property: "shake"; to: -0.8; duration: 55 }
        NumberAnimation { target: body; property: "shake"; to: 0; duration: 50 }
    }
    onHeldChanged: if (held && studio.effects) grabShake.restart()

    // a new form (another edge, or floating) eases in from a little smaller and fainter, instead of jumping
    property real morph: 0
    onFormChanged: if (tokens.on) { morph = 1; easeIn.restart() }
    NumberAnimation { id: easeIn; target: body; property: "morph"; to: 0; duration: body.tokens.slow; easing.type: Easing.BezierSpline; easing.bezierCurve: body.tokens.ease }

    Item {
        id: tilt
        x: body.faceX; y: body.faceY
        width: body.face.width; height: body.face.height
        rotation: body.held && studio.effects ? -1.5 + body.sway + body.shake : 0
        scale: (body.held && studio.effects ? lift : 1) - 0.06 * body.morph
        opacity: 1 - 0.35 * body.morph
        property real lift: 1.03
        Behavior on scale { enabled: body.morph === 0; NumberAnimation { duration: body.tokens.fast; easing.type: Easing.BezierSpline; easing.bezierCurve: body.tokens.ease } }
        Behavior on rotation { enabled: !body.held; NumberAnimation { duration: studio.effects ? 160 : 0; easing.type: Easing.OutBack } }

        // a press on any empty part of the pill: past a few points it's a drag
        MouseArea {
            id: dragArea
            objectName: "pillGrip"
            anchors.fill: parent
            cursorShape: moving ? Qt.ClosedHandCursor : Qt.OpenHandCursor
            property point from: Qt.point(0, 0)
            property point last: Qt.point(0, 0)
            property bool moving: false
            onPressed: { from = body.place.cursor(); last = from; moving = false; body.pressed() }
            onPositionChanged: {
                var at = body.place.cursor()
                if (!moving && Math.abs(at.x - from.x) + Math.abs(at.y - from.y) > 6) {
                    moving = true
                    // where it's held, so it lands where it's let go, held there
                    var on = body.face.mapFromGlobal(at.x, at.y)
                    body.place.holdAt(on.x / Math.max(1, body.face.width), on.y / Math.max(1, body.face.height))
                    body.grabbed(at.x, at.y)
                } else if (moving) {
                    body.nudge(at.x - last.x)
                    body.moved(at.x, at.y)
                }
                last = at
            }
            onReleased: if (moving) { moving = false; body.dropped() }
            onCanceled: if (moving) { moving = false; body.dropped() }
        }

        FloatingPill {
            id: pill
            objectName: "pillFace"
            parent: body.floating && body.cardless ? cardBody : tilt
            visible: !body.floating || body.cardless
            vertical: body.vertical || body.floating
            bare: body.floating
            movable: true
            easeWidth: !body.place.dragging
        }

        // floating: a small window with the fuller detail, and Dock
        Rectangle {
            id: cardFrame
            objectName: "pillCard"
            visible: body.floating
            width: body.cardless ? Math.max(260, pill.width + 32) : body.cardWidth
            height: cardColumn.implicitHeight + 28
            radius: 18
            color: studio.colors.solid
            border.color: pill.ink
            Column {
                id: cardColumn
                x: 16; y: 14
                width: parent.width - 32
                spacing: 12
                RowLayout {
                    width: parent.width
                    spacing: 9
                    Text { text: "⠿"; color: studio.colors.faint; font.pixelSize: 14 }
                    RowLayout { id: head; spacing: 9; Layout.fillWidth: true }
                    PillButton {
                        objectName: "dockButton"
                        kind: "quiet"; small: true; icon: "⇱"; text: "Dock"
                        onClicked: body.place.dock()
                    }
                }
                Column { id: cardBody; width: parent.width; spacing: 12 }
            }
        }
    }

    Item {
        id: under
        x: body.side === "left" ? body.face.width + 10 : 0
        y: body.side === "bottom" || body.besides ? 0 : body.face.height + 10
        width: body.besides ? body.besideWidth : body.face.width
        height: body.belowHeight
    }
}
