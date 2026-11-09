// A state's dot (#441). While `pulsing` (a bot running, its window in sight) a ring spreads from it and fades, again
// and again: the only thing that moves on its own, and only then. It steps 30 times a second rather than every frame,
// which is smooth enough for a ring this small and draws the window half as often. A pill gives it
// `tokens: studio.pillMotion`.
import QtQuick

Rectangle {
    id: dot
    property bool pulsing: false
    property var tokens: studio.motion
    property real phase: 0  // 0 to 1, through one pulse
    radius: width / 2

    Rectangle {
        readonly property real eased: 1 - Math.pow(1 - dot.phase, 3)  // fast, then slowing down
        z: -1
        anchors.centerIn: parent
        width: parent.width; height: parent.height; radius: width / 2
        color: dot.color
        visible: ticking.running
        scale: 1 + 1.6 * eased
        opacity: 0.7 * (1 - eased)
    }
    Timer {
        id: ticking
        interval: 33
        repeat: true
        running: dot.pulsing && dot.visible && dot.tokens.on && dot.tokens.pulse > 0
        onRunningChanged: dot.phase = 0
        onTriggered: dot.phase = (dot.phase + interval / dot.tokens.pulse) % 1
    }
}
