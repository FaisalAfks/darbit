// One line in a menu: an icon and a label, and under it a quieter detail when there's one. `hovered` lets a menu show
// what a line would do before it's clicked.
import QtQuick

Rectangle {
    id: line
    property string text: ""
    property string icon: ""
    property string detail: ""
    property color iconColor: studio.colors.muted
    readonly property bool hovered: area.containsMouse
    signal clicked()
    width: 304; height: detail === "" ? 38 : 50; radius: 10
    color: area.containsMouse ? studio.colors.raisedHover : "transparent"
    Row {
        x: 12; anchors.verticalCenter: parent.verticalCenter; spacing: 10
        Text { text: line.icon; color: line.iconColor; font.pixelSize: 13; font.family: studio.symbols; width: 16; anchors.verticalCenter: parent.verticalCenter }
        Column {
            anchors.verticalCenter: parent.verticalCenter
            Text { width: line.width - 50; text: line.text; color: studio.colors.text; font.pixelSize: 14; font.weight: Font.DemiBold; elide: Text.ElideRight }
            Text { visible: line.detail !== ""; width: line.width - 50; text: line.detail; color: studio.colors.muted; font.pixelSize: 12; elide: Text.ElideRight }
        }
    }
    MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: line.clicked() }
}
