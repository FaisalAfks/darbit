// A window for a pill floating over the game: the run pill's, the recorder's and Highlight's. It sits on a screen
// edge at a snap place, or floats (`place`, docking.py); it can be dragged to another edge, or firmly into the middle
// to float as a small card with Dock. Docked, it shows while its `hiding` (hiding.py) is open and slides out of sight
// past its edge while that's tucked; a real mouse move to that edge beside it brings it back. While it's dragged a
// guide over the screen lights the edge it goes to and its snap places. The bot never sees either in a screen
// capture. Put the pill's controls inside; its card's detail in `heading` and `card`; panels that open by the pill in
// `below`.
import QtQuick
import QtQuick.Window

Window {
    id: pillWindow
    required property QtObject hiding  // a HidingPill
    required property QtObject place   // a PillPlace
    default property alias content: body.content
    property alias heading: body.heading
    property alias card: body.card
    property alias below: body.below
    property alias ink: body.ink
    property alias cardWidth: body.cardWidth
    readonly property string form: body.form
    readonly property string side: place.edge
    readonly property var screenBox: place.screen
    readonly property int margin: 28  // room for the pill's tilt while it's dragged
    signal placed(int x, int y, int width, int height)  // where it is now, in the window's points
    visible: hiding.isOpen
    transientParent: null  // its own window: it shows while the Studio is hidden
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowDoesNotAcceptFocus | Qt.Tool
    color: "transparent"
    width: body.width + 2 * margin
    height: body.height + 2 * margin

    // while it's dragged, the window follows the mouse, holding the pill where it was grabbed
    property point held: Qt.point(0, 0)
    property real grabX: 0.5
    property real grabY: 0.5
    readonly property bool dragging: place.dragging
    readonly property bool tuckedAway: hiding.tucked && !place.floating && !dragging
    // where the window sits when it shows, from the pill's snap place (or floating spot)
    readonly property var spot: { place.screen; place.edge; return place.spotFor(body.face.width, body.face.height) }
    readonly property real shownX: spot.x - margin - body.faceX
    readonly property real shownY: spot.y - margin - body.faceY

    x: dragging ? held.x - margin - body.faceX - grabX * body.face.width
        : tuckedAway && side === "left" ? screenBox.x - width - 4
        : tuckedAway && side === "right" ? screenBox.x + screenBox.width + 4
        : shownX
    y: dragging ? held.y - margin - body.faceY - grabY * body.face.height
        : tuckedAway && side === "top" ? screenBox.y - height - 4
        : tuckedAway && side === "bottom" ? screenBox.y + screenBox.height + 4
        : shownY
    Behavior on x { enabled: !pillWindow.dragging; NumberAnimation { duration: studio.effects ? 200 : 0; easing.type: Easing.OutCubic } }
    Behavior on y { enabled: !pillWindow.dragging; NumberAnimation { duration: studio.effects ? 200 : 0; easing.type: Easing.OutCubic } }

    Component.onCompleted: { ghost.keepOutOfCaptures(pillWindow); hiding.hold(place.floating) }
    onXChanged: report()
    onYChanged: report()
    onWidthChanged: report()
    onHeightChanged: report()
    onVisibleChanged: report()
    onFormChanged: place.setSize(form, body.face.width, body.face.height)
    function report() {
        // where the pill shows (not tucked), stretched to its edge, for the hiding to watch the mouse around
        var left = shownX, top = shownY, right = shownX + width, bottom = shownY + height
        var screen = screenBox
        if (side === "top") top = screen.y
        else if (side === "bottom") bottom = screen.y + screen.height
        else if (side === "left") left = screen.x
        else if (side === "right") right = screen.x + screen.width
        hiding.setShown(left, top, right - left, bottom - top, side)
        placed(x, y, width, height)
    }
    Connections {
        target: pillWindow.place
        function onChanged() { pillWindow.hiding.hold(pillWindow.place.floating || pillWindow.place.dragging); pillWindow.report() }
    }

    PillBody {
        id: body
        x: pillWindow.margin; y: pillWindow.margin
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
        onWidthChanged: if (!pillWindow.dragging) pillWindow.place.setSize(body.form, body.face.width, body.face.height)
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
