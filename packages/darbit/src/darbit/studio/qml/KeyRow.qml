// One key in darbit settings: what it does and its keys. A click listens for new ones: press them, Esc to leave it as
// it is, Delete to turn it off. ↺ goes back to the default.
import QtQuick
import QtQuick.Layouts
import "format.js" as Format

Rectangle {
    id: row
    property var key: ({})
    property bool listening: false
    signal chosen(string keys)
    signal reset()
    implicitHeight: 44
    radius: 10
    color: hover.hovered ? studio.colors.raised : "transparent"
    HoverHandler { id: hover }

    // the keys pressed, in the keymap's words ("ctrl+alt+c"); "" for a modifier alone
    function comboOf(event) {
        var name = ""
        if (event.key >= Qt.Key_F1 && event.key <= Qt.Key_F12) name = "f" + (event.key - Qt.Key_F1 + 1)
        else if (event.key >= 0x20 && event.key <= 0x7e) name = String.fromCharCode(event.key).toLowerCase()
        if (name === "") return ""
        var parts = []
        if (event.modifiers & Qt.ControlModifier) parts.push("ctrl")
        if (event.modifiers & Qt.AltModifier) parts.push("alt")
        if (event.modifiers & Qt.ShiftModifier) parts.push("shift")
        parts.push(name)
        return parts.join("+")
    }

    RowLayout {
        anchors { fill: parent; leftMargin: 12; rightMargin: 6 }
        spacing: 10
        Text { text: row.key.label || ""; color: studio.colors.text; font.pixelSize: 14; Layout.fillWidth: true; elide: Text.ElideRight }
        Rectangle {
            id: cap
            Layout.preferredWidth: Math.max(96, capText.implicitWidth + 24); Layout.preferredHeight: 30
            radius: 8
            color: row.listening ? Qt.rgba(studio.colors.accent.r, studio.colors.accent.g, studio.colors.accent.b, 0.18) : studio.colors.raised
            border.color: row.listening ? studio.colors.accent : studio.colors.line
            focus: row.listening
            Text {
                id: capText
                anchors.centerIn: parent
                text: row.listening ? "Press keys…" : row.key.keys ? Format.sequence(row.key.keys) : "Off"
                color: row.listening ? studio.colors.accent : row.key.keys ? studio.colors.text : studio.colors.faint
                font.pixelSize: 12; font.family: "monospace"; font.weight: Font.DemiBold
            }
            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: { row.listening = true; cap.forceActiveFocus() } }
            onActiveFocusChanged: if (!activeFocus) row.listening = false
            Keys.onPressed: function (event) {
                if (!row.listening) return
                event.accepted = true
                if (event.key === Qt.Key_Escape) { row.listening = false; return }
                if (event.key === Qt.Key_Delete) { row.listening = false; row.chosen(""); return }
                var keys = row.comboOf(event)
                if (keys === "") return  // a modifier alone: the rest is still coming
                row.listening = false
                row.chosen(keys)
            }
        }
        IconButton {
            Layout.preferredWidth: 28; Layout.preferredHeight: 28
            glyph: "↺"; tip: "Back to " + (row.key.default ? Format.sequence(row.key.default) : "off")
            opacity: row.key.keys === row.key.default ? 0 : 1
            enabled: opacity > 0
            onClicked: row.reset()
        }
    }
}
