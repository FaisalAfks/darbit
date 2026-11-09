// A glass card: the panel fill, a hairline edge that brightens under the mouse, an optional small caps title with a
// note on its right. It rises into place when its page shows, one card after another; under the mouse it lifts with
// a soft shadow, and a light follows the mouse over it (CardMotion, MouseLight). `lift: false` keeps it still.
import QtQuick

Rectangle {
    id: card
    property string title: ""
    property string note: ""
    property alias content: body.data
    property int padding: 20
    property bool lift: true
    property real dim: 1  // how see-through it is at rest (a block being dragged)
    readonly property bool hovered: hover.hovered
    readonly property color hoverEdge: Qt.tint(studio.colors.line, Qt.rgba(studio.colors.accent.r, studio.colors.accent.g, studio.colors.accent.b, 0.35))
    radius: 18
    color: studio.colors.glass
    border.color: hover.hovered && lift ? hoverEdge : studio.colors.line
    border.width: 1
    Behavior on border.color { ColorAnimation { duration: studio.motion.hover } }

    // the rise and the lift: opacity and a small move only, which the scene graph does without redrawing the card
    opacity: motion.fade * dim
    transform: motion.moves
    CardMotion { id: motion; hovered: hover.hovered; lifts: card.lift; radius: card.radius }
    HoverHandler { id: hover; onPointChanged: if (hovered) light.at = point.position }
    MouseLight { id: light; visible: card.lift; hovered: hover.hovered; radius: card.radius }

    // a faint sheen along the top edge: the glass catching light
    Rectangle {
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 1 }
        height: parent.radius * 2
        radius: parent.radius
        gradient: Gradient {
            GradientStop { position: 0; color: Qt.rgba(1, 1, 1, studio.glass ? 0.045 : 0) }
            GradientStop { position: 1; color: Qt.rgba(1, 1, 1, 0) }
        }
    }
    Text {
        visible: card.title !== ""
        x: card.padding; y: card.padding - 2
        text: card.title.toUpperCase()
        color: studio.colors.muted
        font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 1.3
    }
    Text {
        visible: card.note !== ""
        anchors.right: parent.right; anchors.rightMargin: card.padding
        y: card.padding - 3
        text: card.note
        color: studio.colors.faint
        font.pixelSize: 13; font.weight: Font.DemiBold
    }
    Item {
        id: body
        x: card.padding
        y: card.title !== "" ? card.padding + 26 : card.padding
        width: card.width - card.padding * 2
        height: card.height - y - card.padding
    }
}
