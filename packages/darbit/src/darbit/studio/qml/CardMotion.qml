// How a card or tile moves (#441): it rises into place when its page shows, one card after another, and under the
// mouse it lifts 3 px with a soft shadow and an accent glow round its edge. A card holds one and takes its moves:
//   CardMotion { id: motion; hovered: ...; radius: card.radius }
//   transform: motion.moves; opacity: motion.fade
// Nothing of it is drawn at rest: the shadow and glow are made only while the mouse is on the card. With effects off,
// or the window out of sight, everything is at once in place.
import QtQuick
import "motion.js" as Motion

Item {
    id: moving
    property bool hovered: false
    property bool lifts: true          // false: it rises, but stays put under the mouse
    property real radius: 16
    readonly property var tokens: studio.motion
    readonly property bool tilting: studio.blurThrough  // the setting: cards tilt in instead of rising

    // what the card takes
    property real fade: 1
    property real rise: 0              // how far below its place it is, rising
    property real angle: 0             // tilted back, tilting in
    readonly property real lift: hovered && lifts && tokens.on ? -3 : 0
    property real lifted: lift
    Behavior on lifted { NumberAnimation { duration: moving.tokens.hover; easing.type: Easing.BezierSpline; easing.bezierCurve: moving.tokens.spring } }
    readonly property Translate shift: Translate { y: moving.rise + moving.lifted }
    readonly property Rotation tilt: Rotation {
        origin.x: moving.width / 2; origin.y: 0
        axis { x: 1; y: 0; z: 0 }
        angle: moving.angle
    }
    // a move only: scaling or turning a card's text, even for a moment, leaves Qt's glyphs drawn a little
    // differently afterwards, so the rise has no scale, and the tilt is there only with blur-through on
    readonly property var moves: tilting ? [shift, tilt] : [shift]

    anchors.fill: parent
    z: -1  // under the card

    function rest() {
        rising.stop()
        fade = 1; rise = 0; angle = 0
    }
    function start() {
        if (!tokens.on) { rest(); return }
        var turn = Motion.nextTurn()
        rising.wait = turn * (tilting ? tokens.tiltStagger : tokens.stagger)
        rising.length = tilting ? tokens.tilt : tokens.rise
        fade = 0; rise = tilting ? 20 : 14; angle = tilting ? 10 : 0
        rising.restart()
    }
    onVisibleChanged: if (visible) start(); else rest()
    Component.onCompleted: if (Motion.fresh()) start()
    Connections {
        target: studio
        function onMotionChanged() { if (!studio.motion.on) moving.rest() }
    }

    SequentialAnimation {
        id: rising
        property int wait: 0
        property int length: 500
        PauseAnimation { duration: rising.wait }
        ParallelAnimation {
            NumberAnimation { target: moving; property: "fade"; to: 1; duration: rising.length; easing.type: Easing.BezierSpline; easing.bezierCurve: moving.tokens.ease }
            NumberAnimation { target: moving; property: "rise"; to: 0; duration: rising.length; easing.type: Easing.BezierSpline; easing.bezierCurve: moving.tilting ? moving.tokens.ease : moving.tokens.spring }
            NumberAnimation { target: moving; property: "angle"; to: 0; duration: rising.length; easing.type: Easing.BezierSpline; easing.bezierCurve: moving.tokens.ease }
        }
    }

    // under the mouse: a soft drop shadow and an accent glow, both outside the card only (the glass shows through)
    property real glow: hovered && lifts && tokens.on ? 1 : 0
    Behavior on glow { NumberAnimation { duration: moving.tokens.hover; easing.type: Easing.BezierSpline; easing.bezierCurve: moving.tokens.ease } }
    Loader {
        active: moving.glow > 0
        x: -48; y: -48; width: moving.width + 96; height: moving.height + 96
        opacity: moving.glow
        source: "CardShadow.qml"
    }
}
