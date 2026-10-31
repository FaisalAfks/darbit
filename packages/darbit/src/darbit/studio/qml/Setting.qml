// One setting: a switch for yes or no, a number field, a list to choose from, or a text field for the rest.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Rectangle {
    id: row
    property var setting: ({})
    property var current
    signal edited(var value)
    readonly property string kind: setting.type || "str"
    height: kind === "bool" ? 66 : 92
    radius: 12
    color: kind === "bool" ? studio.colors.raised : "transparent"

    // a switch, on the right of its label
    RowLayout {
        visible: row.kind === "bool"
        anchors { fill: parent; leftMargin: 14; rightMargin: 14 }
        Column {
            Layout.fillWidth: true
            Text { text: row.setting.label || row.setting.key; color: studio.colors.text; font.pixelSize: 15; font.weight: Font.DemiBold }
            Text { text: row.setting.help || ""; visible: text !== ""; color: studio.colors.muted; font.pixelSize: 13 }
        }
        Switch {
            checked: row.current === true
            onToggled: row.edited(checked)
            indicator: Rectangle {
                implicitWidth: 44; implicitHeight: 26; radius: 13
                color: parent.checked ? studio.colors.accent : studio.colors.raisedHover
                Rectangle {
                    x: parent.parent.checked ? parent.width - width - 3 : 3; y: 3
                    width: 20; height: 20; radius: 10
                    color: parent.parent.checked ? studio.colors.onAccent : studio.colors.text
                    Behavior on x { NumberAnimation { duration: 120 } }
                }
            }
        }
    }

    // a field under its label
    Column {
        visible: row.kind !== "bool"
        width: parent.width; spacing: 6
        Text { text: row.setting.label || row.setting.key; color: studio.colors.text; font.pixelSize: 15; font.weight: Font.DemiBold }
        Loader {
            width: parent.width; height: 40
            sourceComponent: row.kind === "choice" ? choice : field
        }
        Text { text: row.setting.help || ""; visible: text !== ""; color: studio.colors.muted; font.pixelSize: 13 }
    }

    Component {
        id: field
        TextField {
            text: row.current === undefined || row.current === null ? "" : (Array.isArray(row.current) ? row.current.join(", ") : String(row.current))
            color: studio.colors.text
            font.pixelSize: 15
            inputMethodHints: row.kind === "int" || row.kind === "float" ? Qt.ImhFormattedNumbersOnly : Qt.ImhNone
            validator: row.kind === "int" ? whole : (row.kind === "float" ? decimal : null)
            onTextEdited: row.edited(row.parsed(text))
            background: Rectangle {
                radius: 10; color: studio.colors.raised
                border.color: parent.activeFocus ? studio.colors.accent : studio.colors.line
            }
        }
    }
    Component {
        id: choice
        ComboBox {
            model: (row.setting.rules && row.setting.rules.options) || []
            currentIndex: model.indexOf(row.current)
            onActivated: function (index) { row.edited(model[index]) }
        }
    }
    IntValidator { id: whole; bottom: row.setting.rules && row.setting.rules.min !== undefined ? row.setting.rules.min : -2147483647; top: row.setting.rules && row.setting.rules.max !== undefined ? row.setting.rules.max : 2147483647 }
    DoubleValidator { id: decimal }

    function parsed(text) {
        if (kind === "int") return parseInt(text)
        if (kind === "float") return parseFloat(text)
        if (kind === "list" || kind === "keys") return text.split(",").map(function (part) { return part.trim() }).filter(function (part) { return part !== "" })
        return text
    }
}
