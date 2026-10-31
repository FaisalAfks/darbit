// A small rounded label: a state (done, running), a count, a version. `tone` picks the colour.
import QtQuick

Rectangle {
    id: chip
    property string text: ""
    property string tone: "plain"  // plain, ok, info, warn, danger, accent
    readonly property color ink: tone === "ok" ? studio.colors.ok : tone === "info" ? studio.colors.info
        : tone === "warn" ? studio.colors.warn : tone === "danger" ? studio.colors.danger
        : tone === "accent" ? studio.colors.accent : studio.colors.muted
    height: 24
    width: label.implicitWidth + 20
    radius: 12
    color: Qt.rgba(ink.r, ink.g, ink.b, 0.13)
    border.color: Qt.rgba(ink.r, ink.g, ink.b, 0.45)
    border.width: 1
    Text {
        id: label
        anchors.centerIn: parent
        text: chip.text
        color: chip.tone === "plain" ? studio.colors.text : chip.ink
        font.pixelSize: 12; font.weight: Font.DemiBold
    }
}
