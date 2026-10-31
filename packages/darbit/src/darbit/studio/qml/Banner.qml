// A line that needs you: a problem or a step to take, its detail, and the one thing to do about it.
import QtQuick
import QtQuick.Layouts

Rectangle {
    id: banner
    property string tone: "warn"  // warn, danger, info
    property string icon: "!"
    property string title: ""
    property string detail: ""
    property string action: ""
    signal acted()
    readonly property color ink: tone === "danger" ? studio.colors.danger : tone === "info" ? studio.colors.info : studio.colors.warn
    implicitHeight: 72
    radius: 16
    color: Qt.rgba(ink.r, ink.g, ink.b, 0.09)
    border.color: Qt.rgba(ink.r, ink.g, ink.b, 0.38)
    RowLayout {
        anchors { fill: parent; leftMargin: 18; rightMargin: 16 }
        spacing: 14
        Rectangle {
            width: 34; height: 34; radius: 17
            color: Qt.rgba(banner.ink.r, banner.ink.g, banner.ink.b, 0.2)
            Text { anchors.centerIn: parent; text: banner.icon; color: banner.ink; font.pixelSize: 15; font.weight: Font.Bold }
        }
        Column {
            Layout.fillWidth: true
            Text { width: parent.width; text: banner.title; color: studio.colors.text; font.pixelSize: 15; font.weight: Font.DemiBold; elide: Text.ElideRight }
            Text { width: parent.width; text: banner.detail; visible: text !== ""; color: studio.colors.muted; font.pixelSize: 13; elide: Text.ElideRight }
        }
        PillButton { visible: banner.action !== ""; text: banner.action; kind: "primary"; small: true; onClicked: banner.acted() }
    }
}
