// One page in the stack: it fades and slides a little into place each time it's shown. Only opacity and a move are
// animated, so changing pages costs no layout work.
import QtQuick
import QtQuick.Layouts

Item {
    id: frame
    default property alias page: holder.data
    readonly property bool shown: StackLayout.isCurrentItem
    onShownChanged: if (shown) enter.restart()

    Item {
        id: holder
        width: frame.width; height: frame.height
        opacity: 1
        transform: Translate { id: shift; x: 0 }
    }
    ParallelAnimation {
        id: enter
        NumberAnimation { target: holder; property: "opacity"; from: studio.effects ? 0 : 1; to: 1; duration: studio.effects ? 220 : 0; easing.type: Easing.OutCubic }
        NumberAnimation { target: shift; property: "x"; from: studio.effects ? 18 : 0; to: 0; duration: studio.effects ? 280 : 0; easing.type: Easing.OutCubic }
    }
}
