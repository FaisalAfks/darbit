// A short message at the bottom: what just happened, or what went wrong (darbit's service's reasons).
import QtQuick

Rectangle {
    id: toast
    property string text: ""
    property bool bad: false
    function show(message, wrong) { text = message; bad = !!wrong; shown = true; hide.interval = Math.max(wrong ? 10000 : 4500, message.length * 70); hide.restart() }
    property bool shown: false
    anchors.horizontalCenter: parent.horizontalCenter
    y: parent.height - (shown ? height + 28 : -10)
    Behavior on y { NumberAnimation { duration: studio.effects ? 260 : 0; easing.type: Easing.OutCubic } }
    opacity: shown ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: studio.effects ? 200 : 0 } }
    width: Math.min(label.implicitWidth + 62, parent.width - 80); height: Math.max(46, label.height + 24); radius: 23
    color: studio.colors.glassStrong
    border.color: bad ? studio.colors.danger : studio.colors.line
    Row {
        anchors.centerIn: parent; spacing: 10
        Text { text: toast.bad ? "!" : "✓"; color: toast.bad ? studio.colors.danger : studio.colors.ok; font.pixelSize: 14; font.weight: Font.Bold }
        // a whole reason, on as many lines as it takes: a cut-off error explains nothing
        Text { id: label; text: toast.text; color: studio.colors.text; font.pixelSize: 14; wrapMode: Text.Wrap; maximumLineCount: 4; elide: Text.ElideRight; width: Math.min(implicitWidth, toast.parent.width - 142) }
    }
    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: toast.shown = false }
    Timer { id: hide; interval: 4500; onTriggered: toast.shown = false }
    Connections {
        target: studio
        function onMessageChanged() { if (studio.message !== "") toast.show(studio.message, true) }
    }
}
