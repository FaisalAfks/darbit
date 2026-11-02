// A text field: the one every page, sheet and tool uses. `round` is the search shape (with an `icon`), `quiet` shows no
// box until it's being edited (a name in a heading), and `ink` is the colour of its edge while it has the focus.
import QtQuick
import QtQuick.Controls.Basic

TextField {
    id: field
    property string icon: ""
    property bool round: false
    property bool quiet: false
    property color ink: studio.colors.accent
    implicitHeight: 34
    leftPadding: icon !== "" ? 34 : 12
    color: studio.colors.text
    placeholderTextColor: studio.colors.faint
    font.pixelSize: 13
    background: Rectangle {
        radius: field.round ? height / 2 : 10
        color: field.quiet && !field.activeFocus ? "transparent" : field.round ? studio.colors.glass : studio.colors.raised
        border.color: field.activeFocus ? field.ink : field.quiet ? "transparent" : studio.colors.line
        Text {
            visible: field.icon !== ""
            x: 13; anchors.verticalCenter: parent.verticalCenter
            text: field.icon; color: studio.colors.faint; font.pixelSize: 15; font.family: studio.symbols
        }
    }
}
