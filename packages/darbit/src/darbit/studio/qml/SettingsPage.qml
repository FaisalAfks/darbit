// Settings: the bot's settings.toml as a form, a card per section; changes are kept until Save.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Flickable {
    id: page
    property var edits: ({})
    readonly property bool changed: Object.keys(edits).length > 0
    contentHeight: column.height + 120
    clip: true
    ScrollBar.vertical: ScrollBar {}

    Connections {
        target: studio
        function onSettingsChanged() { page.edits = {} }
    }

    function value(setting) {
        if (setting.key in edits) return edits[setting.key]
        var values = studio.settings.values || {}
        return setting.key in values ? values[setting.key] : setting.default
    }
    function edit(key, value) {
        var next = Object.assign({}, edits)
        next[key] = value
        edits = next
    }
    function save() {
        var values = Object.assign({}, studio.settings.values || {}, edits)
        studio.saveSettings(values)
    }
    function restoreDefaults() {
        var next = {}
        var sections = studio.settings.sections || []
        for (var index = 0; index < sections.length; index++)
            for (var at = 0; at < sections[index].settings.length; at++) {
                var setting = sections[index].settings[at]
                next[setting.key] = setting.default
            }
        edits = next
    }

    ColumnLayout {
        id: column
        x: 24; width: page.width - 48
        spacing: 20

        RowLayout {
            Layout.fillWidth: true
            spacing: 16
            Text { text: "Settings"; color: studio.colors.text; font.pixelSize: 30; font.weight: Font.Bold }
            Text {
                text: (studio.bot.name || "") + (page.changed ? " · not saved yet" : "")
                color: page.changed ? studio.colors.warn : studio.colors.muted; font.pixelSize: 14
                Layout.fillWidth: true
            }
            Button {
                text: "Restore defaults"
                onClicked: page.restoreDefaults()
                contentItem: Text { text: parent.text; color: studio.colors.text; font.weight: Font.DemiBold; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                background: Rectangle { implicitHeight: 40; implicitWidth: 150; radius: 10; color: parent.hovered ? studio.colors.raisedHover : studio.colors.raised }
            }
            Button {
                text: "Undo"
                visible: page.changed
                onClicked: page.edits = {}
                contentItem: Text { text: parent.text; color: studio.colors.text; font.weight: Font.DemiBold; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                background: Rectangle { implicitHeight: 40; implicitWidth: 80; radius: 10; color: parent.hovered ? studio.colors.raisedHover : studio.colors.raised }
            }
            Button {
                text: "Save"
                enabled: page.changed
                onClicked: page.save()
                contentItem: Text { text: parent.text; color: studio.colors.onAccent; font.weight: Font.Bold; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                background: Rectangle { implicitHeight: 40; implicitWidth: 80; radius: 10; color: studio.colors.accent; opacity: parent.enabled ? 1 : 0.4 }
            }
        }

        Text {
            visible: !!studio.settings.error
            text: studio.settings.error || ""
            color: studio.colors.danger; font.pixelSize: 14
            Layout.fillWidth: true; wrapMode: Text.Wrap
        }
        Text {
            visible: (studio.settings.sections || []).length === 0 && !studio.settings.error
            text: "This bot has no settings.toml, so nothing to set."
            color: studio.colors.muted; font.pixelSize: 15
        }

        GridLayout {
            Layout.fillWidth: true
            columns: page.width > 1100 ? 2 : 1
            columnSpacing: 20; rowSpacing: 20
            Repeater {
                model: studio.settings.sections || []
                delegate: Glass {
                    id: section
                    required property var modelData
                    title: modelData.label
                    Layout.fillWidth: true; Layout.alignment: Qt.AlignTop
                    Layout.preferredHeight: 70 + fields.height
                    content: Column {
                        id: fields
                        width: parent.width; spacing: 12
                        Repeater {
                            model: section.modelData.settings
                            delegate: Setting {
                                required property var modelData
                                width: parent.width
                                setting: modelData
                                current: page.value(modelData)
                                onEdited: function (value) { page.edit(modelData.key, value) }
                            }
                        }
                    }
                }
            }
        }
    }
}
