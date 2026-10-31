// Settings: the bot's settings.toml as a form, its sections on the left; a changed value gets a dot, and a save bar
// slides up until the changes are saved or undone.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Item {
    id: page
    property var edits: ({})
    property string section: ""
    readonly property bool changed: Object.keys(edits).length > 0
    readonly property var sections: studio.settings.sections || []
    readonly property var shown: sections.filter(function (one) { return page.section === "" || one.key === page.section })

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
    function restoreDefaults() {
        var next = {}
        for (var index = 0; index < sections.length; index++)
            for (var at = 0; at < sections[index].settings.length; at++) {
                var setting = sections[index].settings[at]
                if (JSON.stringify((studio.settings.values || {})[setting.key]) !== JSON.stringify(setting.default)) next[setting.key] = setting.default
            }
        edits = next
    }

    Column {
        visible: page.sections.length === 0
        anchors.centerIn: parent; spacing: 8
        Text { anchors.horizontalCenter: parent.horizontalCenter; text: studio.settings.error ? "Its settings.toml has a problem" : "Nothing to set"; color: studio.colors.text; font.pixelSize: 20; font.weight: Font.Bold }
        Text { anchors.horizontalCenter: parent.horizontalCenter; text: studio.settings.error || "This bot has no settings.toml."; color: studio.colors.muted; font.pixelSize: 14 }
    }

    // ---- the sections
    Column {
        id: list
        visible: page.sections.length > 1
        x: 24; width: 220; spacing: 4
        Repeater {
            model: [{ key: "", label: "Everything" }].concat(page.sections)
            delegate: Rectangle {
                required property var modelData
                readonly property bool on: page.section === modelData.key
                width: list.width; height: 42; radius: 12
                color: on ? studio.colors.raisedHover : area.containsMouse ? studio.colors.raised : "transparent"
                Rectangle { visible: parent.on; x: 0; y: 10; width: 3; height: 22; radius: 1.5; color: studio.colors.accent }
                Text { x: 16; anchors.verticalCenter: parent.verticalCenter; text: modelData.label; color: parent.on ? studio.colors.text : studio.colors.muted; font.pixelSize: 14; font.weight: Font.DemiBold }
                MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: page.section = modelData.key }
            }
        }
    }

    // ---- the form
    Flickable {
        visible: page.sections.length > 0
        anchors { left: list.visible ? list.right : parent.left; leftMargin: list.visible ? 16 : 24; right: parent.right; rightMargin: 24; top: parent.top; bottom: parent.bottom }
        contentHeight: form.height + 120
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {}
        ColumnLayout {
            id: form
            width: Math.min(parent.width, 860)
            spacing: 16
            Repeater {
                model: page.shown
                delegate: Glass {
                    id: card
                    required property var modelData
                    required property int index
                    title: modelData.label
                    delay: index * 50
                    Layout.fillWidth: true
                    Layout.preferredHeight: 70 + fields.height
                    content: Column {
                        id: fields
                        width: parent.width; spacing: 10
                        Repeater {
                            model: card.modelData.settings
                            delegate: Setting {
                                required property var modelData
                                width: parent.width
                                setting: modelData
                                current: page.value(modelData)
                                changed: modelData.key in page.edits
                                onEdited: function (value) { page.edit(modelData.key, value) }
                            }
                        }
                    }
                }
            }
        }
    }

    // ---- the save bar
    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        y: page.changed ? page.height - height - 24 : page.height + 20
        Behavior on y { NumberAnimation { duration: studio.effects ? 260 : 0; easing.type: Easing.OutCubic } }
        width: saveRow.implicitWidth + 24; height: 60; radius: 30
        color: studio.colors.glassStrong; border.color: studio.colors.line
        RowLayout {
            id: saveRow
            anchors { left: parent.left; leftMargin: 20; verticalCenter: parent.verticalCenter }
            spacing: 10
            Text {
                text: Object.keys(page.edits).length + (Object.keys(page.edits).length === 1 ? " change" : " changes") + " not saved"
                color: studio.colors.warn; font.pixelSize: 14; font.weight: Font.DemiBold
                rightPadding: 8
            }
            PillButton { text: "Undo"; kind: "quiet"; small: true; onClicked: page.edits = {} }
            PillButton { text: "Save"; kind: "primary"; small: true; onClicked: studio.saveSettings(Object.assign({}, studio.settings.values || {}, page.edits)) }
        }
    }
    PillButton {
        visible: page.sections.length > 0 && !page.changed
        anchors { right: parent.right; rightMargin: 24; bottom: parent.bottom; bottomMargin: 24 }
        text: "Restore defaults"; kind: "quiet"; small: true
        onClicked: page.restoreDefaults()
    }
    Shortcut { sequence: "Ctrl+S"; enabled: page.visible && page.changed; onActivated: studio.saveSettings(Object.assign({}, studio.settings.values || {}, page.edits)) }
}
