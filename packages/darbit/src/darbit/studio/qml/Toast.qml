// A short message at the bottom: what just happened, or what went wrong (darbit's service's reasons). It springs into
// place, and fades where it is when it goes. A change that can be taken back (a delete or a rename) comes with Undo.
import QtQuick

Rectangle {
    id: toast
    property string text: ""
    property bool bad: false
    property bool undoable: false
    function show(message, wrong) { text = message; bad = !!wrong; undoable = false; shown = true; hide.interval = Math.max(wrong ? 10000 : 4500, message.length * 70); hide.restart() }
    // with Undo: up long enough to reach it
    function offer(message) { show(message, false); undoable = true; hide.interval = Math.max(8000, message.length * 70); hide.restart() }
    property bool shown: false
    readonly property bool away: !shown && opacity === 0  // gone: it waits below the window, out of sight
    anchors.horizontalCenter: parent.horizontalCenter
    property real drop: 0  // how far below its place it still is, springing in
    y: parent.height - (away ? -10 : height + 28) + drop
    onShownChanged: if (shown && studio.motion.on) { drop = 38; dropping.restart() }
    NumberAnimation { id: dropping; target: toast; property: "drop"; to: 0; duration: studio.motion.toast; easing.type: Easing.BezierSpline; easing.bezierCurve: studio.motion.spring }
    opacity: shown ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: studio.motion.normal; easing.type: Easing.BezierSpline; easing.bezierCurve: studio.motion.ease } }
    readonly property real undoRoom: undoable ? undo.implicitWidth + 10 : 0
    width: Math.min(label.implicitWidth + 62 + undoRoom, parent.width - 80); height: Math.max(46, label.height + 24); radius: 23
    color: studio.colors.solid
    border.color: bad ? studio.colors.danger : studio.colors.line
    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: toast.shown = false }
    Row {
        anchors.centerIn: parent; spacing: 10
        Text { text: toast.bad ? "!" : "✓"; color: toast.bad ? studio.colors.danger : studio.colors.ok; font.pixelSize: 14; font.weight: Font.Bold; y: toast.undoable ? (parent.height - height) / 2 : 0 }
        // a whole reason, on as many lines as it takes: a cut-off error explains nothing
        Text { id: label; text: toast.text; color: studio.colors.text; font.pixelSize: 14; wrapMode: Text.Wrap; maximumLineCount: 4; elide: Text.ElideRight; width: Math.min(implicitWidth, toast.parent.width - 142 - toast.undoRoom); y: toast.undoable ? (parent.height - height) / 2 : 0 }
        PillButton {
            id: undo
            objectName: "toastUndo"
            visible: toast.undoable
            small: true; kind: "quiet"; icon: "↶"; text: "Undo"
            anchors.verticalCenter: parent.verticalCenter
            onClicked: { toast.undoable = false; toast.shown = false; studio.undoLast() }
        }
    }
    Timer { id: hide; interval: 4500; onTriggered: toast.shown = false }
    Connections {
        target: studio
        function onMessageChanged() { if (studio.message !== "") toast.show(studio.message, true) }
        function onOffered(text) { toast.offer(text) }
    }
}
