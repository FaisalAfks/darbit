// One action: its name, how many steps and sections it has, which actions call it, and Play.
import QtQuick
import QtQuick.Controls.Basic

Rectangle {
    id: card
    property var action: ({})
    property bool chosen: false
    property bool dimmed: false
    signal clicked()
    signal play()
    height: 206
    radius: 16
    color: chosen ? Qt.rgba(studio.colors.accent.r, studio.colors.accent.g, studio.colors.accent.b, 0.1) : studio.colors.glass
    border.color: chosen ? studio.colors.accent : area.containsMouse ? Qt.tint(studio.colors.line, Qt.rgba(studio.colors.accent.r, studio.colors.accent.g, studio.colors.accent.b, 0.35)) : studio.colors.line
    border.width: chosen ? 2 : 1
    Behavior on border.color { ColorAnimation { duration: studio.motion.hover } }
    // it rises with its page; under the mouse it lifts, with a light that follows the mouse (CardMotion, MouseLight)
    property real dim: dimmed ? 0.55 : 1
    Behavior on dim { NumberAnimation { duration: studio.motion.fast } }
    opacity: motion.fade * dim
    transform: motion.moves
    CardMotion { id: motion; hovered: area.containsMouse; lifts: !card.chosen; radius: card.radius }
    MouseLight { id: light; hovered: area.containsMouse && !card.chosen; radius: card.radius }

    MouseArea {
        id: area
        anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
        onClicked: card.clicked()
        onDoubleClicked: window.openAction(card.action.name)
        onPositionChanged: function (mouse) { light.at = Qt.point(mouse.x, mouse.y) }
    }
    Rectangle {  // the action as a strip of its steps
        x: 10; y: 10; width: card.width - 20; height: 112; radius: 11
        color: studio.colors.bg
        Column {
            anchors.centerIn: parent; spacing: 6
            Repeater {
                model: Math.min(5, Math.max(1, card.action.sections || 1))
                delegate: Rectangle {
                    required property int index
                    width: 120 - index * 14; height: 8; radius: 4
                    color: index === 0 ? studio.colors.accent2 : Qt.rgba(studio.colors.accent2.r, studio.colors.accent2.g, studio.colors.accent2.b, 0.35)
                }
            }
        }
        Rectangle {  // Play
            anchors { right: parent.right; bottom: parent.bottom; margins: 8 }
            width: 34; height: 34; radius: 17
            color: playArea.containsMouse ? Qt.lighter(studio.colors.accent, 1.1) : studio.colors.accent
            scale: playArea.pressed ? 0.92 : 1
            Text { anchors.centerIn: parent; text: "▶"; color: studio.colors.onAccent; font.pixelSize: 12 }
            MouseArea { id: playArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: card.play() }
        }
    }
    Text {
        id: nameText
        x: 12; y: 130; width: card.width - 24
        text: card.action.name || ""
        color: studio.colors.text; font.pixelSize: 14; font.weight: Font.DemiBold
        elide: Text.ElideMiddle
    }
    Text {
        x: 12; y: 152; width: card.width - 24; elide: Text.ElideRight
        text: card.action.error ? "can't be read" : (card.action.steps || 0) + " steps" + (card.action.sections > 1 ? " · " + card.action.sections + " sections" : "")
        color: card.action.error ? studio.colors.danger : studio.colors.muted; font.pixelSize: 12
    }
    Text {
        x: 12; y: 172; width: card.width - 24; elide: Text.ElideRight
        text: card.action.used_by && card.action.used_by.length ? "used by " + card.action.used_by.join(", ") : "ACTION"
        color: card.action.used_by && card.action.used_by.length ? studio.colors.faint : studio.colors.accent2
        font.pixelSize: card.action.used_by && card.action.used_by.length ? 12 : 10; font.weight: Font.DemiBold
        font.letterSpacing: card.action.used_by && card.action.used_by.length ? 0 : 0.6
    }
    // a name too long for the card: whole on hover
    ToolTip.visible: area.containsMouse && nameText.truncated
    ToolTip.text: nameText.text
    ToolTip.delay: 400
}
