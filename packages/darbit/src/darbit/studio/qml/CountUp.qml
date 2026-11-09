// A number that counts up (#441): from 0 when its page shows, and from the old value to a new one. Its text shows
// `value` while `counting`, and the number as it always is once it has arrived:
//   CountUp { id: count; to: 134 }
//   Text { text: count.counting ? Math.round(count.value) : 134 }
import QtQuick
import "motion.js" as Motion

Item {
    id: count
    property real to: 0
    property var tokens: studio.motion  // a pill's: studio.pillMotion
    property real value: 0
    readonly property bool counting: going.running
    property bool ready: false

    function from(start) {
        if (!tokens.on || isNaN(to) || isNaN(start) || start === to) { going.stop(); value = to; return }
        value = start
        going.from = start
        going.restart()
    }
    onToChanged: if (ready) from(value)
    onVisibleChanged: if (visible) from(0); else { going.stop(); value = to }
    Component.onCompleted: { ready = true; if (Motion.fresh()) from(0); else value = to }

    NumberAnimation {
        id: going
        target: count; property: "value"; to: count.to
        duration: count.tokens.count
        easing.type: Easing.BezierSpline; easing.bezierCurve: count.tokens.ease
    }
}
