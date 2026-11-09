// One page, made the first time it's shown and kept from then on: a page never visited costs no memory. Shown, it
// fades in and slides up 10 px while its cards rise one after another; left, it fades out the same way under the next
// one. With blur-through on (darbit settings) it also blurs out and in, the blur only while it moves. Only opacity, a
// move and scale are animated, so changing pages costs no layout work.
import QtQuick
import "motion.js" as Motion

Item {
    id: pageFrame
    property url source
    property bool shown: false
    property bool visited: false
    readonly property var tokens: studio.motion
    readonly property bool blurring: studio.blurThrough && tokens.on
    property Component blurLayer: null  // made the first time a page blurs: the effects module loads only then
    onBlurringChanged: if (blurring && blurLayer === null) blurLayer = Qt.createComponent("BlurLayer.qml")
    visible: shown || leaving.running
    enabled: shown  // the page leaving takes no clicks
    onShownChanged: {
        if (shown) {
            visited = true
            leaving.stop()
            Motion.pageShown()
            enter.restart()
        } else if (tokens.on) {
            enter.stop()
            leaving.restart()
        }
    }
    Component.onCompleted: {
        if (shown) { visited = true; Motion.pageShown() }
        if (blurring) blurLayer = Qt.createComponent("BlurLayer.qml")
    }

    Item {
        id: holder
        width: pageFrame.width; height: pageFrame.height
        opacity: 1
        property real blur: 0
        transform: [
            Translate { id: shift; y: 0 },
            Scale { id: grow; origin.x: holder.width / 2; origin.y: holder.height / 2; xScale: 1; yScale: 1 }
        ]
        // the blur is drawn only while the page moves: a layer left on at rest would change how its text is drawn
        layer.enabled: pageFrame.blurring && holder.blur > 0
        layer.effect: pageFrame.blurLayer
        Loader { anchors.fill: parent; active: pageFrame.visited; source: pageFrame.source }
    }
    ParallelAnimation {
        id: enter
        NumberAnimation { target: holder; property: "opacity"; from: pageFrame.tokens.on ? 0 : 1; to: 1; duration: pageFrame.blurring ? pageFrame.tokens.blur : pageFrame.tokens.pageFade; easing.type: Easing.BezierSpline; easing.bezierCurve: pageFrame.tokens.ease }
        NumberAnimation { target: shift; property: "y"; from: pageFrame.tokens.on && !pageFrame.blurring ? 10 : 0; to: 0; duration: pageFrame.tokens.pageMove; easing.type: Easing.BezierSpline; easing.bezierCurve: pageFrame.tokens.ease }
        NumberAnimation { targets: [grow]; properties: "xScale,yScale"; from: pageFrame.blurring ? 0.96 : 1; to: 1; duration: pageFrame.tokens.blur; easing.type: Easing.BezierSpline; easing.bezierCurve: pageFrame.tokens.ease }
        NumberAnimation { target: holder; property: "blur"; from: pageFrame.blurring ? 0.2 : 0; to: 0; duration: pageFrame.tokens.blur; easing.type: Easing.BezierSpline; easing.bezierCurve: pageFrame.tokens.ease }
    }
    ParallelAnimation {
        id: leaving
        NumberAnimation { target: holder; property: "opacity"; to: 0; duration: pageFrame.blurring ? pageFrame.tokens.blur : pageFrame.tokens.pageFade; easing.type: Easing.BezierSpline; easing.bezierCurve: pageFrame.tokens.ease }
        NumberAnimation { target: shift; property: "y"; to: pageFrame.blurring ? 0 : 10; duration: pageFrame.tokens.pageMove; easing.type: Easing.BezierSpline; easing.bezierCurve: pageFrame.tokens.ease }
        NumberAnimation { targets: [grow]; properties: "xScale,yScale"; to: pageFrame.blurring ? 0.96 : 1; duration: pageFrame.tokens.blur; easing.type: Easing.BezierSpline; easing.bezierCurve: pageFrame.tokens.ease }
        NumberAnimation { target: holder; property: "blur"; to: pageFrame.blurring ? 0.2 : 0; duration: pageFrame.tokens.blur; easing.type: Easing.BezierSpline; easing.bezierCurve: pageFrame.tokens.ease }
    }
}
