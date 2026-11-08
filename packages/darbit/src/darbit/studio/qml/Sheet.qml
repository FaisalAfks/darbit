// A sheet over the Studio: New bot, Record, Play's checks, Stop and start. One frame for all of them: solid, round,
// centred over a dimmed window, growing in as it opens and fading as it closes. Put its content in `contentItem`.
import QtQuick
import QtQuick.Controls.Basic

Popup {
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: 520
    modal: true
    focus: true
    padding: 26
    Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, 0.45) }
    background: Rectangle { radius: 22; color: studio.colors.solid; border.color: studio.colors.line }
    enter: Transition {
        ParallelAnimation {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: studio.effects ? 180 : 0 }
            NumberAnimation { property: "scale"; from: 0.94; to: 1; duration: studio.effects ? 240 : 0; easing.type: Easing.OutBack; easing.overshoot: 1.2 }
        }
    }
    exit: Transition { NumberAnimation { property: "opacity"; to: 0; duration: studio.effects ? 120 : 0 } }
}
