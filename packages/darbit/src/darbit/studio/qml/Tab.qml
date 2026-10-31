// One page in the page bar: an icon and a name, filled with the accent when it's the page shown.
import QtQuick

Rectangle {
    id: tab
    property string icon: ""
    property string label: ""
    property bool current: false
    signal clicked()
    height: 40
    width: content.implicitWidth + 36
    radius: 20
    color: current ? studio.colors.accent : (area.containsMouse ? studio.colors.raisedHover : "transparent")
    Behavior on color { ColorAnimation { duration: 120 } }

    Row {
        id: content
        anchors.centerIn: parent
        spacing: 9
        Text {
            text: tab.icon
            color: tab.current ? studio.colors.onAccent : studio.colors.muted
            font.pixelSize: 13
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            text: tab.label
            color: tab.current ? studio.colors.onAccent : studio.colors.text
            font.pixelSize: 14; font.weight: Font.DemiBold
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: tab.clicked() }
}
