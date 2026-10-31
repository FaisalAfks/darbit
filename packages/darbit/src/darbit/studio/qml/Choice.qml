// A setting that's on or off: its label and help, and a switch that slides.
import QtQuick
import QtQuick.Layouts

Rectangle {
    id: choice
    property string label: ""
    property string help: ""
    property bool checked: false
    signal toggled(bool on)
    height: Math.max(64, words.implicitHeight + 24)
    radius: 14
    color: area.containsMouse ? studio.colors.raisedHover : studio.colors.raised
    Behavior on color { ColorAnimation { duration: studio.effects ? 120 : 0 } }
    RowLayout {
        anchors { fill: parent; leftMargin: 16; rightMargin: 16 }
        spacing: 16
        Column {
            id: words
            Layout.fillWidth: true
            Text { text: choice.label; color: studio.colors.text; font.pixelSize: 15; font.weight: Font.DemiBold }
            Text { width: parent.width; text: choice.help; visible: text !== ""; color: studio.colors.muted; font.pixelSize: 13; wrapMode: Text.Wrap }
        }
        Rectangle {
            width: 46; height: 26; radius: 13
            color: choice.checked ? studio.colors.accent : studio.colors.raisedHover
            Behavior on color { ColorAnimation { duration: studio.effects ? 160 : 0 } }
            Rectangle {
                x: choice.checked ? parent.width - width - 3 : 3; y: 3
                width: 20; height: 20; radius: 10
                color: choice.checked ? studio.colors.onAccent : studio.colors.text
                Behavior on x { NumberAnimation { duration: studio.effects ? 180 : 0; easing.type: Easing.OutBack } }
            }
        }
    }
    MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: choice.toggled(!choice.checked) }
}
