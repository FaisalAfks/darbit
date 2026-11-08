// One line in a menu: an icon and a label, and under it a quieter detail when there's one; `keys` on the right when
// it has a shortcut, `ink` for a line that ends something (Quit). `hovered` lets a menu show what a line would do
// before it's clicked.
import QtQuick

Rectangle {
    id: line
    property string text: ""
    property string icon: ""
    property string detail: ""
    property color iconColor: studio.colors.muted
    property color ink: studio.colors.text
    property string keys: ""
    readonly property bool hovered: area.containsMouse
    signal clicked()
    width: 304; height: detail === "" ? 38 : 50; radius: 10
    color: area.containsMouse ? studio.colors.raisedHover : "transparent"
    Row {
        x: 12; anchors.verticalCenter: parent.verticalCenter; spacing: 10
        Text { text: line.icon; color: line.iconColor; font.pixelSize: 13; font.family: studio.symbols; width: 16; anchors.verticalCenter: parent.verticalCenter }
        Column {
            anchors.verticalCenter: parent.verticalCenter
            Text { width: line.width - 50 - (keyCap.visible ? keyCap.width + 10 : 0); text: line.text; color: line.ink; font.pixelSize: 14; font.weight: Font.DemiBold; elide: Text.ElideRight }
            Text { visible: line.detail !== ""; width: line.width - 50; text: line.detail; color: studio.colors.muted; font.pixelSize: 12; elide: Text.ElideRight }
        }
    }
    Rectangle {
        id: keyCap
        visible: line.keys !== ""
        anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
        width: keyText.implicitWidth + 12; height: 20; radius: 5
        color: studio.colors.raised; border.color: studio.colors.line
        Text { id: keyText; anchors.centerIn: parent; text: line.keys; color: studio.colors.muted; font.pixelSize: 11; font.family: "monospace" }
    }
    MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: line.clicked() }
}
