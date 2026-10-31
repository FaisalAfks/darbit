// One plain line in a menu: an icon and a label.
import QtQuick

Rectangle {
    id: line
    property string text: ""
    property string icon: ""
    signal clicked()
    width: 304; height: 38; radius: 10
    color: area.containsMouse ? studio.colors.raisedHover : "transparent"
    Row {
        x: 12; anchors.verticalCenter: parent.verticalCenter; spacing: 10
        Text { text: line.icon; color: studio.colors.muted; font.pixelSize: 13; width: 16 }
        Text { text: line.text; color: studio.colors.text; font.pixelSize: 14; font.weight: Font.DemiBold }
    }
    MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: line.clicked() }
}
