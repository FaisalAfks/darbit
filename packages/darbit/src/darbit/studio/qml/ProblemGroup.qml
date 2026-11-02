// One kind of problem on the Results page (round 13, C with A's detail): its likely cause, what failed and how often,
// the plain sentence of what the bot saw, and, opened, the evidence (each image that ran out: how close it came against
// the line it needs, for how long) with the screen when it stopped and the fixes. From server/problems.py.
import QtQuick
import QtQuick.Layouts
import "format.js" as Format

Rectangle {
    id: group
    property var problem: ({})
    property bool open: false
    signal hide()
    readonly property color ink: problem.tone === "info" ? studio.colors.info : problem.tone === "warn" ? studio.colors.warn : studio.colors.danger
    implicitHeight: body.implicitHeight + 32
    radius: 16
    color: Qt.rgba(ink.r, ink.g, ink.b, 0.06)
    border.color: Qt.rgba(ink.r, ink.g, ink.b, 0.35)
    Behavior on implicitHeight { NumberAnimation { duration: studio.effects ? 220 : 0; easing.type: Easing.OutCubic } }
    clip: true

    Column {
        id: body
        x: 18; y: 16; width: parent.width - 36
        spacing: 10
        // the head: its cause, what failed, how often and when; a click opens the evidence
        RowLayout {
            width: parent.width; spacing: 12
            Rectangle {
                Layout.preferredWidth: causeText.implicitWidth + 22; Layout.preferredHeight: 26; radius: 13
                color: Qt.rgba(group.ink.r, group.ink.g, group.ink.b, 0.16)
                border.color: Qt.rgba(group.ink.r, group.ink.g, group.ink.b, 0.5)
                Text { id: causeText; anchors.centerIn: parent; text: group.problem.label || ""; color: group.ink; font.pixelSize: 12; font.weight: Font.DemiBold }
            }
            Text {
                Layout.fillWidth: true; elide: Text.ElideRight
                text: (group.problem.step || "") + ": " + (group.problem.reason || "")
                color: studio.colors.text; font.pixelSize: 15; font.weight: Font.DemiBold
            }
            Text {
                text: (group.problem.count > 1 ? group.problem.count + " times · " : "")
                    + (group.problem.times || []).map(function (time) { return Format.clock(time) }).join(", ")
                color: studio.colors.muted; font.pixelSize: 12
            }
            IconButton { glyph: group.open ? "▴" : "▾"; tip: group.open ? "Less" : "What it saw"; onClicked: group.open = !group.open }
        }
        Text {
            width: parent.width; wrapMode: Text.Wrap
            text: group.problem.sentence || ""
            color: studio.colors.text; font.pixelSize: 13; lineHeight: 1.2
        }

        // the evidence, opened: the images that ran out, and the screen when it stopped
        RowLayout {
            visible: group.open
            width: parent.width; spacing: 14
            Column {
                Layout.fillWidth: true; Layout.alignment: Qt.AlignTop
                spacing: 6
                Text { visible: (group.problem.searches || []).length === 0; text: "Nothing it looked for ran out before it stopped."; color: studio.colors.muted; font.pixelSize: 12 }
                Repeater {
                    model: group.problem.searches || []
                    delegate: Rectangle {
                        required property var modelData
                        width: parent.width; height: 48; radius: 10
                        color: studio.colors.raised
                        RowLayout {
                            anchors { fill: parent; leftMargin: 8; rightMargin: 12 }
                            spacing: 12
                            Rectangle {
                                Layout.preferredWidth: 60; Layout.preferredHeight: 34; radius: 6; color: studio.colors.bg; clip: true
                                Image { anchors.fill: parent; anchors.margins: 2; source: modelData.picture || ""; fillMode: Image.PreserveAspectFit; asynchronous: true }
                            }
                            Column {
                                Layout.fillWidth: true
                                Text { text: modelData.target; color: studio.colors.text; font.pixelSize: 13; font.family: "monospace"; font.weight: Font.DemiBold }
                                Text { text: "looked for " + Format.duration(modelData.seconds); color: studio.colors.muted; font.pixelSize: 11 }
                            }
                            // how close it came, against the line it needs
                            Item {
                                Layout.preferredWidth: 150; Layout.preferredHeight: 14
                                Rectangle { anchors.verticalCenter: parent.verticalCenter; width: parent.width; height: 6; radius: 3; color: studio.colors.raisedHover }
                                Rectangle {
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: parent.width * Math.max(0, Math.min(1, modelData.closest)); height: 6; radius: 3
                                    color: modelData.closest >= modelData.needs - 0.2 ? studio.colors.warn : studio.colors.danger
                                }
                                Rectangle { x: parent.width * modelData.needs - 1; width: 2; height: 14; color: studio.colors.text }
                            }
                            Text {
                                Layout.preferredWidth: 80; horizontalAlignment: Text.AlignRight
                                text: modelData.closest.toFixed(2) + " / " + modelData.needs.toFixed(2)
                                color: studio.colors.text; font.pixelSize: 12; font.family: "monospace"
                            }
                        }
                    }
                }
            }
            // the screen when it stopped: a click opens it full size
            Rectangle {
                visible: !!group.problem.screenshot
                Layout.preferredWidth: 260; Layout.preferredHeight: 146; Layout.alignment: Qt.AlignTop
                radius: 10; color: studio.colors.bg; border.color: studio.colors.line; clip: true
                Image { id: shot; anchors.fill: parent; anchors.margins: 1; source: group.problem.screenshot || ""; fillMode: Image.PreserveAspectFit; asynchronous: true; sourceSize.width: 520 }
                Text {
                    x: 8; y: 6; text: "when it stopped · " + Format.clock((group.problem.times || [""])[(group.problem.times || [""]).length - 1])
                    color: studio.colors.text; font.pixelSize: 10; font.family: "monospace"
                    style: Text.Outline; styleColor: studio.colors.bg
                }
                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: Qt.openUrlExternally(group.problem.screenshot) }
            }
        }
        // the fixes
        Row {
            visible: group.open
            spacing: 8
            PillButton {
                visible: (group.problem.screenshots || []).length > 1
                readonly property var shots: group.problem.screenshots || []
                small: true; icon: "▤"; text: "Screenshots (" + shots.length + ")"
                onClicked: Qt.openUrlExternally(shots[shots.length - 1].replace(/[^/]*$/, ""))
            }
            PillButton {
                visible: !!group.problem.target
                small: true; icon: "◎"; text: "Highlight " + group.problem.target
                onClicked: studio.highlightOne(group.problem.target)
            }
            PillButton {
                visible: !!group.problem.target
                small: true; icon: "▣"; text: "Retake " + group.problem.target
                kind: group.problem.cause === "changed" || group.problem.cause === "missing" ? "primary" : "plain"
                onClicked: studio.retake(group.problem.target, "image")
            }
            PillButton { small: true; kind: "quiet"; text: "Not a problem"; onClicked: group.hide() }
        }
    }
}
