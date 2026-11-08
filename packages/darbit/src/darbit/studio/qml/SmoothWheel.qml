// The mouse wheel on a Flickable or ListView: each notch glides it a good step (Qt's own wheel moves a few points,
// stiffly). A touchpad's pixels move it directly. Put it inside the view: SmoothWheel { view: list }; `sideways` for a
// view that scrolls left and right (the wheel's turn moves it along).
import QtQuick

WheelHandler {
    id: wheel
    required property Flickable view
    property bool sideways: false
    readonly property real notch: 140  // points per wheel notch
    readonly property string along: sideways ? "contentX" : "contentY"
    property real goal: 0
    target: null
    acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
    function clamp(at) {
        if (sideways) return Math.max(view.originX, Math.min(at, view.originX + view.contentWidth - view.width))
        return Math.max(view.originY, Math.min(at, view.originY + view.contentHeight - view.height))
    }
    onWheel: function (event) {
        if (sideways ? view.contentWidth <= view.width : view.contentHeight <= view.height) return
        var pixels = sideways ? (event.pixelDelta.x || event.pixelDelta.y) : event.pixelDelta.y
        if (pixels !== 0) {
            wheel.glide.stop()
            view[along] = clamp(view[along] - pixels)
            return
        }
        var turn = sideways ? (event.angleDelta.y || event.angleDelta.x) : event.angleDelta.y
        goal = clamp((wheel.glide.running ? goal : view[along]) - turn / 120 * notch)
        wheel.glide.to = goal
        wheel.glide.restart()
    }
    readonly property NumberAnimation glide: NumberAnimation {  // a handler holds no children: a property instead
        target: wheel.view; property: wheel.along
        duration: studio.effects ? 220 : 0; easing.type: Easing.OutCubic
    }
}
