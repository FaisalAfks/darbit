// A window for a pill floating over the game: the run pill's, the recorder's and Scout's. It sits on a screen
// edge where it was dropped, or floats (`place`, docking.py), always inside the screen's work area (never under the
// taskbar); it can be dragged to another edge, or firmly into the middle to float as a small card with Dock. Docked,
// it shows while its `hiding` (hiding.py) is open and slides out of sight past its screen edge while that's tucked;
// a real mouse move to that edge beside it brings it back. While it's dragged a guide over the screen lights the edge
// it goes to, its corners and centre, and where it lands. The bot never sees either in a screen capture. Put the
// pill's controls inside; its card's detail in `heading` and `card`; panels that open by the pill in `below`.
//
// While it's dragged, and while it lands, the window keeps one size around the pill (`room`), so a change of form
// only redraws inside it and the window only moves; it takes the pill's own size again once the pill has landed.
import QtQuick
import QtQuick.Window

Window {
    id: pillWindow
    required property QtObject hiding  // a HidingPill
    required property QtObject place   // a PillPlace
    default property alias content: body.content
    property alias heading: body.heading
    property alias card: body.card
    property alias drawer: body.drawer  // what opens under the row, inside the pill
    property alias below: body.below
    property alias ink: body.ink
    property alias cardWidth: body.cardWidth
    readonly property string form: body.form
    readonly property string side: place.edge
    readonly property var screenBox: place.screen  // all of the screen: a tucked pill goes past its edge
    readonly property var tokens: studio.pillMotion
    readonly property int margin: 12  // room around the pill at rest
    readonly property int tiltRoom: 28  // and while it's dragged or lands: room for its tilt
    // where it is now, in the window's points; while it's dragged, the whole screen it's on (the recorder leaves the
    // drag's clicks out), and once more where it lands
    signal placed(int x, int y, int width, int height)
    visible: hiding.isOpen
    transientParent: null  // its own window: it shows while the Studio is hidden
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowDoesNotAcceptFocus | Qt.Tool
    color: "transparent"

    // while it's dragged, the pill follows the mouse, held where it was grabbed
    property point held: Qt.point(0, 0)
    property real grabX: 0.5
    property real grabY: 0.5
    readonly property bool dragging: place.dragging
    property bool holding: false  // follows `dragging`, set here so the landing takes over in the same step
    property bool landing: false
    readonly property bool roomy: holding || landing
    property size room: Qt.size(0, 0)
    readonly property bool tuckedAway: hiding.tucked && !place.floating && !holding
    // where the pill sits when it shows, from its place on its edge (or floating spot)
    readonly property var spot: { place.screen; place.work; place.edge; return place.spotFor(body.face.width, body.face.height) }
    readonly property real restWidth: body.width + 2 * margin
    readonly property real restHeight: body.height + 2 * margin
    readonly property real shownX: spot.x - margin - body.faceX
    readonly property real shownY: spot.y - margin - body.faceY

    // the pill's top-left corner on the screen: held, landing, tucked away past the screen's edge, or shown
    readonly property real restFaceX: tuckedAway && side === "left" ? screenBox.x - restWidth - 4 + margin + body.faceX
        : tuckedAway && side === "right" ? screenBox.x + screenBox.width + 4 + margin + body.faceX
        : spot.x
    readonly property real restFaceY: tuckedAway && side === "top" ? screenBox.y - restHeight - 4 + margin + body.faceY
        : tuckedAway && side === "bottom" ? screenBox.y + screenBox.height + 4 + margin + body.faceY
        : spot.y
    // landing: from where it was let go to where it sits, which may still change as the pill takes its new size
    property real fromX: 0
    property real fromY: 0
    property real landed: 0  // 0 where it was let go, 1 where it sits; past 1 and back with the spring
    readonly property real faceX: holding ? held.x - grabX * body.face.width
        : landing ? fromX + (restFaceX - fromX) * landed : restFaceX
    readonly property real faceY: holding ? held.y - grabY * body.face.height
        : landing ? fromY + (restFaceY - fromY) * landed : restFaceY
    property real shownFaceX: faceX
    property real shownFaceY: faceY
    Behavior on shownFaceX { enabled: !pillWindow.roomy; NumberAnimation { duration: pillWindow.tokens.normal; easing.type: Easing.BezierSpline; easing.bezierCurve: pillWindow.tokens.ease } }
    Behavior on shownFaceY { enabled: !pillWindow.roomy; NumberAnimation { duration: pillWindow.tokens.normal; easing.type: Easing.BezierSpline; easing.bezierCurve: pillWindow.tokens.ease } }

    // the body in the window: held with the grab point in the middle of the room, or by the margin at rest
    readonly property real bodyX: roomy ? room.width / 2 - grabX * body.face.width - body.faceX : margin
    readonly property real bodyY: roomy ? room.height / 2 - grabY * body.face.height - body.faceY : margin
    readonly property real wantX: shownFaceX - body.faceX - bodyX
    readonly property real wantY: shownFaceY - body.faceY - bodyY
    readonly property real wantWidth: roomy ? room.width : restWidth
    readonly property real wantHeight: roomy ? room.height : restHeight
    onWantXChanged: settle()
    onWantYChanged: settle()
    onWantWidthChanged: settle()
    onWantHeightChanged: settle()
    // the window's place and size in one go: set one by one, it could show a frame at the new place with the old size
    function settle() {
        setGeometry(Math.round(wantX), Math.round(wantY), Math.max(1, Math.round(wantWidth)), Math.max(1, Math.round(wantHeight)))
    }

    function roomFor() {
        // big enough for the pill in any form held anywhere, with its panels and its tilt
        var widest = Math.max(body.width, pillWindow.cardWidth)
        var tallest = body.height
        var sizes = [place.sizeOf("row"), place.sizeOf("column"), place.sizeOf("card")]
        for (var index = 0; index < sizes.length; index++) {
            widest = Math.max(widest, sizes[index].width + body.belowWidth + 10)
            tallest = Math.max(tallest, sizes[index].height + body.belowHeight + 10)
        }
        return Qt.size(2 * (widest + tiltRoom), 2 * (tallest + tiltRoom))
    }
    onDraggingChanged: {
        if (dragging) {
            landing = false
            landingMotion.stop()
            room = roomFor()
            holding = true
            placed(screenBox.x, screenBox.y, screenBox.width, screenBox.height)
            return
        }
        // let go: the pill glides from where it was held to where it lands, and settles there
        fromX = faceX
        fromY = faceY
        landed = 0
        landing = true
        holding = false
        landingMotion.restart()
    }
    NumberAnimation {
        id: landingMotion
        target: pillWindow; property: "landed"; from: 0; to: 1
        duration: pillWindow.tokens.slow; easing.type: Easing.BezierSpline; easing.bezierCurve: pillWindow.tokens.spring
        onFinished: { pillWindow.landing = false; pillWindow.report() }
    }

    Component.onCompleted: { ghost.keepOutOfCaptures(pillWindow); hiding.hold(place.floating); settle() }
    onXChanged: report()
    onYChanged: report()
    onWidthChanged: report()
    onHeightChanged: report()
    onVisibleChanged: { if (visible) settle(); report() }
    onFormChanged: place.setSize(form, body.face.width, body.face.height)
    function report() {
        // where the pill shows (not tucked), stretched to its screen edge, for the hiding to watch the mouse around
        var left = shownX, top = shownY, right = shownX + restWidth, bottom = shownY + restHeight
        var screen = screenBox
        if (side === "top") top = screen.y
        else if (side === "bottom") bottom = screen.y + screen.height
        else if (side === "left") left = screen.x
        else if (side === "right") right = screen.x + screen.width
        hiding.setShown(left, top, right - left, bottom - top, side)
        if (!roomy) placed(x, y, width, height)
    }
    onScreenBoxChanged: if (dragging) placed(screenBox.x, screenBox.y, screenBox.width, screenBox.height)
    Connections {
        target: pillWindow.place
        function onChanged() { pillWindow.hiding.hold(pillWindow.place.floating || pillWindow.place.dragging); pillWindow.report() }
    }

    PillBody {
        id: body
        x: pillWindow.bodyX; y: pillWindow.bodyY
        place: pillWindow.place
        onGrabbed: function (gx, gy) {
            var at = body.face.mapFromGlobal(gx, gy)
            pillWindow.grabX = Math.max(0, Math.min(1, at.x / body.face.width))
            pillWindow.grabY = Math.max(0, Math.min(1, at.y / body.face.height))
            pillWindow.held = Qt.point(gx, gy)
            pillWindow.place.setSize(body.form, body.face.width, body.face.height)
            pillWindow.place.begin(gx, gy)
            pillWindow.hiding.hold(true)
        }
        onMoved: function (gx, gy) { pillWindow.held = Qt.point(gx, gy); pillWindow.place.move(gx, gy) }
        onDropped: pillWindow.place.end()
        onWidthChanged: pillWindow.place.setSize(body.form, body.face.width, body.face.height)
        onHeightChanged: pillWindow.place.setSize(body.form, body.face.width, body.face.height)
    }

    // while it's dragged: the guide over the screen it's on
    Window {
        id: guideWindow
        visible: pillWindow.dragging && pillWindow.visible
        transientParent: null
        flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowDoesNotAcceptFocus | Qt.WindowTransparentForInput | Qt.Tool
        color: "transparent"
        title: pillWindow.title + " guide"
        x: pillWindow.screenBox.x; y: pillWindow.screenBox.y
        width: pillWindow.screenBox.width; height: pillWindow.screenBox.height
        Component.onCompleted: ghost.keepOutOfCaptures(guideWindow)
        onVisibleChanged: if (visible) pillWindow.raise()
        PillGuide {
            anchors.fill: parent
            place: pillWindow.place
            origin: Qt.point(pillWindow.screenBox.x, pillWindow.screenBox.y)
        }
    }
}
