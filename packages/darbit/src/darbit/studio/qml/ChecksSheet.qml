// Play's checks (#314, C): shown only when darbit doctor's checks before a start find a problem. Every check with
// what it found and how to fix it, Take them for targets not taken, and Cancel, Check again or Start anyway.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Sheet {
    id: sheet
    objectName: "checksSheet"
    readonly property var checks: studio.checks.bot === studio.bot.path ? (studio.checks.checks || []) : []
    readonly property int problems: studio.checks.bot === studio.bot.path ? (studio.checks.problems || 0) : 0
    property bool checking: false
    width: 560
    Connections {
        target: studio
        function onChecksChanged() { sheet.checking = false }
    }

    function title(name) {
        if (name === "darbit.toml") return name
        return name.charAt(0).toUpperCase() + name.slice(1)
    }
    // how to fix it, worded for the Studio where the command line's words name the command line
    function fixOf(check) {
        if (check.name === "targets" && (check.missing || []).length) return "take them with Capture"
        return check.fix || ""
    }
    function startAnyway() { close(); studio.start() }

    contentItem: Column {
        spacing: 16
        Text {
            width: parent.width; elide: Text.ElideRight
            text: (studio.bot.name || "The bot") + (sheet.problems ? " may not work right now" : " is ready")
            color: studio.colors.text; font.pixelSize: 22; font.weight: Font.Bold
        }
        Text {
            width: parent.width; wrapMode: Text.Wrap
            text: sheet.problems
                ? sheet.problems + " of " + sheet.checks.length + (sheet.checks.length === 1 ? " check" : " checks") + " found a problem. Fix "
                    + (sheet.problems === 1 ? "it" : "them") + ", or start anyway: the bot runs, but may fail where "
                    + (sheet.problems === 1 ? "it matters." : "they matter.")
                : "Every check is fine now."
            color: studio.colors.muted; font.pixelSize: 14
        }
        Column {
            width: parent.width; spacing: 12
            Repeater {
                model: sheet.checks
                delegate: RowLayout {
                    id: line
                    required property var modelData
                    readonly property color ink: modelData.ok === true ? studio.colors.ok : modelData.ok === false ? studio.colors.warn : studio.colors.faint
                    width: parent.width; spacing: 12
                    Rectangle {
                        Layout.alignment: Qt.AlignTop
                        Layout.preferredWidth: 24; Layout.preferredHeight: 24; radius: 12
                        color: Qt.rgba(ink.r, ink.g, ink.b, 0.2)
                        Text {
                                                    text: modelData.ok === true ? "✓" : modelData.ok === false ? "!" : "–"
                            color: line.ink; font.pixelSize: 13; font.weight: Font.Bold
                        }
                    }
                    Column {
                        Layout.fillWidth: true; spacing: 3
                        Text { text: sheet.title(modelData.name); color: studio.colors.text; font.pixelSize: 14; font.weight: Font.DemiBold }
                        Text { width: parent.width; wrapMode: Text.Wrap; text: modelData.found || ""; color: studio.colors.muted; font.pixelSize: 13 }
                        Text {
                            visible: text !== ""
                            width: parent.width; wrapMode: Text.Wrap
                            text: modelData.ok === false && sheet.fixOf(modelData) ? "Fix: " + sheet.fixOf(modelData) : ""
                            color: studio.colors.text; font.pixelSize: 13
                        }
                    }
                    PillButton {
                        objectName: "takeThem"
                        visible: modelData.ok === false && (modelData.missing || []).length > 0
                        Layout.alignment: Qt.AlignTop
                        small: true; text: "Take them"
                        onClicked: { sheet.close(); studio.openCapture("guide") }
                    }
                }
            }
        }
        Row {
            anchors.right: parent.right
            spacing: 10
            PillButton { text: "Cancel"; kind: "quiet"; onClicked: sheet.close() }
            PillButton {
                objectName: "checkAgain"
                icon: "↻"; text: sheet.checking ? "Checking…" : "Check again"
                enabled: !sheet.checking
                onClicked: { sheet.checking = true; studio.checkBot() }
            }
            PillButton {
                objectName: "startAnyway"
                kind: "primary"; icon: "▶"; text: sheet.problems ? "Start anyway" : "Start"
                onClicked: sheet.startAnyway()
            }
        }
    }
}
