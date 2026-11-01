// The mouse wheel on a Flickable or ListView: each notch glides it a good step (Qt's own wheel moves a few points,
// stiffly). A touchpad's pixels move it directly. Put it inside the view: SmoothWheel { view: list }
import QtQuick

WheelHandler {
    id: wheel
    required property Flickable view
    readonly property real notch: 140  // points per wheel notch
    property real goal: 0
    target: null
    acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
    function clamp(y) { return Math.max(view.originY, Math.min(y, view.originY + view.contentHeight - view.height)) }
    onWheel: function (event) {
        if (view.contentHeight <= view.height) return
        if (event.pixelDelta.y !== 0) {
            wheel.glide.stop()
            view.contentY = clamp(view.contentY - event.pixelDelta.y)
            return
        }
        goal = clamp((wheel.glide.running ? goal : view.contentY) - event.angleDelta.y / 120 * notch)
        wheel.glide.to = goal
        wheel.glide.restart()
    }
    readonly property NumberAnimation glide: NumberAnimation {  // a handler holds no children: a property instead
        target: wheel.view; property: "contentY"
        duration: studio.effects ? 220 : 0; easing.type: Easing.OutCubic
    }
}
