// Stop and start (#427): Play (a bot's, or an action's) refused because a bot or an action that sends input runs
// (one at a time, decision 0020). It names what's in the way, each with its state, and asks to stop it and start
// this bot (or play this action): Stop and start sends it again with replace, Cancel (or Esc, or a click outside)
// leaves it running.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "format.js" as Format

Sheet {
    id: sheet
    objectName: "stopAndStartSheet"
    property var asked: ({})  // held while it shows: it reads the same as it fades out
    readonly property var inTheWay: asked.running || []
    readonly property string bot: asked.name || "the bot"
    readonly property bool action: asked.method === "bot.action.play"
    // what was refused, as the question says it: "start my-bot" or "play go_to_boss"
    readonly property string doing: action ? "play " + ((asked.params || {}).name || "the action") : "start " + bot
    readonly property bool several: inTheWay.length > 1
    width: 560
    onAboutToShow: asked = studio.inTheWay
    onClosed: studio.keepRunning()

    // "a", "a and b", "a, b and c"
    function names() {
        var all = inTheWay.map(called)
        if (all.length < 2) return all.join("")
        return all.slice(0, -1).join(", ") + " and " + all[all.length - 1]
    }
    // a bot's name, or "my-bot's action go_to_boss" for an action playing
    function called(one) {
        var name = one.name || "A bot"
        return one.action ? name + "'s action " + one.action : name
    }
    // the bot as the Studio knows it: its square's colour and when it started
    function known(path) {
        var found = studio.bots.filter(function (one) { return one.path === path })
        return found.length ? found[0] : ({})
    }
    function stopAndStart() { studio.replaceAndStart(); close() }

    contentItem: Column {
        spacing: 16
        Text {
            width: parent.width; elide: Text.ElideRight
            text: sheet.doing.charAt(0).toUpperCase() + sheet.doing.slice(1) + "?"
            color: studio.colors.text; font.pixelSize: 22; font.weight: Font.Bold
        }
        Text {
            objectName: "question"
            width: parent.width; wrapMode: Text.Wrap
            text: sheet.names() + (sheet.several ? " are running and use" : " is running and uses") + " the mouse and keys. Stop "
                + (sheet.several ? "them" : "it") + " and " + sheet.doing + "?"
            color: studio.colors.muted; font.pixelSize: 14
        }
        Column {
            width: parent.width; spacing: 10
            Repeater {
                model: sheet.inTheWay
                delegate: RowLayout {
                    id: line
                    required property var modelData
                    readonly property var known: sheet.known(modelData.path)
                    readonly property string state: modelData.status || "running"
                    width: parent.width; spacing: 12
                    Avatar { size: 32; name: line.modelData.name || ""; accent: line.known.accent || ""; icon: line.known.icon || "" }
                    Column {
                        Layout.fillWidth: true; spacing: 2
                        Text {
                            width: parent.width; elide: Text.ElideRight
                            text: sheet.called(line.modelData)
                            color: studio.colors.text; font.pixelSize: 14; font.weight: Font.DemiBold
                        }
                        Row {
                            spacing: 6
                            Rectangle {
                                width: 8; height: 8; radius: 4; anchors.verticalCenter: parent.verticalCenter
                                color: line.state === "paused" ? studio.colors.warn : line.state === "playing" ? studio.colors.info : studio.colors.ok
                            }
                            Text { text: line.state; color: studio.colors.muted; font.pixelSize: 12 }
                            Text {
                                visible: line.state === "running" && !!line.known.since
                                text: Format.duration(studio.now - line.known.since)
                                color: studio.colors.muted; font.pixelSize: 12; font.family: "monospace"
                            }
                        }
                    }
                    Chip { text: "mouse and keys"; tone: "warn" }
                }
            }
        }
        Text {
            width: parent.width; wrapMode: Text.Wrap
            text: "Stopping lets go of every key, as Stop does."
            color: studio.colors.faint; font.pixelSize: 13
        }
        Row {
            anchors.right: parent.right
            spacing: 10
            PillButton { objectName: "keepRunning"; text: "Cancel"; kind: "quiet"; onClicked: sheet.close() }
            PillButton {
                objectName: "stopAndStart"
                kind: "primary"; icon: "■"; text: sheet.action ? "Stop and play" : "Stop and start"
                onClicked: sheet.stopAndStart()
            }
        }
    }
}
