// A filter that's on or off: a pill in its tone, filled while on.
import QtQuick

Rectangle {
    id: toggle
    property string text: ""
    property string tone: "warn"
    property bool on: false
    signal clicked()
    readonly property color ink: tone === "danger" ? studio.colors.danger : tone === "ok" ? studio.colors.ok : studio.colors.warn
    implicitWidth: label.implicitWidth + 28; implicitHeight: 42
    radius: height / 2
    color: on ? Qt.rgba(ink.r, ink.g, ink.b, 0.2) : area.containsMouse ? studio.colors.raised : studio.colors.glass
    border.color: on ? Qt.rgba(ink.r, ink.g, ink.b, 0.6) : studio.colors.line
    Behavior on color { ColorAnimation { duration: studio.effects ? 120 : 0 } }
    Text { id: label; anchors.centerIn: parent; text: toggle.text; color: toggle.ink; font.pixelSize: 14; font.weight: Font.DemiBold }
    MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: toggle.clicked() }
}
