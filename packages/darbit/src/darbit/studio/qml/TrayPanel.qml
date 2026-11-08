// The panel darbit's tray icon opens, in darbit's own menu (MenuPanel, MenuLine): every running bot with its state,
// Pause or Go on and Stop, alongside for one that sends no input (the shown bot's Play when none runs), the tools
// with their keys, Open darbit Studio, and Quit saying what it does with the running bots. app.py places it by the
// icon on the taskbar's edge and shows it; a click outside or Esc closes it.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Window
import "format.js" as Format

Window {
    id: panel
    readonly property var running: studio.running
    transientParent: null  // its own window: it shows while the Studio is hidden
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
    color: "transparent"
    width: 336
    height: menu.implicitHeight
    title: "darbit"

    function done() { panel.hide() }

    onVisibleChanged: visible ? menu.open() : menu.close()
    onActiveChanged: if (!active && visible) panel.hide()  // a click anywhere else
    Shortcut { sequence: "Esc"; onActivated: panel.hide() }
    Timer { interval: 1000; running: panel.visible && panel.running.length > 0; repeat: true; onTriggered: studio.tick() }

    component Heading: Text {
        leftPadding: 12; topPadding: 6; bottomPadding: 4
        color: studio.colors.muted; font.pixelSize: 11; font.weight: Font.Bold; font.letterSpacing: 1.2
    }
    component Divider: Item {
        width: parent.width; height: 13
        Rectangle { x: 10; width: parent.width - 20; height: 1; anchors.verticalCenter: parent.verticalCenter; color: studio.colors.line }
    }
    component BotLine: Item {
        id: line
        required property var bot
        property bool playing: true  // running or paused; false: the shown bot, stopped, with Play
        readonly property string state: bot.status || "stopped"
        width: parent.width; height: 50
        Avatar { id: square; x: 10; anchors.verticalCenter: parent.verticalCenter; size: 28; name: line.bot.name || ""; accent: line.bot.accent || "" }
        Column {
            anchors { left: square.right; leftMargin: 10; right: controls.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
            Text { width: parent.width; text: line.bot.name || ""; color: studio.colors.text; font.pixelSize: 14; font.weight: Font.DemiBold; elide: Text.ElideRight }
            Row {
                spacing: 6
                Rectangle {
                    width: 8; height: 8; radius: 4; anchors.verticalCenter: parent.verticalCenter
                    color: line.state === "running" ? studio.colors.ok : line.state === "paused" ? studio.colors.warn : studio.colors.faint
                }
                Text { text: line.state; color: studio.colors.muted; font.pixelSize: 12 }
                Text {
                    visible: line.state === "running" && !!line.bot.since
                    text: Format.duration(studio.now - line.bot.since)
                    color: studio.colors.muted; font.pixelSize: 12; font.family: "monospace"
                }
                Text {
                    // a bot that sends no input runs next to anything (decision 0020)
                    visible: line.playing && line.bot.input === false
                    text: "· alongside"; color: studio.colors.muted; font.pixelSize: 12
                }
            }
        }
        Row {
            id: controls
            anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
            spacing: 2
            IconButton {
                visible: line.playing; width: 32; height: 32
                glyph: line.state === "paused" ? "▶" : "❚❚"; tip: line.state === "paused" ? "Go on" : "Pause"
                onClicked: studio.pauseBot(line.bot.path)
            }
            IconButton {
                visible: line.playing; width: 32; height: 32
                glyph: "■"; tip: "Stop"; ink: studio.colors.danger
                onClicked: studio.stopBot(line.bot.path)
            }
            PillButton {
                visible: !line.playing
                small: true; kind: "primary"; text: "Play"; icon: "▶"
                onClicked: { studio.play(); panel.done() }
            }
        }
    }

    MenuPanel {
        id: menu
        objectName: "trayMenu"
        x: 0; y: 0; width: panel.width
        closePolicy: Popup.NoAutoClose  // the window closes it: a click outside or Esc
        contentItem: Column {
            width: menu.availableWidth
            Heading { text: "BOTS" }
            Repeater {
                model: panel.running
                delegate: BotLine { required property var modelData; bot: modelData }
            }
            BotLine { visible: panel.running.length === 0 && !!studio.bot.name; bot: studio.bot; playing: false }
            Text {
                visible: panel.running.length === 0 && !studio.bot.name
                leftPadding: 12; topPadding: 4; bottomPadding: 8
                text: "No bot yet: make one in darbit Studio"; color: studio.colors.muted; font.pixelSize: 13
            }
            Divider {}
            Heading { text: "TOOLS" }
            MenuLine {
                width: parent.width; icon: "◎"; text: "Capture"; keys: Format.sequence(studio.keys["capture.freeze"])
                onClicked: { panel.done(); studio.openCapture("any") }
            }
            MenuLine {
                width: parent.width; icon: "⌕"; text: "Scout"; keys: Format.sequence(studio.keys["scout.toggle"])
                onClicked: { panel.done(); studio.toggleScout() }
            }
            MenuLine {
                width: parent.width; icon: "●"; text: "Record an action…"
                onClicked: { panel.done(); trayPanel.record() }
            }
            Divider {}
            MenuLine {
                width: parent.width; icon: "⤢"; text: "Open darbit Studio"
                onClicked: { panel.done(); trayPanel.openStudio() }
            }
            MenuLine {
                objectName: "quitLine"
                width: parent.width; icon: "✕"; text: studio.quitLabel
                iconColor: studio.colors.danger; ink: studio.colors.danger
                onClicked: { panel.done(); trayPanel.quit() }
            }
        }
    }
}
