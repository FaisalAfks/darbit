// A short message at the bottom: what just happened, or what went wrong (darbit's service's reasons).
import QtQuick

Rectangle {
    id: toast
    property string text: ""
    property bool bad: false
    function show(message, wrong) { text = message; bad = !!wrong; shown = true; hide.restart() }
    property bool shown: false
    anchors.horizontalCenter: parent.horizontalCenter
    y: parent.height - (shown ? height + 28 : -10)
    Behavior on y { NumberAnimation { duration: studio.effects ? 260 : 0; easing.type: Easing.OutCubic } }
    opacity: shown ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: studio.effects ? 200 : 0 } }
    width: Math.min(label.implicitWidth + 48, parent.width - 80); height: 46; radius: 23
    color: studio.colors.glassStrong
    border.color: bad ? studio.colors.danger : studio.colors.line
    Row {
        anchors.centerIn: parent; spacing: 10
        Text { text: toast.bad ? "!" : "✓"; color: toast.bad ? studio.colors.danger : studio.colors.ok; font.pixelSize: 14; font.weight: Font.Bold }
        Text { id: label; text: toast.text; color: studio.colors.text; font.pixelSize: 14; elide: Text.ElideRight; width: Math.min(implicitWidth, toast.parent.width - 140) }
    }
    Timer { id: hide; interval: 4500; onTriggered: toast.shown = false }
    Connections {
        target: studio
        function onMessageChanged() { if (studio.message !== "") toast.show(studio.message, true) }
    }
}
