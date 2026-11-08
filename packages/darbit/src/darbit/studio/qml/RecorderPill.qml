// The recorder, floating on a screen edge while keys, clicks and the mouse go into an action: its state and time,
// Checkpoint, Pause (and, while paused, a check to add), Done and Cancel; ≡ shows the steps as they're caught. A row
// on the top and bottom edges, a labelled column on the sides, a card with the last steps floating. Clicks on it
// aren't recorded. Like the run pill it slides out of sight a few seconds after the mouse leaves it and comes back at
// its edge (PillWindow, hiding.py); it's away while Capture takes an image for a check.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "format.js" as Format

PillWindow {
    id: recorderWindow
    hiding: recorderHiding
    place: recorderPlace
    title: "darbit recorder"
    cardWidth: 420
    property bool stepsOpen: false
    property bool checksOpen: false
    readonly property bool column: form === "column"
    readonly property color dot: recorder.paused ? studio.colors.warn : studio.colors.danger
    readonly property string stateText: recorder.paused ? "Paused" : "Recording"
    readonly property string counts: recorder.count + (recorder.count === 1 ? " step" : " steps")
        + (recorder.checks ? " · " + recorder.checks + (recorder.checks === 1 ? " check" : " checks") : "")
        + (recorder.parts > 1 ? " · part " + recorder.parts : "")
    ink: recorder.paused ? Qt.rgba(studio.colors.warn.r, studio.colors.warn.g, studio.colors.warn.b, 0.6)
                         : Qt.rgba(studio.colors.danger.r, studio.colors.danger.g, studio.colors.danger.b, 0.55)
    onPlaced: function (x, y, width, height) { recorder.setArea(x, y, width, height) }
    onVisibleChanged: if (!visible) checksOpen = false

    Row {
        visible: !recorderWindow.column
        Layout.leftMargin: 4; Layout.rightMargin: 12
        spacing: 9
        Rectangle { width: 11; height: 11; radius: 5.5; color: recorderWindow.dot; anchors.verticalCenter: parent.verticalCenter }
        Text {
            text: recorderWindow.stateText
            color: studio.colors.text; font.pixelSize: 14; font.weight: Font.Bold
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            text: recorder.name + " · " + Format.timer(recorder.seconds) + " · " + recorderWindow.counts
            color: studio.colors.muted; font.pixelSize: 13
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    Column {
        visible: recorderWindow.column
        Layout.preferredWidth: 132; Layout.leftMargin: 4
        spacing: 3
        Row {
            spacing: 8
            Rectangle { width: 10; height: 10; radius: 5; color: recorderWindow.dot; anchors.verticalCenter: parent.verticalCenter }
            Text { text: recorderWindow.stateText; color: studio.colors.text; font.pixelSize: 14; font.weight: Font.Bold }
        }
        Text { text: recorder.name; width: 132; elide: Text.ElideRight; color: studio.colors.muted; font.pixelSize: 13 }
        Text { text: Format.timer(recorder.seconds); color: studio.colors.faint; font.family: "monospace"; font.pixelSize: 12 }
        Text { text: recorderWindow.counts; width: 132; wrapMode: Text.Wrap; color: studio.colors.faint; font.pixelSize: 12 }
    }
    Rectangle {
        Layout.preferredWidth: recorderWindow.column ? 132 : 1; Layout.preferredHeight: recorderWindow.column ? 1 : 24
        Layout.topMargin: recorderWindow.column ? 4 : 0; Layout.bottomMargin: recorderWindow.column ? 4 : 0
        color: studio.colors.line
    }
    PillAction { labelled: recorderWindow.column; glyph: "≡"; label: "Steps"; tip: "The steps so far"; onClicked: recorderWindow.stepsOpen = !recorderWindow.stepsOpen }
    PillAction { labelled: recorderWindow.column; glyph: "⚑"; label: "Checkpoint"; tip: "Checkpoint (Ctrl+Alt+K): what came before becomes its own action"; onClicked: recorder.mark() }
    PillAction {
        visible: recorder.paused
        labelled: recorderWindow.column
        glyph: "＋"; label: "Check"; tip: "Add a check"
        onClicked: recorderWindow.checksOpen = !recorderWindow.checksOpen
    }
    PillAction {
        labelled: recorderWindow.column
        glyph: recorder.paused ? "▶" : "❚❚"
        label: recorder.paused ? "Go on" : "Pause"
        tip: (recorder.paused ? "Go on" : "Pause, to add a check") + " (Ctrl+Alt+P)"
        onClicked: { recorderWindow.checksOpen = false; recorder.pause() }
    }
    Rectangle {
        Layout.preferredWidth: recorderWindow.column ? 132 : 1; Layout.preferredHeight: recorderWindow.column ? 1 : 24
        Layout.topMargin: recorderWindow.column ? 4 : 0; Layout.bottomMargin: recorderWindow.column ? 4 : 0
        color: studio.colors.line
    }
    PillAction { labelled: recorderWindow.column; glyph: "✕"; label: "Throw away"; tip: "Throw this recording away"; onClicked: recorder.finish(false) }
    PillButton { kind: "primary"; small: true; text: "Done"; Layout.fillWidth: recorderWindow.column; onClicked: recorder.finish(true) }

    // floating: its state and time, what it's recording, the last steps caught
    heading: [
        Rectangle { width: 11; height: 11; radius: 5.5; color: recorderWindow.dot },
        Text { text: recorderWindow.stateText; color: studio.colors.text; font.pixelSize: 15; font.weight: Font.Bold },
        Item { Layout.fillWidth: true },
        Text { text: Format.timer(recorder.seconds); color: studio.colors.muted; font.family: "monospace"; font.pixelSize: 12 }
    ]
    card: [
        RowLayout {
            width: parent.width
            Text { text: recorder.name; color: studio.colors.text; font.pixelSize: 13; font.weight: Font.DemiBold; elide: Text.ElideRight; Layout.fillWidth: true }
            Text { text: recorderWindow.counts; color: studio.colors.muted; font.pixelSize: 12 }
        },
        Column {
            width: parent.width; spacing: 2
            Text { visible: recorder.steps.length === 0; text: "Nothing yet: press keys and click in the game."; color: studio.colors.muted; font.pixelSize: 13 }
            Repeater {
                model: recorder.steps.slice(-3)
                delegate: Text {
                    required property var modelData
                    width: parent.width; elide: Text.ElideRight
                    text: modelData.text
                    color: modelData.kind === "check" ? studio.colors.text : studio.colors.muted
                    font.family: "monospace"; font.pixelSize: 12
                }
            }
        },
        Flow {
            width: parent.width; spacing: 8
            PillButton { small: true; icon: "≡"; text: "Steps"; onClicked: recorderWindow.stepsOpen = !recorderWindow.stepsOpen }
            PillButton { small: true; icon: "⚑"; text: "Checkpoint"; onClicked: recorder.mark() }
            PillButton { visible: recorder.paused; small: true; icon: "＋"; text: "Check"; onClicked: recorderWindow.checksOpen = !recorderWindow.checksOpen }
            PillButton {
                small: true; icon: recorder.paused ? "▶" : "❚❚"; text: recorder.paused ? "Go on" : "Pause"
                onClicked: { recorderWindow.checksOpen = false; recorder.pause() }
            }
            PillButton { small: true; kind: "danger"; icon: "✕"; text: "Throw away"; onClicked: recorder.finish(false) }
            PillButton { small: true; kind: "primary"; text: "Done"; onClicked: recorder.finish(true) }
        }
    ]

    below: Column {
        width: parent.width
        spacing: 10
        // a check to add, while paused
        Rectangle {
            visible: recorderWindow.checksOpen && recorder.paused
            x: recorderWindow.side === "right" ? 0 : parent.width - width
            width: 280; height: choices.implicitHeight + 16; radius: 16
            color: studio.colors.solid
            border.color: studio.colors.line
            Column {
                id: choices
                x: 8; y: 8; spacing: 2
                MenuLine { width: 264; icon: "▣"; text: "Wait for an image…"; onClicked: { recorderWindow.checksOpen = false; recorder.takePicture(false) } }
                MenuLine { width: 264; icon: "◌"; text: "Until an image is gone…"; onClicked: { recorderWindow.checksOpen = false; recorder.takePicture(true) } }
                MenuLine { width: 264; icon: "◷"; text: "Wait 1 second"; onClicked: { recorderWindow.checksOpen = false; recorder.addWait(1) } }
                MenuLine { width: 264; icon: "◷"; text: "Wait 3 seconds"; onClicked: { recorderWindow.checksOpen = false; recorder.addWait(3) } }
                MenuLine { width: 264; icon: "↶"; text: "Undo the last step"; onClicked: { recorderWindow.checksOpen = false; recorder.removeLast() } }
            }
        }
        // the steps so far, newest last
        Rectangle {
            visible: recorderWindow.stepsOpen
            width: parent.width; height: Math.min(320, list.implicitHeight + 20); radius: 16
            color: studio.colors.solid
            border.color: studio.colors.line
            clip: true
            Column {
                id: list
                x: 14; y: 10; width: parent.width - 28; spacing: 2
                Text { visible: recorder.steps.length === 0; text: "Nothing yet: press keys and click in the game."; color: studio.colors.muted; font.pixelSize: 13 }
                Repeater {
                    model: recorder.steps
                    delegate: Row {
                        required property var modelData
                        spacing: 10
                        Text {
                            width: 18; text: modelData.kind === "check" ? "▣" : modelData.kind === "wait" ? "◷" : modelData.kind === "key" ? "⌨" : "●"
                            color: modelData.kind === "check" ? studio.colors.accent2 : studio.colors.faint; font.pixelSize: 12
                        }
                        Text {
                            width: list.width - 28; elide: Text.ElideRight
                            text: modelData.text
                            color: modelData.kind === "check" ? studio.colors.text : studio.colors.muted
                            font.family: "monospace"; font.pixelSize: 12
                        }
                    }
                }
            }
        }
    }
}
