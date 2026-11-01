// An action, open: its sections as cards, its steps read like what they do. Play walks through them (the step
// playing glows); a wait's seconds, a section's name and the order of steps can be changed, then saved to its file.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Item {
    id: page
    property var draft: []  // the sections being edited
    readonly property var action: studio.action
    readonly property string name: action.name || ""
    readonly property bool changed: JSON.stringify(draft) !== JSON.stringify(action.sections || [])
    readonly property bool playingThis: studio.playing.action === name && name !== ""

    Connections {
        target: studio
        function onActionChanged() { page.draft = JSON.parse(JSON.stringify(studio.action.sections || [])) }
    }
    function edit(sectionIndex, mutate) {
        var copy = JSON.parse(JSON.stringify(draft))
        mutate(copy[sectionIndex])
        draft = copy
    }

    // ---- the header
    RowLayout {
        id: head
        x: 24; width: page.width - 48
        spacing: 12
        PillButton { icon: "←"; text: "Actions"; kind: "quiet"; onClicked: window.go("library") }
        Column {
            Layout.fillWidth: true
            Text { text: page.name; color: studio.colors.text; font.pixelSize: 24; font.weight: Font.Bold }
            Text {
                text: page.countSteps() + " steps in " + page.draft.length + (page.draft.length === 1 ? " section" : " sections")
                    + ((page.action.used_by || []).length ? " · used by " + page.action.used_by.join(", ") : "")
                color: studio.colors.muted; font.pixelSize: 13
            }
        }
        PillButton { icon: "●"; text: "Record again"; onClicked: window.recordAction(page.name) }
        PillButton {
            kind: page.playingThis ? "plain" : "primary"
            icon: page.playingThis ? "■" : "▶"; text: page.playingThis ? "Stop" : "Play"
            onClicked: page.playingThis ? studio.stopAction() : studio.playAction(page.name)
        }
    }

    // ---- the sections
    Flickable {
        id: scroller
        SmoothWheel { view: scroller }
        anchors { left: parent.left; right: parent.right; top: head.bottom; topMargin: 18; bottom: parent.bottom }
        contentHeight: sections.height + 120
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {}
        Column {
            id: sections
            x: 24; width: Math.min(parent.width - 48, 1000)
            spacing: 16
            Repeater {
                model: page.draft
                delegate: Glass {
                    id: card
                    required property var modelData
                    required property int index
                    readonly property int sectionIndex: index
                    width: sections.width
                    height: steps.height + 76
                    delay: index * 40
                    Row {
                        x: 20; y: 16; spacing: 10
                        Rectangle { width: 4; height: 22; radius: 2; color: studio.colors.accent2; anchors.verticalCenter: parent.verticalCenter }
                        TextField {
                            text: card.modelData.name || "Steps"
                            width: Math.max(160, implicitWidth); height: 32
                            color: studio.colors.text; font.pixelSize: 16; font.weight: Font.Bold
                            background: Rectangle { radius: 8; color: parent.activeFocus ? studio.colors.raised : "transparent" }
                            onEditingFinished: if (text !== (card.modelData.name || "Steps")) page.edit(card.sectionIndex, function (section) { section.name = text })
                        }
                    }
                    Column {
                        id: steps
                        x: 10; y: 58; width: card.width - 20
                        Repeater {
                            model: card.modelData.steps
                            delegate: StepRow {
                                required property var modelData
                                required property int index
                                width: steps.width
                                step: modelData
                                followed: page.playingThis
                                onChanged: function (copy) { page.edit(card.sectionIndex, function (section) { section.steps[index] = copy }) }
                                onRemoved: page.edit(card.sectionIndex, function (section) { section.steps.splice(index, 1) })
                                onMoved: function (by) {
                                    page.edit(card.sectionIndex, function (section) {
                                        var to = index + by
                                        if (to < 0 || to >= section.steps.length) return
                                        var one = section.steps.splice(index, 1)[0]
                                        section.steps.splice(to, 0, one)
                                    })
                                }
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
            Text { text: "Changes not saved"; color: studio.colors.warn; font.pixelSize: 14; font.weight: Font.DemiBold; rightPadding: 8 }
            PillButton { text: "Undo"; kind: "quiet"; small: true; onClicked: page.draft = JSON.parse(JSON.stringify(studio.action.sections || [])) }
            PillButton { text: "Save"; kind: "primary"; small: true; onClicked: studio.saveAction(page.name, page.draft) }
        }
    }
    Shortcut { sequence: "Ctrl+S"; enabled: page.visible && page.changed; onActivated: studio.saveAction(page.name, page.draft) }

    function countSteps() {
        var total = 0
        for (var index = 0; index < draft.length; index++) total += (draft[index].steps || []).length
        return total
    }
}
