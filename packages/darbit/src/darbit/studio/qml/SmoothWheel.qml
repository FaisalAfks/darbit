// The mouse wheel on a Flickable or ListView: each notch glides it a good step (Qt's own wheel moves a few points,
// stiffly). A touchpad's pixels move it directly. Put it inside the view: SmoothWheel { view: list }. `sideways`
// moves a horizontal view along with the wheel.
import QtQuick

WheelHandler {
    id: wheel
    required property Flickable view
    property bool sideways: false
    readonly property real notch: 140  // points per wheel notch
    property real goal: 0
    readonly property real at: sideways ? view.contentX : view.contentY
    readonly property real low: sideways ? view.originX : view.originY
    readonly property real room: sideways ? view.contentWidth - view.width : view.contentHeight - view.height
    target: null
    acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
    function clamp(value) { return Math.max(low, Math.min(value, low + room)) }
    function put(value) { if (sideways) view.contentX = value; else view.contentY = value }
    onWheel: function (event) {
        if (room <= 0) return
        var pixels = event.pixelDelta.y !== 0 ? event.pixelDelta.y : event.pixelDelta.x
        if (pixels !== 0) {
            wheel.glide.stop()
            put(clamp(at - pixels))
            return
        }
        var steps = (event.angleDelta.y !== 0 ? event.angleDelta.y : event.angleDelta.x) / 120
        goal = clamp((wheel.glide.running ? goal : at) - steps * notch)
        wheel.glide.to = goal
        wheel.glide.restart()
    }
    readonly property NumberAnimation glide: NumberAnimation {  // a handler holds no children: a property instead
        target: wheel.view; property: wheel.sideways ? "contentX" : "contentY"
        duration: studio.effects ? 220 : 0; easing.type: Easing.OutCubic
    }
}
