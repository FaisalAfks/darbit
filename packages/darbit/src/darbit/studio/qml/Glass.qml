// A glass card: the panel fill, a hairline edge and an optional small caps title with something on its right.
import QtQuick

Rectangle {
    id: card
    property string title: ""
    property string note: ""
    property alias content: body.data
    property int padding: 22
    radius: 16
    color: studio.colors.glass
    border.color: studio.colors.line
    border.width: 1

    Text {
        id: heading
        visible: card.title !== ""
        x: card.padding; y: card.padding - 2
        text: card.title.toUpperCase()
        color: studio.colors.muted
        font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 1.2
    }
    Text {
        visible: card.note !== ""
        anchors.right: parent.right; anchors.rightMargin: card.padding
        y: card.padding - 3
        text: card.note
        color: studio.colors.muted
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
