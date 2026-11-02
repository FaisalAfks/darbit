// One page in the stack, made the first time it's shown and kept from then on: a page never visited costs no memory.
// It fades and slides a little into place each time it's shown. Only opacity and a move are animated, so changing
// pages costs no layout work.
import QtQuick
import QtQuick.Layouts

Item {
    id: frame
    property url source
    readonly property bool shown: StackLayout.isCurrentItem
    property bool visited: false
    onShownChanged: if (shown) { visited = true; enter.restart() }
    Component.onCompleted: if (shown) visited = true

    Item {
        id: holder
        width: frame.width; height: frame.height
        opacity: 1
        transform: Translate { id: shift; x: 0 }
        Loader { anchors.fill: parent; active: frame.visited; source: frame.source }
    }
    ParallelAnimation {
        id: enter
        NumberAnimation { target: holder; property: "opacity"; from: studio.effects ? 0 : 1; to: 1; duration: studio.effects ? 220 : 0; easing.type: Easing.OutCubic }
        NumberAnimation { target: shift; property: "x"; from: studio.effects ? 18 : 0; to: 0; duration: studio.effects ? 280 : 0; easing.type: Easing.OutCubic }
    }
}
