// A window for a pill floating over the game, top centre: the run pill's and the recorder's. It shows while its
// `hiding` (hiding.py) is open and slides fully out of sight above the screen while that's tucked; a real mouse move to
// the top edge above it brings it back. The bot never sees it in a screen capture. Put the pill's controls inside;
// panels that open under the pill go in `below`.
import QtQuick
import QtQuick.Window

Window {
    id: pillWindow
    required property QtObject hiding     // a HidingPill
    default property alias content: pill.content
    property alias below: under.data
    property alias edge: pill.edge
    signal placed(int x, int y, int width, int height)  // where it is now, in the window's points
    readonly property real ratio: Screen.devicePixelRatio
    readonly property int shownY: Screen.virtualY + 2
    visible: hiding.isOpen
    transientParent: null  // its own window: it shows while the Studio is hidden
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowDoesNotAcceptFocus | Qt.Tool
    color: "transparent"
    width: Math.max(pill.width, under.childrenRect.width) + 24
    height: pill.height + 24 + (under.childrenRect.height > 0 ? under.childrenRect.height + 10 : 0)
    x: Screen.virtualX + (Screen.width - width) / 2
    y: hiding.tucked ? Screen.virtualY - height - 4 : shownY
    Behavior on y { NumberAnimation { duration: studio.effects ? 200 : 0; easing.type: Easing.OutCubic } }
    Component.onCompleted: ghost.keepOutOfCaptures(pillWindow)
    onXChanged: report()
    onYChanged: report()
    onWidthChanged: report()
    onHeightChanged: report()
    onVisibleChanged: report()
    function report() {
        // where the pill shows (not tucked), in screen pixels, for the hiding to watch the mouse around
        hiding.setArea(Math.round(x * ratio), Math.round(Screen.virtualY * ratio), Math.round(width * ratio), Math.round((shownY - Screen.virtualY + height) * ratio))
        placed(x, y, width, height)
    }

    FloatingPill { id: pill; x: 12; y: 12 }
    Item { id: under; x: 12; y: pill.y + pill.height + 10; width: pill.width }
}
