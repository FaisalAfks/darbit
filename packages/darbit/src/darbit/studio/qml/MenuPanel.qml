// A menu that drops down from a control: one shape and one solid colour for all of them, opening with a short fade.
import QtQuick
import QtQuick.Controls.Basic

Popup {
    padding: 8
    background: Rectangle { radius: 14; color: studio.colors.solid; border.color: studio.colors.line }
    enter: Transition {
        NumberAnimation { property: "opacity"; from: 0; to: 1; duration: studio.effects ? 150 : 0 }
    }
}
