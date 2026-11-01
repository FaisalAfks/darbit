// New bot: make one from darbit's template, install one from its git link, or add a folder that has a darbit.toml.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Dialogs

Popup {
    id: sheet
    property string way: "new"  // new, link, folder
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: 520
    modal: true
    focus: true
    padding: 26
    onOpened: { field.text = ""; field.forceActiveFocus() }
    Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, 0.45) }
    background: Rectangle { radius: 22; color: studio.colors.glassStrong; border.color: studio.colors.line }
    enter: Transition {
        ParallelAnimation {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: studio.effects ? 180 : 0 }
            NumberAnimation { property: "scale"; from: 0.94; to: 1; duration: studio.effects ? 240 : 0; easing.type: Easing.OutBack; easing.overshoot: 1.2 }
        }
    }
    exit: Transition { NumberAnimation { property: "opacity"; to: 0; duration: studio.effects ? 120 : 0 } }

    function submit() {
        var text = field.text.trim()
        if (text === "") return
        if (way === "new") studio.newBot(text)
        else if (way === "link") studio.installBot(text)
        else studio.addBot(text)
        close()
    }

    contentItem: Column {
        spacing: 18
        Text { text: "New bot"; color: studio.colors.text; font.pixelSize: 22; font.weight: Font.Bold }
        Segmented {
            current: sheet.way
            itemHeight: 32
            model: [
                { key: "new", label: "From the template" },
                { key: "link", label: "From a link" },
                { key: "folder", label: "A folder I have" }
            ]
            onPicked: function (key) { sheet.way = key; field.text = ""; field.forceActiveFocus() }
        }
        Text {
            width: parent.width; wrapMode: Text.Wrap
            color: studio.colors.muted; font.pixelSize: 14
            text: sheet.way === "new" ? "A bot folder with darbit's layout (settings, images, actions and its code), in darbit's bots folder."
                : sheet.way === "link" ? "Its git link, e.g. https://github.com/me/my-bot. darbit clones its newest release and sets up its environment: that can take a minute."
                : "A folder with a darbit.toml, kept where it is."
        }
        Row {
            spacing: 10
            TextField {
                id: field
                width: sheet.way === "folder" ? 360 : 468
                height: 44
                placeholderText: sheet.way === "new" ? "Its name, e.g. fish-bot" : sheet.way === "link" ? "https://github.com/…" : "C:\\bots\\my-bot"
                color: studio.colors.text; placeholderTextColor: studio.colors.faint
                font.pixelSize: 15
                onAccepted: sheet.submit()
                background: Rectangle { radius: 12; color: studio.colors.raised; border.color: field.activeFocus ? studio.colors.accent : studio.colors.line }
            }
            PillButton { visible: sheet.way === "folder"; text: "Browse…"; onClicked: folders.open() }
        }
        Row {
            anchors.right: parent.right
            spacing: 10
            PillButton { text: "Cancel"; kind: "quiet"; onClicked: sheet.close() }
            PillButton {
                kind: "primary"
                text: sheet.way === "new" ? "Make it" : sheet.way === "link" ? "Install" : "Add"
                enabled: field.text.trim() !== ""
                onClicked: sheet.submit()
            }
        }
    }
    FolderDialog {
        id: folders
        title: "A bot folder (one with a darbit.toml)"
        onAccepted: field.text = selectedFolder.toString()
    }
}
