// An on/off switch: the one every switch in the Studio is drawn with. Click or Space flips it.
import QtQuick

Rectangle {
    id: switcher
    property bool checked: false
    signal toggled(bool on)
    implicitWidth: 46; implicitHeight: 26; radius: 13
    activeFocusOnTab: true
    color: checked ? studio.colors.accent : studio.colors.raisedHover
    border.color: activeFocus ? studio.colors.accent : "transparent"
    Behavior on color { ColorAnimation { duration: studio.effects ? 160 : 0 } }
    Rectangle {
        x: switcher.checked ? parent.width - width - 3 : 3; y: 3
        width: 20; height: 20; radius: 10
        color: switcher.checked ? studio.colors.onAccent : studio.colors.text
        Behavior on x { NumberAnimation { duration: studio.effects ? 180 : 0; easing.type: Easing.OutBack } }
    }
    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: switcher.toggled(!switcher.checked) }
    Keys.onSpacePressed: switcher.toggled(!switcher.checked)
}
