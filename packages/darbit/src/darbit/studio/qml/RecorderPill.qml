// The recorder, floating at the top of the screen while keys, clicks and the mouse go into an action: its state and
// time, Checkpoint, Pause (and, while paused, a check to add), Done and Cancel; ≡ shows the steps as they're caught.
// Clicks on it aren't recorded. Like the run pill it slides out of sight a few seconds after the mouse leaves it and
// comes back at the top edge (PillWindow, hiding.py); it's away while Capture takes an image for a check.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "format.js" as Format

PillWindow {
    id: recorderWindow
    hiding: recorderHiding
    title: "darbit recorder"
    property bool stepsOpen: false
    property bool checksOpen: false
    edge: recorder.paused ? Qt.rgba(studio.colors.warn.r, studio.colors.warn.g, studio.colors.warn.b, 0.6)
                          : Qt.rgba(studio.colors.danger.r, studio.colors.danger.g, studio.colors.danger.b, 0.55)
    onPlaced: function (x, y, width, height) { recorder.setArea(x, y, width, height) }
    onVisibleChanged: if (!visible) checksOpen = false

    Row {
        Layout.leftMargin: 12; Layout.rightMargin: 12
        spacing: 9
        Rectangle {
            width: 11; height: 11; radius: 5.5
            color: recorder.paused ? studio.colors.warn : studio.colors.danger
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            text: recorder.paused ? "Paused" : "Recording"
            color: studio.colors.text; font.pixelSize: 14; font.weight: Font.Bold
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            text: recorder.name + " · " + Format.timer(recorder.seconds) + " · " + recorder.count + (recorder.count === 1 ? " step" : " steps")
                + (recorder.checks ? " · " + recorder.checks + (recorder.checks === 1 ? " check" : " checks") : "")
                + (recorder.parts > 1 ? " · part " + recorder.parts : "")
            color: studio.colors.muted; font.pixelSize: 13
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 24; color: studio.colors.line }
    IconButton { glyph: "≡"; tip: "The steps so far"; onClicked: recorderWindow.stepsOpen = !recorderWindow.stepsOpen }
    IconButton { glyph: "⚑"; tip: "Checkpoint (Ctrl+Alt+K): what came before becomes its own action"; onClicked: recorder.mark() }
    PillButton {
        visible: recorder.paused
        small: true; icon: "＋"; text: "Check"
        onClicked: recorderWindow.checksOpen = !recorderWindow.checksOpen
    }
    IconButton {
        glyph: recorder.paused ? "▶" : "❚❚"
        tip: (recorder.paused ? "Go on" : "Pause, to add a check") + " (Ctrl+Alt+P)"
        onClicked: { recorderWindow.checksOpen = false; recorder.pause() }
    }
    Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 24; color: studio.colors.line }
    IconButton { glyph: "✕"; tip: "Throw this recording away"; onClicked: recorder.finish(false) }
    PillButton { kind: "primary"; small: true; text: "Done"; onClicked: recorder.finish(true) }

    below: Column {
        width: parent.width
        spacing: 10
        // a check to add, while paused
        Rectangle {
            visible: recorderWindow.checksOpen && recorder.paused
            anchors.right: parent.right
            width: 280; height: choices.implicitHeight + 16; radius: 16
            color: Qt.rgba(studio.colors.glassStrong.r, studio.colors.glassStrong.g, studio.colors.glassStrong.b, 1)
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
            color: Qt.rgba(studio.colors.glassStrong.r, studio.colors.glassStrong.g, studio.colors.glassStrong.b, 1)
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
