// A short message at the bottom: what just happened, or what went wrong (darbit's service's reasons). It springs into
// place, and fades where it is when it goes.
import QtQuick

Rectangle {
    id: toast
    property string text: ""
    property bool bad: false
    function show(message, wrong) { text = message; bad = !!wrong; shown = true; hide.interval = Math.max(wrong ? 10000 : 4500, message.length * 70); hide.restart() }
    property bool shown: false
    readonly property bool away: !shown && opacity === 0  // gone: it waits below the window, out of sight
    anchors.horizontalCenter: parent.horizontalCenter
    property real drop: 0  // how far below its place it still is, springing in
    y: parent.height - (away ? -10 : height + 28) + drop
    onShownChanged: if (shown && studio.motion.on) { drop = 38; dropping.restart() }
    NumberAnimation { id: dropping; target: toast; property: "drop"; to: 0; duration: studio.motion.toast; easing.type: Easing.BezierSpline; easing.bezierCurve: studio.motion.spring }
    opacity: shown ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: studio.motion.normal; easing.type: Easing.BezierSpline; easing.bezierCurve: studio.motion.ease } }
    width: Math.min(label.implicitWidth + 62, parent.width - 80); height: Math.max(46, label.height + 24); radius: 23
    color: studio.colors.solid
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
