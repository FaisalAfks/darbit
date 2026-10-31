// A round button with one glyph, and a tooltip.
import QtQuick
import QtQuick.Controls.Basic

Rectangle {
    id: button
    property string glyph: ""
    property string tip: ""
    signal clicked()
    width: 40; height: 40; radius: 20
    opacity: enabled ? 1 : 0.35
    color: area.containsMouse && enabled ? studio.colors.raisedHover : "transparent"
    Text { anchors.centerIn: parent; text: button.glyph; color: studio.colors.text; font.pixelSize: 13 }
    MouseArea {
        id: area; anchors.fill: parent; hoverEnabled: true
        cursorShape: button.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: if (button.enabled) button.clicked()
    }
    ToolTip.visible: area.containsMouse && tip !== ""
    ToolTip.text: tip
    ToolTip.delay: 400
}
