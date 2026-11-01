// The recorder, floating at the top of the screen while keys, clicks and the mouse go into an action: its state and
// time, Checkpoint, Pause (and, while paused, a check to add), Done and Cancel; ≡ shows the steps as they're caught.
// Clicks on it aren't recorded. It hides while Capture takes a picture for a check.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Window
import "format.js" as Format

Window {
    id: pillWindow
    readonly property bool shown: recorder.active && !capture.isOpen
    property bool stepsOpen: false
    visible: shown
    transientParent: null  // its own window: it shows while the Studio is hidden (Windows hides a hidden window's tool windows too)
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
    color: "transparent"
    title: "darbit recorder"
    width: pill.width + 24
    height: pill.height + 24 + (stepsOpen ? steps.height + 10 : 0) + (checkMenu.visible ? checkMenu.height + 10 : 0)
    x: Screen.virtualX + (Screen.width - width) / 2
    y: Screen.virtualY + 14
    onXChanged: report()
    onYChanged: report()
    onWidthChanged: report()
    onHeightChanged: report()
    function report() { recorder.setArea(x, y, width, height) }

    Rectangle {
        id: pill
        x: 12; y: 12
        width: row.implicitWidth + 16; height: 56; radius: 28
        color: studio.colors.glassStrong
        border.color: recorder.paused ? Qt.rgba(studio.colors.warn.r, studio.colors.warn.g, studio.colors.warn.b, 0.6)
                                      : Qt.rgba(studio.colors.danger.r, studio.colors.danger.g, studio.colors.danger.b, 0.55)
        Behavior on width { NumberAnimation { duration: studio.effects ? 180 : 0; easing.type: Easing.OutCubic } }

        Row {
            id: row
            x: 8; anchors.verticalCenter: parent.verticalCenter
            spacing: 4
            Item {
                width: label.implicitWidth + 24; height: 40
                Row {
                    id: label
                    x: 12; anchors.verticalCenter: parent.verticalCenter
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
            }
            Rectangle { width: 1; height: 24; color: studio.colors.line; anchors.verticalCenter: parent.verticalCenter }
            IconButton { glyph: "≡"; tip: "The steps so far"; anchors.verticalCenter: parent.verticalCenter; onClicked: pillWindow.stepsOpen = !pillWindow.stepsOpen }
            IconButton { glyph: "⚑"; tip: "Checkpoint (Ctrl+Alt+K): what came before becomes its own action"; anchors.verticalCenter: parent.verticalCenter; onClicked: recorder.mark() }
            PillButton {
                visible: recorder.paused
                small: true; icon: "＋"; text: "Check"
                anchors.verticalCenter: parent.verticalCenter
                onClicked: checkMenu.visible = !checkMenu.visible
            }
            IconButton {
                glyph: recorder.paused ? "▶" : "❚❚"
                tip: (recorder.paused ? "Go on" : "Pause, to add a check") + " (Ctrl+Alt+P)"
                anchors.verticalCenter: parent.verticalCenter
                onClicked: { checkMenu.visible = false; recorder.pause() }
            }
            Rectangle { width: 1; height: 24; color: studio.colors.line; anchors.verticalCenter: parent.verticalCenter }
            IconButton { glyph: "✕"; tip: "Throw this recording away"; anchors.verticalCenter: parent.verticalCenter; onClicked: recorder.finish(false) }
            PillButton { kind: "primary"; small: true; text: "Done"; anchors.verticalCenter: parent.verticalCenter; onClicked: recorder.finish(true) }
        }
    }

    // a check to add, while paused
    Rectangle {
        id: checkMenu
        visible: false
        x: 12 + pill.width - width; y: pill.y + pill.height + 10
        width: 280; height: choices.implicitHeight + 16; radius: 16
        color: studio.colors.glassStrong; border.color: studio.colors.line
        Column {
            id: choices
            x: 8; y: 8; spacing: 2
            MenuLine { width: 264; icon: "▣"; text: "Wait for a picture…"; onClicked: { checkMenu.visible = false; recorder.takePicture(false) } }
            MenuLine { width: 264; icon: "◌"; text: "Until a picture is gone…"; onClicked: { checkMenu.visible = false; recorder.takePicture(true) } }
            MenuLine { width: 264; icon: "◷"; text: "Wait 1 second"; onClicked: { checkMenu.visible = false; recorder.addWait(1) } }
            MenuLine { width: 264; icon: "◷"; text: "Wait 3 seconds"; onClicked: { checkMenu.visible = false; recorder.addWait(3) } }
            MenuLine { width: 264; icon: "↶"; text: "Undo the last step"; onClicked: { checkMenu.visible = false; recorder.removeLast() } }
        }
    }

    // the steps so far, newest last
    Rectangle {
        id: steps
        visible: pillWindow.stepsOpen
        x: 12; y: pill.y + pill.height + 10 + (checkMenu.visible ? checkMenu.height + 10 : 0)
        width: pill.width; height: Math.min(320, list.implicitHeight + 20); radius: 16
        color: studio.colors.glassStrong; border.color: studio.colors.line
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
