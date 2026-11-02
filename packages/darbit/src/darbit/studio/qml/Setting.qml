// One setting as a row (round 12): its name and help on the left, a control made for its type on the right (a switch,
// a stepper, a slider when it has a range, a list, a field), a dot while it isn't saved, and ↺ back to its default.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "format.js" as Format

Rectangle {
    id: row
    property var setting: ({})
    property var current
    property bool changed: false   // not saved yet: a dot by its name
    property bool first: false     // no line above the first row of a card
    signal edited(var value)
    signal pointed()               // the mouse or the keys came to it: the help panel shows it
    readonly property string kind: setting.type || "str"
    readonly property var rules: setting.rules || ({})
    readonly property bool hasRange: rules.min !== undefined && rules.max !== undefined
    readonly property bool atDefault: JSON.stringify(current) === JSON.stringify(setting.default)
    implicitHeight: Math.max(54, words.implicitHeight + 22)
    color: hover.hovered ? Qt.rgba(1, 1, 1, 0.025) : "transparent"
    HoverHandler { id: hover; onHoveredChanged: if (hovered) row.pointed() }

    function shown(value) { return Format.setting(value) }
    function parsed(text) {
        if (kind === "list" || kind === "keys") return text.split(",").map(function (part) { return part.trim() }).filter(function (part) { return part !== "" })
        return text
    }

    Rectangle { visible: !row.first; width: parent.width; height: 1; color: Qt.rgba(1, 1, 1, 0.05) }
    RowLayout {
        anchors { fill: parent; leftMargin: 0; rightMargin: 0 }
        spacing: 14
        Column {
            id: words
            Layout.fillWidth: true
            spacing: 2
            Row {
                spacing: 7
                Rectangle { visible: row.changed; width: 7; height: 7; radius: 3.5; color: studio.colors.warn; anchors.verticalCenter: parent.verticalCenter }
                Text { text: row.setting.label || row.setting.key; color: studio.colors.text; font.pixelSize: 14; font.weight: Font.DemiBold }
            }
            Text {
                width: parent.width
                visible: text !== ""
                text: [row.setting.help || "", row.atDefault || row.setting.default === undefined ? "" : "default " + row.shown(row.setting.default)]
                    .filter(function (part) { return part !== "" }).join("  ·  ")
                color: studio.colors.muted; font.pixelSize: 12
                wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight
            }
        }
        Loader {
            Layout.alignment: Qt.AlignVCenter
            sourceComponent: row.kind === "bool" ? asSwitch
                : row.kind === "float" && row.hasRange ? asSlider
                : row.kind === "int" || row.kind === "float" ? asStepper
                : row.kind === "choice" ? asList : asField
        }
        IconButton {
            Layout.preferredWidth: 30; Layout.preferredHeight: 30
            glyph: "↺"; tip: "Back to its default: " + row.shown(row.setting.default)
            opacity: row.atDefault || row.setting.default === undefined ? 0 : 1
            enabled: opacity > 0
            onClicked: row.edited(row.setting.default)
        }
    }

    Component { id: asSwitch; Switcher { checked: row.current === true; onToggled: function (on) { row.edited(on) } } }
    Component {
        id: asStepper
        Stepper {
            value: Number(row.current) || 0
            step: row.kind === "float" ? 0.1 : 1
            decimals: row.kind === "float" ? 1 : 0
            low: row.rules.min !== undefined ? row.rules.min : null
            high: row.rules.max !== undefined ? row.rules.max : null
            onEdited: function (value) { row.edited(value) }
        }
    }
    Component {
        id: asSlider
        ValueSlider {
            value: Number(row.current) || 0
            low: row.rules.min; high: row.rules.max
            decimals: row.rules.max - row.rules.min > 10 ? 0 : 1
            onEdited: function (value) { row.edited(value) }
        }
    }
    Component { id: asList; Dropdown { choices: row.rules.options || []; chosen: row.current; onPicked: function (value) { row.edited(value) } } }
    Component {
        id: asField
        Field {
            implicitWidth: 230; implicitHeight: 34
            text: row.shown(row.current)
            color: studio.colors.text; font.pixelSize: 13
            leftPadding: 10
            onTextEdited: row.edited(row.parsed(text))
            onActiveFocusChanged: if (activeFocus) row.pointed()
        }
    }
}
