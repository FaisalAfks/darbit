// A button in a pill: a round glyph with a tooltip in a row, and the glyph with its label in a pill's column or
// floating card (`labelled`). `kind` danger colours it. Every pill's buttons are these, so they change form together.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Rectangle {
    id: action
    property string glyph: ""
    property string label: ""
    property string tip: label
    property bool labelled: false
    property string kind: "plain"  // plain or danger
    signal clicked()
    readonly property color ink: kind === "danger" ? studio.colors.danger : studio.colors.text
    implicitWidth: labelled ? line.implicitWidth + 28 : 40
    implicitHeight: labelled ? 34 : 40
    Layout.fillWidth: labelled
    radius: height / 2
    opacity: enabled ? 1 : 0.35
    scale: area.pressed ? 0.96 : 1
    Behavior on scale { NumberAnimation { duration: studio.effects ? 90 : 0 } }
    color: area.containsMouse && enabled ? studio.colors.raisedHover : labelled ? studio.colors.raised : "transparent"
    Row {
        id: line
        anchors.verticalCenter: parent.verticalCenter
        x: action.labelled ? 14 : (parent.width - width) / 2
        spacing: 9
        Text {
            text: action.glyph
            color: action.ink; font.pixelSize: 13; font.family: studio.symbols
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            visible: action.labelled
            text: action.label
            color: action.ink; font.pixelSize: 13; font.weight: Font.DemiBold
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    MouseArea {
        id: area; anchors.fill: parent; hoverEnabled: true
        cursorShape: action.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: if (action.enabled) action.clicked()
    }
    ToolTip.visible: area.containsMouse && tip !== "" && (!labelled || tip !== label)
    ToolTip.text: tip
    ToolTip.delay: 400
}
