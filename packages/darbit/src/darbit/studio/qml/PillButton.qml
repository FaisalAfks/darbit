// A button: `kind` primary (the accent, for the one main action), plain, quiet (no fill until hovered) or danger.
import QtQuick

Rectangle {
    id: button
    property string text: ""
    property string icon: ""
    property string kind: "plain"
    property bool small: false
    signal clicked()
    implicitWidth: row.implicitWidth + (small ? 22 : 30)
    implicitHeight: small ? 32 : 40
    radius: height / 2
    opacity: enabled ? 1 : 0.4
    scale: hover.pressed ? 0.96 : 1
    Behavior on scale { NumberAnimation { duration: studio.effects ? 90 : 0 } }
    color: kind === "primary" ? studio.colors.accent
        : kind === "danger" ? Qt.rgba(studio.colors.danger.r, studio.colors.danger.g, studio.colors.danger.b, hover.containsMouse ? 0.24 : 0.14)
        : kind === "quiet" ? (hover.containsMouse ? studio.colors.raised : "transparent")
        : hover.containsMouse ? studio.colors.raisedHover : studio.colors.raised
    Behavior on color { ColorAnimation { duration: studio.effects ? 120 : 0 } }
    gradient: kind === "primary" ? accentFill : null
    Gradient {
        id: accentFill
        orientation: Gradient.Horizontal
        GradientStop { position: 0; color: hover.containsMouse ? Qt.lighter(studio.colors.accent, 1.08) : studio.colors.accent }
        GradientStop { position: 1; color: Qt.tint(studio.colors.accent, Qt.rgba(0.65, 0.55, 0.98, 0.45)) }
    }
    Row {
        id: row
        anchors.centerIn: parent
        spacing: 7
        Text {
            visible: button.icon !== ""
            text: button.icon
            color: label.color; font.pixelSize: button.small ? 12 : 13
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            id: label
            visible: button.text !== ""
            text: button.text
            color: button.kind === "primary" ? studio.colors.onAccent : button.kind === "danger" ? studio.colors.danger : studio.colors.text
            font.pixelSize: button.small ? 12.5 : 13.5; font.weight: Font.DemiBold
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    MouseArea {
        id: hover
        anchors.fill: parent; hoverEnabled: true
        cursorShape: button.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: if (button.enabled) button.clicked()
    }
}
