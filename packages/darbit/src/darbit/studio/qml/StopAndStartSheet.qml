// Stop and start (#427): Play refused because a bot that sends input runs (one such bot at a time, decision 0020).
// It names the bots in the way, each with its state, and asks to stop them and start this one: Stop and start sends
// the start again with replace, Cancel (or Esc, or a click outside) leaves them running.
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
    readonly property bool several: inTheWay.length > 1
    width: 560
    onAboutToShow: asked = studio.inTheWay
    onClosed: studio.keepRunning()

    // "a", "a and b", "a, b and c"
    function names() {
        var all = inTheWay.map(function (one) { return one.name || "A bot" })
        if (all.length < 2) return all.join("")
        return all.slice(0, -1).join(", ") + " and " + all[all.length - 1]
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
            text: "Start " + sheet.bot + "?"
            color: studio.colors.text; font.pixelSize: 22; font.weight: Font.Bold
        }
        Text {
            objectName: "question"
            width: parent.width; wrapMode: Text.Wrap
            text: sheet.names() + (sheet.several ? " are running and use" : " is running and uses") + " the mouse and keys. Stop "
                + (sheet.several ? "them" : "it") + " and start " + sheet.bot + "?"
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
                    Avatar { size: 32; name: line.modelData.name || ""; accent: line.known.accent || "" }
                    Column {
                        Layout.fillWidth: true; spacing: 2
                        Text {
                            width: parent.width; elide: Text.ElideRight
                            text: line.modelData.name || ""
                            color: studio.colors.text; font.pixelSize: 14; font.weight: Font.DemiBold
                        }
                        Row {
                            spacing: 6
                            Rectangle {
                                width: 8; height: 8; radius: 4; anchors.verticalCenter: parent.verticalCenter
                                color: line.state === "paused" ? studio.colors.warn : studio.colors.ok
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
                kind: "primary"; icon: "■"; text: "Stop and start"
                onClicked: sheet.stopAndStart()
            }
        }
    }
}
