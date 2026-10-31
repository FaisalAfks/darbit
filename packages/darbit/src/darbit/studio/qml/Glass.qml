// A glass card: the panel fill, a hairline edge that brightens under the mouse, an optional small caps title with a
// note on its right, and a short rise into place when it first shows (`delay` staggers a page's cards).
import QtQuick

Rectangle {
    id: card
    property string title: ""
    property string note: ""
    property alias content: body.data
    property int padding: 20
    property int delay: 0
    property bool lift: true
    radius: 18
    color: studio.colors.glass
    border.color: hover.hovered && lift ? Qt.tint(studio.colors.line, Qt.rgba(0.35, 0.78, 0.98, 0.25)) : studio.colors.line
    border.width: 1
    Behavior on border.color { ColorAnimation { duration: studio.effects ? 160 : 0 } }

    // the rise: opacity and a small move only, which the scene graph does without redrawing the card's contents
    opacity: 0
    transform: Translate { id: shift; y: studio.effects ? 14 : 0 }
    Component.onCompleted: rise.start()
    SequentialAnimation {
        id: rise
        PauseAnimation { duration: studio.effects ? card.delay : 0 }
        ParallelAnimation {
            NumberAnimation { target: card; property: "opacity"; to: 1; duration: studio.effects ? 260 : 0; easing.type: Easing.OutCubic }
            NumberAnimation { target: shift; property: "y"; to: 0; duration: studio.effects ? 320 : 0; easing.type: Easing.OutCubic }
        }
    }
    HoverHandler { id: hover }

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
