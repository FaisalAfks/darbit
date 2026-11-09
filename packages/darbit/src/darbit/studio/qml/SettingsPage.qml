// Settings (round 12, A with B's help): the bot's settings.toml as rows in section cards that flow into two columns
// on a wide window; the section list with search, counts and a dot on sections with changes; on a wide window, a
// panel that explains the setting under the mouse. A changed value gets a dot and ↺, and a save bar slides up until
// the changes are saved or undone.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "format.js" as Format

Item {
    id: page
    property var edits: ({})
    property string section: ""
    property string query: ""
    property var pointed: null      // the setting the help panel explains
    readonly property bool changed: Object.keys(edits).length > 0
    readonly property var sections: studio.settings.sections || []
    readonly property bool twoColumns: scroller.width >= 940
    readonly property bool withHelp: page.width >= 1320
    // the sections shown: the chosen one (or all), each with only the settings the search matches
    readonly property var shown: {
        var words = query.toLowerCase().trim()
        var found = []
        for (var index = 0; index < sections.length; index++) {
            var one = sections[index]
            if (section !== "" && one.key !== section) continue
            var settings = one.settings.filter(function (setting) {
                return words === "" || [setting.label, setting.help, setting.key].join(" ").toLowerCase().indexOf(words) >= 0
            })
            if (settings.length) found.push({ key: one.key, label: one.label, settings: settings })
        }
        return found
    }
    // the cards split into two columns by their number of rows, so the columns end about level
    readonly property var columns: {
        if (!twoColumns) return [shown, []]
        var left = [], right = [], leftRows = 0, rightRows = 0
        for (var index = 0; index < shown.length; index++) {
            var rows = shown[index].settings.length + 1
            if (leftRows <= rightRows) { left.push(shown[index]); leftRows += rows }
            else { right.push(shown[index]); rightRows += rows }
        }
        return [left, right]
    }

    Connections {
        target: studio
        function onSettingsChanged() { page.edits = {}; if (!page.sections.some(function (one) { return one.key === page.section })) page.section = "" }
    }
    function value(setting) {
        if (setting.key in edits) return edits[setting.key]
        var values = studio.settings.values || {}
        return setting.key in values ? values[setting.key] : setting.default
    }
    function edit(key, value) {
        var next = Object.assign({}, edits)
        var saved = (studio.settings.values || {})[key]
        if (JSON.stringify(saved) === JSON.stringify(value)) delete next[key]
        else next[key] = value
        edits = next
    }
    function changesIn(one) { return one.settings.filter(function (setting) { return setting.key in page.edits }).length }
    function restoreDefaults() {
        var next = {}
        for (var index = 0; index < sections.length; index++)
            for (var at = 0; at < sections[index].settings.length; at++) {
                var setting = sections[index].settings[at]
                if (JSON.stringify((studio.settings.values || {})[setting.key]) !== JSON.stringify(setting.default)) next[setting.key] = setting.default
            }
        edits = next
    }
    function save() { studio.saveSettings(Object.assign({}, studio.settings.values || {}, page.edits)) }

    Column {
        visible: page.sections.length === 0
        anchors.centerIn: parent; spacing: 8
        Text { anchors.horizontalCenter: parent.horizontalCenter; text: studio.settings.error ? "Its settings.toml has a problem" : "Nothing to set"; color: studio.colors.text; font.pixelSize: 20; font.weight: Font.Bold }
        Text { anchors.horizontalCenter: parent.horizontalCenter; text: studio.settings.error || "This bot has no settings.toml."; color: studio.colors.muted; font.pixelSize: 14 }
    }

    // ---- the sections, with search
    Column {
        id: list
        visible: page.sections.length > 0
        x: 24; width: 210; spacing: 3
        Field {
            id: search
            round: true; icon: "⌕"
            width: parent.width; height: 38
            placeholderText: "Search " + page.sections.reduce(function (sum, one) { return sum + one.settings.length }, 0) + " settings"
            onTextChanged: page.query = text
        }
        Item { width: 1; height: 6 }
        Repeater {
            model: [{ key: "", label: "Everything", settings: [] }].concat(page.sections)
            delegate: Rectangle {
                required property var modelData
                readonly property bool on: page.section === modelData.key
                readonly property int changes: modelData.key === "" ? Object.keys(page.edits).length : page.changesIn(modelData)
                width: list.width; height: 38; radius: 11
                color: on ? studio.colors.raisedHover : area.containsMouse ? studio.colors.raised : "transparent"
                Rectangle { visible: parent.on; x: 0; y: 9; width: 3; height: 20; radius: 1.5; color: studio.colors.accent }
                Text { x: 14; anchors.verticalCenter: parent.verticalCenter; width: parent.width - 50; elide: Text.ElideRight; text: modelData.label; color: parent.on ? studio.colors.text : studio.colors.muted; font.pixelSize: 13; font.weight: Font.DemiBold }
                Rectangle { visible: parent.changes > 0; anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter } width: 7; height: 7; radius: 3.5; color: studio.colors.warn }
                Text {
                    visible: parent.changes === 0 && modelData.key !== ""
                    anchors { right: parent.right; rightMargin: 12; verticalCenter: parent.verticalCenter }
                    text: modelData.settings.length; color: studio.colors.faint; font.pixelSize: 11
                }
                MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: page.section = modelData.key }
            }
        }
    }

    // ---- the cards
    Flickable {
        id: scroller
        SmoothWheel { view: scroller }
        visible: page.sections.length > 0
        anchors { left: list.right; leftMargin: 16; right: help.visible ? help.left : parent.right; rightMargin: help.visible ? 16 : 24; top: parent.top; bottom: parent.bottom }
        contentHeight: Math.max(leftColumn.height, rightColumn.height) + 110
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {}
        Text {
            visible: page.shown.length === 0
            text: "No setting matches “" + page.query + "”"
            color: studio.colors.muted; font.pixelSize: 14
        }
        Repeater {
            model: 2
            delegate: Column {
                id: column
                required property int index
                x: index === 0 ? 0 : (scroller.width + 14) / 2
                width: page.twoColumns ? (scroller.width - 14) / 2 : scroller.width
                spacing: 14
                Component.onCompleted: if (index === 0) leftColumn.target = column; else rightColumn.target = column
                Repeater {
                    model: page.columns[column.index]
                    delegate: Glass {
                        id: card
                        required property var modelData
                        required property int index
                        width: column.width
                        height: rows.height + 64
                        title: modelData.label
                        note: page.changesIn(modelData) ? page.changesIn(modelData) + " changed" : ""
                        content: Column {
                            id: rows
                            width: parent.width
                            Repeater {
                                model: card.modelData.settings
                                delegate: Setting {
                                    required property var modelData
                                    required property int index
                                    width: rows.width
                                    first: index === 0
                                    setting: modelData
                                    current: page.value(modelData)
                                    changed: modelData.key in page.edits
                                    onEdited: function (value) { page.edit(modelData.key, value) }
                                    onPointed: page.pointed = modelData
                                }
                            }
                        }
                    }
                }
            }
        }
        QtObject { id: leftColumn; property Item target: null; readonly property real height: target ? target.height : 0 }
        QtObject { id: rightColumn; property Item target: null; readonly property real height: target ? target.height : 0 }
    }

    // ---- the help panel: what the setting under the mouse does, on a wide window
    Glass {
        id: help
        visible: page.withHelp && page.sections.length > 0
        anchors { right: parent.right; rightMargin: 24; top: parent.top }
        width: 280; height: about.implicitHeight + 40
        lift: false
        readonly property var setting: page.pointed
        content: Column {
            id: about
            width: parent.width; spacing: 10
            Text {
                visible: !help.setting
                width: parent.width; wrapMode: Text.Wrap
                text: "Point at a setting to see what it does."
                color: studio.colors.muted; font.pixelSize: 13
            }
            Text {
                visible: !!help.setting
                width: parent.width; wrapMode: Text.Wrap
                text: help.setting ? (help.setting.label || help.setting.key) : ""
                color: studio.colors.text; font.pixelSize: 17; font.weight: Font.Bold
            }
            Text {
                visible: !!help.setting && !!help.setting.help
                width: parent.width; wrapMode: Text.Wrap
                text: help.setting ? help.setting.help || "" : ""
                color: studio.colors.muted; font.pixelSize: 13; lineHeight: 1.15
            }
            Grid {
                visible: !!help.setting
                columns: 2; columnSpacing: 12; rowSpacing: 6
                readonly property var rules: help.setting && help.setting.rules ? help.setting.rules : ({})
                Text { text: "Now"; color: studio.colors.faint; font.pixelSize: 12 }
                Text { text: help.setting ? Format.setting(page.value(help.setting)) : ""; color: studio.colors.text; font.pixelSize: 12; font.family: "monospace" }
                Text { text: "Default"; color: studio.colors.faint; font.pixelSize: 12 }
                Text { text: help.setting ? Format.setting(help.setting.default) : ""; color: studio.colors.text; font.pixelSize: 12; font.family: "monospace" }
                Text { visible: parent.rules.min !== undefined || parent.rules.max !== undefined; text: "Range"; color: studio.colors.faint; font.pixelSize: 12 }
                Text {
                    visible: parent.rules.min !== undefined || parent.rules.max !== undefined
                    text: (parent.rules.min !== undefined ? parent.rules.min : "…") + " to " + (parent.rules.max !== undefined ? parent.rules.max : "…")
                    color: studio.colors.text; font.pixelSize: 12; font.family: "monospace"
                }
                Text { text: "Key"; color: studio.colors.faint; font.pixelSize: 12 }
                Text { text: help.setting ? help.setting.key : ""; color: studio.colors.text; font.pixelSize: 12; font.family: "monospace" }
            }
            Text {
                visible: !!help.setting && help.setting.key in page.edits
                text: "Changed, not saved yet."
                color: studio.colors.warn; font.pixelSize: 12; font.weight: Font.DemiBold
            }
        }
    }

    // ---- the save bar
    FloatingPill {
        anchors.horizontalCenter: parent.horizontalCenter
        y: page.changed ? page.height - height - 24 : page.height + 20
        Behavior on y { NumberAnimation { duration: studio.effects ? 260 : 0; easing.type: Easing.OutCubic } }
        Text {
            Layout.leftMargin: 12
            text: Object.keys(page.edits).length + (Object.keys(page.edits).length === 1 ? " change" : " changes") + " not saved"
            color: studio.colors.warn; font.pixelSize: 14; font.weight: Font.DemiBold
            rightPadding: 8
        }
        PillButton { text: "Undo"; kind: "quiet"; small: true; onClicked: page.edits = {} }
        PillButton { text: "Save"; kind: "primary"; small: true; onClicked: page.save() }
    }
    PillButton {
        visible: page.sections.length > 0 && !page.changed
        anchors { right: parent.right; rightMargin: 24; bottom: parent.bottom; bottomMargin: 24 }
        text: "Restore defaults"; kind: "quiet"; small: true
        onClicked: page.restoreDefaults()
    }
    Shortcut { sequence: window.keyOf("file.save"); enabled: page.visible && page.changed; onActivated: page.save() }
    Shortcut { sequence: window.keyOf("search"); enabled: page.visible && page.sections.length > 0; onActivated: search.forceActiveFocus() }
}
