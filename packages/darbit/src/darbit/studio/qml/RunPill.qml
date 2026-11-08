// The run pill (#245): while a bot runs, the Studio hides and this shows on a screen edge: the bot, where it is and
// for how long, Pause, Stop and ⤢ back to the Studio. A row on the top and bottom edges, a labelled column on the
// sides; floating, a card with where it is, the round so far and the last step. Docked, it slides out of sight a few
// seconds after the mouse leaves it; moving the mouse to its edge brings it back (PillWindow, hiding.py).
import QtQuick
import QtQuick.Layouts
import "format.js" as Format

PillWindow {
    id: runWindow
    hiding: runPill
    place: runPlace
    title: "darbit run pill"
    cardWidth: 440
    readonly property bool column: form === "column"
    readonly property string state: studio.bot.status || "stopped"
    readonly property color dot: state === "running" ? studio.colors.ok : state === "paused" ? studio.colors.warn : studio.colors.faint
    readonly property var info: studio.overview && studio.overview.data ? studio.overview.data : ({})
    readonly property var now: info.now || null
    readonly property var steps: now && now.path ? now.path.map(function (step) { return String(step).split(" > ").pop() }) : []
    readonly property string where: state === "paused" ? "Paused" : steps.join(" › ")
    readonly property string time: studio.bot.since ? Format.duration(studio.now - studio.bot.since) : ""
    // the round: its steps, how many are over, and the last one that ended
    readonly property var round: info.round && info.round.steps ? info.round.steps : []
    readonly property var ended: round.filter(function (step) { return step.state !== "planned" && step.state !== "running" })
    readonly property var lastStep: ended.length > 0 ? ended[ended.length - 1] : null

    Timer { interval: 1000; running: runPill.isOpen && !runPill.tucked; repeat: true; onTriggered: studio.tick() }

    // a row: the bot, where it is and for how long
    Row {
        visible: !runWindow.column
        Layout.leftMargin: 4; Layout.rightMargin: 12
        spacing: 9
        Rectangle { width: 11; height: 11; radius: 5.5; color: runWindow.dot; anchors.verticalCenter: parent.verticalCenter }
        Text {
            text: studio.bot.name || "darbit"
            color: studio.colors.text; font.pixelSize: 14; font.weight: Font.Bold
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            text: [runWindow.where, runWindow.time].filter(function (part) { return part !== "" }).join(" · ")
            width: Math.min(implicitWidth, 420); elide: Text.ElideLeft
            color: studio.colors.muted; font.pixelSize: 13
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    // a column: the same, a line each
    Column {
        visible: runWindow.column
        Layout.preferredWidth: 132; Layout.leftMargin: 4
        spacing: 3
        Row {
            spacing: 8
            Rectangle { width: 10; height: 10; radius: 5; color: runWindow.dot; anchors.verticalCenter: parent.verticalCenter }
            Text {
                text: studio.bot.name || "darbit"; width: 112; elide: Text.ElideRight
                color: studio.colors.text; font.pixelSize: 14; font.weight: Font.Bold
            }
        }
        Text {
            visible: text !== ""
            width: 132; wrapMode: Text.Wrap; maximumLineCount: 4; elide: Text.ElideRight
            text: runWindow.state === "paused" ? "Paused" : runWindow.steps.join("\n› ")
            color: studio.colors.muted; font.pixelSize: 13
        }
        Text { text: runWindow.time; color: studio.colors.faint; font.family: "monospace"; font.pixelSize: 12 }
    }
    Rectangle {
        Layout.preferredWidth: runWindow.column ? 132 : 1; Layout.preferredHeight: runWindow.column ? 1 : 24
        Layout.topMargin: runWindow.column ? 4 : 0; Layout.bottomMargin: runWindow.column ? 4 : 0
        color: studio.colors.line
    }
    PillAction {
        labelled: runWindow.column
        glyph: runWindow.state === "paused" ? "▶" : "❚❚"
        label: runWindow.state === "paused" ? "Go on" : "Pause"
        onClicked: studio.pause()
    }
    PillAction { labelled: runWindow.column; glyph: "■"; label: "Stop"; tip: "Stop the bot"; onClicked: studio.stop() }
    PillAction { labelled: runWindow.column; glyph: "⤢"; label: "Studio"; tip: "Open darbit Studio"; onClicked: runPill.close() }

    // floating: the bot and its state, then where it is, the round and the last step
    heading: [
        Rectangle { width: 11; height: 11; radius: 5.5; color: runWindow.dot },
        Text { text: studio.bot.name || "darbit"; color: studio.colors.text; font.pixelSize: 15; font.weight: Font.Bold },
        Chip { text: runWindow.state; tone: runWindow.state === "running" ? "ok" : runWindow.state === "paused" ? "warn" : "plain" },
        Item { Layout.fillWidth: true },
        Text { text: runWindow.time; color: studio.colors.muted; font.family: "monospace"; font.pixelSize: 12 }
    ]
    card: [
        Flow {
            width: parent.width; spacing: 6
            visible: runWindow.steps.length > 0
            Repeater {
                model: runWindow.steps
                delegate: Row {
                    required property var modelData
                    required property int index
                    spacing: 6
                    Text { visible: index > 0; text: "›"; color: studio.colors.faint; font.pixelSize: 13; anchors.verticalCenter: parent.verticalCenter }
                    Chip { text: modelData; tone: index === runWindow.steps.length - 1 ? "accent" : "plain" }
                }
            }
        },
        Text {
            visible: runWindow.steps.length === 0
            text: runWindow.state === "paused" ? "Paused" : "Between steps"
            color: studio.colors.muted; font.pixelSize: 13
        },
        Column {
            visible: runWindow.round.length > 0
            width: parent.width; spacing: 6
            RowLayout {
                width: parent.width
                Text { text: "Today's round"; color: studio.colors.text; font.pixelSize: 13; font.weight: Font.DemiBold; Layout.fillWidth: true }
                Text { text: runWindow.ended.length + " of " + runWindow.round.length + " done"; color: studio.colors.muted; font.pixelSize: 12 }
            }
            Bar { width: parent.width; gradientFill: true; share: runWindow.round.length ? runWindow.ended.length / runWindow.round.length : 0 }
        },
        Text {
            visible: runWindow.lastStep !== null
            width: parent.width; elide: Text.ElideRight
            textFormat: Text.StyledText
            text: runWindow.lastStep ? "Last: <b>" + runWindow.lastStep.name + "</b> " + Format.stateText(runWindow.lastStep.state)
                + (runWindow.lastStep.seconds ? " · " + Format.duration(runWindow.lastStep.seconds) : "") : ""
            color: studio.colors.muted; font.pixelSize: 13
        },
        RowLayout {
            width: parent.width; spacing: 8
            PillButton {
                small: true; icon: runWindow.state === "paused" ? "▶" : "❚❚"; text: runWindow.state === "paused" ? "Go on" : "Pause"
                onClicked: studio.pause()
            }
            PillButton { small: true; kind: "danger"; icon: "■"; text: "Stop"; onClicked: studio.stop() }
            Item { Layout.fillWidth: true }
            PillButton { small: true; icon: "⤢"; text: "Open Studio"; onClicked: runPill.close() }
        }
    ]
}
